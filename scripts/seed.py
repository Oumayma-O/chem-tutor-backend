"""
Seed script — Master Lesson Library v2.

Architecture:
  seed_data/lessons.py  — MASTER_LESSONS (single source of truth)
  seed_data/units.py    — STANDARD_UNITS, AP_UNITS, UNIT_BRIDGE_MAP
  seed_data/phases.py   — STANDARD_PHASES, AP_PHASES
  seed_data/lookup.py   — GRADES, INTERESTS, KEEP_COURSE_NAMES
  seed_data/lesson_standards.py — LESSON_STANDARDS (junction seed)
  seed_data/problem_few_shots.py — FEW_SHOT_DATA

Usage:
  python -m scripts.seed           # idempotent upsert
  python -m scripts.seed --clean   # wipe everything and reseed from scratch
"""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.infrastructure.database.models import (
    Course,
    FewShotExample,
    Grade,
    Interest,
    Lesson,
    LessonStandard,
    Phase,
    Standard,
    Unit,
    UnitLesson,
)
from scripts.seed_data.problem_few_shots import FEW_SHOT_DATA
from scripts.seed_data.lessons import MASTER_LESSONS
from scripts.seed_data.reference_cards import REFERENCE_CARDS
from scripts.seed_data.lookup import GRADES, INTERESTS, KEEP_COURSE_NAMES
from scripts.seed_data.phases import AP_PHASES, STANDARD_PHASES
from scripts.seed_data.lesson_standards import LESSON_STANDARDS
from scripts.seed_data.standards import STANDARDS_SEED
from scripts.seed_data.units import AP_UNITS, STANDARD_UNITS

settings = get_settings()

KEEP_UNIT_IDS: set[str] = {u["id"] for u in STANDARD_UNITS} | {u["id"] for u in AP_UNITS}


# ══════════════════════════════════════════════════════════════
# SEED FUNCTIONS
# ══════════════════════════════════════════════════════════════

async def seed(session: AsyncSession) -> None:
    print("\n─── Lookup tables ───")

    for name, sort in GRADES:
        if not await session.scalar(select(Grade).where(Grade.name == name)):
            session.add(Grade(name=name, sort_order=sort))
            print(f"  + Grade: {name}")
    await session.flush()

    for name, sort in [("Standard Chemistry", 1), ("AP Chemistry", 2)]:
        if not await session.scalar(select(Course).where(Course.name == name)):
            session.add(Course(name=name, sort_order=sort))
            print(f"  + Course: {name}")
    await session.flush()

    for slug, label, icon in INTERESTS:
        if not await session.scalar(select(Interest).where(Interest.slug == slug)):
            session.add(Interest(slug=slug, label=label, icon=icon))
            print(f"  + Interest: {label}")
    await session.flush()

    # Remove stale courses
    for c in (await session.scalars(select(Course))).all():
        if c.name not in KEEP_COURSE_NAMES:
            print(f"  ✗ Removing stale course: {c.name}")
            await session.delete(c)
    await session.flush()

    std_course = await session.scalar(select(Course).where(Course.name == "Standard Chemistry"))
    ap_course  = await session.scalar(select(Course).where(Course.name == "AP Chemistry"))

    # Remove stale units
    for unit in (await session.scalars(select(Unit))).all():
        if unit.id not in KEEP_UNIT_IDS:
            print(f"  ✗ Removing stale unit: {unit.id}")
            await session.execute(text(f"DELETE FROM units WHERE id = '{unit.id}'"))
    await session.flush()

    print("\n─── Upserting units ───")
    await _upsert_units_bare(session, STANDARD_UNITS, std_course.id)
    await _upsert_units_bare(session, AP_UNITS, ap_course.id)

    print("\n─── Master lesson library ───")
    result = await session.execute(text("DELETE FROM lessons WHERE slug LIKE 'L-legacy-%'"))
    if result.rowcount:
        print(f"  ✗ Deleted {result.rowcount} legacy lessons")
    await session.flush()

    slug_to_lesson_id: dict[str, int] = {}
    for slug, data in MASTER_LESSONS.items():
        lesson = await session.scalar(select(Lesson).where(Lesson.slug == slug))
        ext_of  = data.get("extension_of")
        has_sim = data.get("has_simulation", False)
        if lesson is None:
            lesson = Lesson(
                slug=slug,
                title=data["title"],
                description="",
                is_ap_only=data["is_ap_only"],
                key_equations=data["key_equations"],
                objectives=data["objectives"],
                key_rules=data.get("key_rules", []),
                misconceptions=data.get("misconceptions", []),
                blueprint=data.get("blueprint", "solver"),
                required_tools=data.get("required_tools", []),
                unit_id=data["canonical_unit"],
                lesson_index=data["canonical_index"],
                extension_of=ext_of,
                has_simulation=has_sim,
                is_active=True,
            )
            session.add(lesson)
            await session.flush()
            print(f"  + {slug}")
        else:
            lesson.title          = data["title"]
            lesson.is_ap_only     = data["is_ap_only"]
            lesson.key_equations  = data["key_equations"]
            lesson.objectives     = data["objectives"]
            lesson.key_rules      = data.get("key_rules", [])
            lesson.misconceptions = data.get("misconceptions", [])
            lesson.blueprint      = data.get("blueprint", "solver")
            lesson.required_tools = data.get("required_tools", [])
            lesson.extension_of   = ext_of
            lesson.has_simulation = has_sim
        slug_to_lesson_id[slug] = lesson.id
    await session.flush()

    print("\n─── Standard Chemistry unit_lessons ───")
    await _seed_unit_lessons(session, STANDARD_UNITS, slug_to_lesson_id)

    print("\n─── AP Chemistry unit_lessons ───")
    await _seed_unit_lessons(session, AP_UNITS, slug_to_lesson_id)

    print("\n─── Standard Chemistry Phases ───")
    await _seed_phases(session, std_course.id, STANDARD_PHASES)

    print("\n─── AP Chemistry Phases ───")
    await _seed_phases(session, ap_course.id, AP_PHASES)

    print("\n✅  Seed complete!")


async def _upsert_units_bare(
    session: AsyncSession,
    unit_defs: list[dict],
    course_id: int,
) -> None:
    """Create or update units without touching unit_lessons."""
    for u in unit_defs:
        unit = await session.get(Unit, u["id"])
        if unit is None:
            unit = Unit(
                id=u["id"],
                title=u["title"],
                description=u.get("description", ""),
                icon=u.get("icon"),
                sort_order=u["sort_order"],
                course_id=course_id,
                is_active=True,
                is_coming_soon=False,
            )
            session.add(unit)
            await session.flush()
            print(f"  + {u['id']}: {u['title']}")
        else:
            unit.title       = u["title"]
            unit.description = u.get("description", unit.description)
            unit.icon        = u.get("icon", unit.icon)
            unit.sort_order  = u["sort_order"]
            unit.course_id   = course_id
    await session.flush()


async def _seed_unit_lessons(
    session: AsyncSession,
    unit_defs: list[dict],
    slug_to_lesson_id: dict[str, int],
) -> None:
    """Clear and re-seed unit_lessons junction rows."""
    for u in unit_defs:
        await session.execute(delete(UnitLesson).where(UnitLesson.unit_id == u["id"]))
        lesson_ids = u.get("lesson_ids", [])
        for order, slug in enumerate(lesson_ids):
            lid = slug_to_lesson_id.get(slug)
            if lid is None:
                print(f"  ⚠  Unknown slug in {u['id']}: {slug}")
                continue
            session.add(UnitLesson(unit_id=u["id"], lesson_id=lid, lesson_order=order))
        await session.flush()
        print(f"  {u['id']}: {len(lesson_ids)} lessons")


async def _seed_phases(
    session: AsyncSession,
    course_id: int,
    phase_defs: list[dict],
) -> None:
    """Upsert phases for a course and assign units."""
    for p in phase_defs:
        phase = await session.scalar(
            select(Phase).where(Phase.course_id == course_id, Phase.sort_order == p["sort_order"])
        )
        if phase is None:
            phase = Phase(
                name=p["name"],
                description=p["description"],
                course_id=course_id,
                sort_order=p["sort_order"],
                color=p["color"],
            )
            session.add(phase)
            await session.flush()
            print(f"  + {p['name']} (id={phase.id})")
        else:
            phase.name        = p["name"]
            phase.description = p["description"]
            phase.color       = p["color"]
            await session.flush()
            print(f"  ✓ {p['name']} (id={phase.id})")

        for unit_id, order in p["units"]:
            unit = await session.get(Unit, unit_id)
            if unit:
                unit.phase_id            = phase.id
                unit.order_within_phase  = order
            else:
                print(f"    [skip] unit '{unit_id}' not in DB")
    await session.flush()


# ── Standards ─────────────────────────────────────────────────────────────────

async def _seed_standards(async_session) -> None:
    print("\n─── Standards ───")

    # Ensure title and category columns exist (idempotent — safe to run on existing DBs)
    async with async_session() as session:
        await session.execute(text(
            "ALTER TABLE standards "
            "ADD COLUMN IF NOT EXISTS title VARCHAR(300) NOT NULL DEFAULT ''"
        ))
        await session.execute(text(
            "ALTER TABLE standards "
            "ADD COLUMN IF NOT EXISTS category VARCHAR(200)"
        ))
        await session.execute(text(
            "ALTER TABLE standards "
            "ADD COLUMN IF NOT EXISTS is_core BOOLEAN NOT NULL DEFAULT true"
        ))
        await session.commit()

    inserted = updated = 0
    async with async_session() as session:
        for entry in STANDARDS_SEED:
            src = entry["source"]
            existing = await session.scalar(
                select(Standard).where(Standard.code == entry["code"])
            )
            is_core = entry.get("is_core", True)
            if existing is None:
                session.add(Standard(
                    code=entry["code"],
                    framework=src,
                    title=entry["title"],
                    description=entry.get("description"),
                    category=entry.get("category"),
                    is_core=is_core,
                ))
                inserted += 1
            else:
                existing.framework = src
                existing.title = entry["title"]
                existing.description = entry.get("description")
                existing.category = entry.get("category")
                existing.is_core = is_core
                updated += 1
        await session.commit()

    print(f"  {inserted} inserted, {updated} updated")


async def _seed_lesson_standards(async_session) -> None:
    print("\n─── Lesson ↔ Standard links ───")
    inserted = skipped = 0
    async with async_session() as session:
        for lesson_slug, standard_code in LESSON_STANDARDS:
            lesson = await session.scalar(
                select(Lesson).where(Lesson.slug == lesson_slug)
            )
            standard = await session.scalar(
                select(Standard).where(Standard.code == standard_code)
            )
            if lesson is None or standard is None:
                skipped += 1
                if lesson is None:
                    print(f"  SKIP (lesson not found): {lesson_slug}")
                else:
                    print(f"  SKIP (standard not found): {standard_code}")
                continue
            exists = await session.scalar(
                select(LessonStandard).where(
                    LessonStandard.lesson_id == lesson.id,
                    LessonStandard.standard_id == standard.id,
                )
            )
            if not exists:
                session.add(LessonStandard(lesson_id=lesson.id, standard_id=standard.id))
                inserted += 1
        await session.commit()
    print(f"  {inserted} inserted, {skipped} skipped")


# ── Few-shot examples ─────────────────────────────────────────────────────────

def _fs_normalize_steps(steps: list[dict]) -> list[dict]:
    """Normalize curated few-shot steps into API-facing structure, preserving all widget fields."""
    normalized: list[dict] = []
    for i, s in enumerate(steps):
        step = {
            "stepNumber": i + 1,
            "label": s["label"],
            "type": s["type"],
            "instruction": s["instruction"],
        }
        if (ca := s.get("correctAnswer")) is not None:
            step["correctAnswer"] = ca
        if skill_used := s.get("skillUsed"):
            step["skillUsed"] = skill_used
        if explanation := s.get("explanation"):
            step["explanation"] = explanation
        # Preserve widget-specific fields
        if eq := s.get("equationParts"):
            step["equationParts"] = eq
        if fields := (s.get("input_fields") or s.get("inputFields") or s.get("labeledValues")):
            step["input_fields"] = fields
        if cp := s.get("comparisonParts"):
            step["comparisonParts"] = cp
        normalized.append(step)
    return normalized


async def _seed_few_shots(async_session) -> None:
    print("\n─── Few-shot examples ───")

    # ── Ensure variant_index column and correct unique index exist ────────────
    # Done here (not via Alembic) so no migration files are needed.
    async with async_session() as session:
        await session.execute(text(
            "ALTER TABLE few_shot_examples "
            "ADD COLUMN IF NOT EXISTS variant_index INTEGER NOT NULL DEFAULT 1"
        ))
        await session.execute(text("DROP INDEX IF EXISTS ix_few_shot_lookup"))
        await session.execute(text(
            "CREATE UNIQUE INDEX ix_few_shot_lookup "
            "ON few_shot_examples "
            "(unit_id, lesson_index, difficulty, level, strategy, variant_index)"
        ))
        await session.commit()

    # ── Insert all examples, assigning variant_index per slot ─────────────────
    # variant_index increments for each additional problem with the same
    # (unit_id, lesson_index, difficulty, strategy) key so all variants are kept.
    variant_counter: dict[tuple, int] = {}
    inserted = 0

    async with async_session() as session:
        for unit_id, lesson_index, difficulty, blueprint, ex in FEW_SHOT_DATA:
            slot_key = (unit_id, lesson_index, difficulty, blueprint)
            variant_counter[slot_key] = variant_counter.get(slot_key, 0) + 1
            variant_index = variant_counter[slot_key]

            normalized_json = {
                "title": ex["title"],
                "statement": ex["statement"],
                "steps": _fs_normalize_steps(ex["steps"]),
            }

            await session.execute(text("""
                INSERT INTO few_shot_examples
                    (unit_id, lesson_index, difficulty, level, strategy,
                     variant_index, example_json, is_active, promoted, created_at)
                VALUES
                    (:unit_id, :lesson_index, :difficulty, 1, :strategy,
                     :variant_index, cast(:example_json as jsonb), true, false, now())
                ON CONFLICT (unit_id, lesson_index, difficulty, level, strategy, variant_index)
                DO UPDATE SET
                    example_json = EXCLUDED.example_json,
                    is_active    = EXCLUDED.is_active
            """).bindparams(
                unit_id=unit_id,
                lesson_index=lesson_index,
                difficulty=difficulty,
                strategy=blueprint,
                variant_index=variant_index,
                example_json=__import__("json").dumps(normalized_json),
            ))
            inserted += 1

        await session.commit()

    print(f"  {inserted} upserted")


async def _seed_reference_cards(async_session) -> None:
    print("\n─── Reference cards ───")
    seeded = 0
    async with async_session() as session:
        for card in REFERENCE_CARDS:
            lesson = await session.scalar(
                select(Lesson)
                .join(UnitLesson, UnitLesson.lesson_id == Lesson.id)
                .where(UnitLesson.unit_id == card["unit_id"])
                .where(UnitLesson.lesson_order == card["lesson_index"])
            )
            if lesson is None:
                print(f"  ⚠  No lesson for {card['unit_id']} index {card['lesson_index']} — skipped")
                continue
            if lesson.reference_card_json is None:
                lesson.reference_card_json = card
                seeded += 1
                print(f"  + {card['unit_id']}[{card['lesson_index']}]: {card['lesson']}")
        await session.commit()
    print(f"  {seeded} seeded (existing cards untouched)")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

_TRUNCATE_TABLES = [
    "classroom_curriculum_overrides",
    "exit_ticket_responses", "exit_tickets",
    "misconception_logs", "thinking_tracker_logs",
    "skill_mastery", "problem_attempts",
    "user_lesson_playlists", "lesson_progress",
    "problem_cache", "generation_logs",
    "unit_lessons", "lesson_standards", "lessons", "units",
    "phases", "standards", "curriculum_documents",
    "student_interests", "user_profiles",
    "classroom_students", "classrooms",
    "interests", "courses", "grades",
    "prompt_versions", "few_shot_examples", "users",
]


async def _clean_all(conn) -> None:
    """TRUNCATE all app tables with CASCADE. Dev only."""
    print("\n─── Cleaning all data ───")
    existing = []
    for t in _TRUNCATE_TABLES:
        r = await conn.execute(
            text("SELECT 1 FROM information_schema.tables WHERE table_name = :t"), {"t": t}
        )
        if r.fetchone():
            existing.append(t)
    if existing:
        await conn.execute(text(f"TRUNCATE TABLE {', '.join(existing)} CASCADE"))
        print(f"  Truncated {len(existing)} tables")
    else:
        print("  No tables to clean")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the database")
    parser.add_argument("--clean", action="store_true", help="Wipe all data first, then reseed")
    args = parser.parse_args()

    eng = create_async_engine(settings.database_url, echo=False)

    if args.clean:
        async with eng.begin() as conn:
            await _clean_all(conn)

    async_session = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with session.begin():
            await seed(session)

    await _seed_standards(async_session)
    await _seed_lesson_standards(async_session)
    await _seed_few_shots(async_session)
    await _seed_reference_cards(async_session)
    await eng.dispose()


if __name__ == "__main__":
    asyncio.run(main())
