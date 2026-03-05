"""
Repositories for Phase-based curriculum and classroom curriculum overrides.

PhaseRepository              — CRUD for phases
ClassroomCurriculumRepository — fetch curriculum (global or classroom-specific)
                                and manage per-classroom overrides
"""

import uuid
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    ClassroomCurriculumOverride,
    Phase,
    Unit,
    UnitLesson,
)


# ── PhaseRepository ───────────────────────────────────────────

class PhaseRepository:

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self, course_id: int | None = None) -> list[Phase]:
        q = select(Phase).order_by(Phase.sort_order)
        if course_id is not None:
            q = q.where(Phase.course_id == course_id)
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def get_by_id(self, phase_id: int) -> Phase | None:
        return await self._db.get(Phase, phase_id)

    async def create(self, phase: Phase) -> Phase:
        self._db.add(phase)
        await self._db.flush()
        return phase

    async def update(self, phase: Phase, **fields) -> Phase:
        for k, v in fields.items():
            if v is not None:
                setattr(phase, k, v)
        await self._db.flush()
        return phase

    async def delete(self, phase: Phase) -> None:
        await self._db.delete(phase)
        await self._db.flush()


# ── ClassroomCurriculumRepository ────────────────────────────

class ClassroomCurriculumRepository:
    """
    Fetches curriculum units in display order, merging classroom overrides.

    Global (no classroom):
        ORDER BY unit.phase_id, COALESCE(unit.order_within_phase, unit.sort_order)

    Classroom-specific:
        Same base query + LEFT JOIN overrides.
        - is_hidden = TRUE  → excluded
        - phase_id override → unit moves to a different phase group
        - custom_order      → replaces order_within_phase within that phase
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Internal helpers ──────────────────────────────────────

    async def _load_units_with_lessons(self, course_id: int | None) -> list[Unit]:
        """Load all active units for a course, with their lesson counts."""
        from app.infrastructure.database.models import Course

        q = (
            select(Unit)
            .options(
                selectinload(Unit.unit_lessons).selectinload(UnitLesson.lesson),
                selectinload(Unit.phase),
                selectinload(Unit.course),
            )
            .where(Unit.is_active == True)
            .order_by(Unit.phase_id.nullslast(), Unit.sort_order)
        )
        if course_id is not None:
            q = q.where(Unit.course_id == course_id)
        result = await self._db.execute(q)
        return list(result.scalars().unique().all())

    async def _load_overrides(
        self, classroom_id: uuid.UUID
    ) -> dict[str, ClassroomCurriculumOverride]:
        """Return {unit_id: override} for the classroom."""
        q = select(ClassroomCurriculumOverride).where(
            ClassroomCurriculumOverride.classroom_id == classroom_id
        )
        result = await self._db.execute(q)
        return {row.unit_id: row for row in result.scalars().all()}

    async def _load_all_phases(self) -> dict[int, Phase]:
        result = await self._db.execute(select(Phase).order_by(Phase.sort_order))
        return {p.id: p for p in result.scalars().all()}

    # ── Public API ────────────────────────────────────────────

    async def fetch_curriculum(
        self,
        course_id: int | None,
        classroom_id: uuid.UUID | None,
    ) -> dict:
        """
        Returns a structured dict ready to be serialised as CurriculumResponse.

        Grouping logic
        ──────────────
        Each unit belongs to the *effective* phase:
            effective_phase_id = override.phase_id ?? unit.phase_id

        Within a phase, units are sorted by:
            effective_order = override.custom_order ?? unit.order_within_phase ?? unit.sort_order

        Units without any phase go into a synthetic "Unassigned" group at the end.
        """
        units = await self._load_units_with_lessons(course_id)
        overrides = (
            await self._load_overrides(classroom_id) if classroom_id else {}
        )
        phases_map = await self._load_all_phases()

        is_customised = bool(overrides)

        # ── Build per-phase buckets ───────────────────────────
        # phase_id (or None for unassigned) → list of (effective_order, unit_dict)
        buckets: dict[int | None, list[tuple[int, dict]]] = {}

        for unit in units:
            override = overrides.get(unit.id)

            if override and override.is_hidden:
                continue  # hidden by teacher

            effective_phase_id = (
                override.phase_id if (override and override.phase_id is not None)
                else unit.phase_id
            )
            effective_order = (
                override.custom_order if (override and override.custom_order is not None)
                else (unit.order_within_phase if unit.order_within_phase is not None else unit.sort_order)
            )

            lesson_titles = [
                ul.lesson.title
                for ul in sorted(unit.unit_lessons, key=lambda x: x.lesson_order)
                if ul.lesson
            ]

            unit_dict = {
                "id": unit.id,
                "title": unit.title,
                "description": unit.description,
                "icon": unit.icon,
                "gradient": unit.gradient,
                "grade_id": unit.grade_id,
                "course_id": unit.course_id,
                "course_name": unit.course.name if unit.course else None,
                "sort_order": unit.sort_order,
                "is_active": unit.is_active,
                "is_coming_soon": unit.is_coming_soon,
                "lesson_count": len(unit.unit_lessons),
                "skill_count": sum(
                    len(ul.lesson.objectives or [])
                    for ul in unit.unit_lessons
                    if ul.lesson
                ),
                "lesson_titles": lesson_titles,
                "effective_phase_id": effective_phase_id,
                "effective_order": effective_order,
                "is_hidden": False,
                "has_override": override is not None,
            }

            buckets.setdefault(effective_phase_id, []).append(
                (effective_order, unit_dict)
            )

        # ── Sort units within each bucket ─────────────────────
        for pid in buckets:
            buckets[pid].sort(key=lambda t: t[0])

        # ── Build phase groups in phase sort_order ────────────
        phase_groups = []

        # Assigned phases (in sort_order)
        seen_phases = sorted(
            (pid for pid in buckets if pid is not None),
            key=lambda pid: phases_map[pid].sort_order if pid in phases_map else 9999,
        )
        for pid in seen_phases:
            phase = phases_map.get(pid)
            phase_groups.append({
                "phase_id": pid,
                "phase_name": phase.name if phase else f"Phase {pid}",
                "phase_description": phase.description if phase else None,
                "phase_color": phase.color if phase else None,
                "phase_course_id": phase.course_id if phase else None,
                "sort_order": phase.sort_order if phase else 9999,
                "units": [u for _, u in buckets[pid]],
            })

        # Unassigned units go last
        if None in buckets:
            phase_groups.append({
                "phase_id": None,
                "phase_name": "Unassigned",
                "phase_description": None,
                "phase_color": None,
                "phase_course_id": None,
                "sort_order": 9999,
                "units": [u for _, u in buckets[None]],
            })

        return {
            "classroom_id": classroom_id,
            "is_customised": is_customised,
            "phases": phase_groups,
        }

    # ── Overrides ─────────────────────────────────────────────

    async def upsert_override(
        self,
        classroom_id: uuid.UUID,
        unit_id: str,
        phase_id: int | None,
        custom_order: int | None,
        is_hidden: bool,
    ) -> ClassroomCurriculumOverride:
        q = select(ClassroomCurriculumOverride).where(
            ClassroomCurriculumOverride.classroom_id == classroom_id,
            ClassroomCurriculumOverride.unit_id == unit_id,
        )
        result = await self._db.execute(q)
        override = result.scalar_one_or_none()

        if override is None:
            override = ClassroomCurriculumOverride(
                classroom_id=classroom_id,
                unit_id=unit_id,
            )
            self._db.add(override)

        override.phase_id = phase_id
        override.custom_order = custom_order
        override.is_hidden = is_hidden
        override.synced_at = datetime.utcnow()
        await self._db.flush()
        return override

    async def get_overrides(
        self, classroom_id: uuid.UUID
    ) -> list[ClassroomCurriculumOverride]:
        q = select(ClassroomCurriculumOverride).where(
            ClassroomCurriculumOverride.classroom_id == classroom_id
        )
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def delete_override(
        self, classroom_id: uuid.UUID, unit_id: str
    ) -> bool:
        q = delete(ClassroomCurriculumOverride).where(
            ClassroomCurriculumOverride.classroom_id == classroom_id,
            ClassroomCurriculumOverride.unit_id == unit_id,
        )
        result = await self._db.execute(q)
        return result.rowcount > 0

    async def sync_from_global(
        self, classroom_id: uuid.UUID, course_id: int | None
    ) -> tuple[int, int]:
        """
        Pull any new global units (not yet overridden) into the classroom's
        override table with default values so teachers can see and manage them.

        Returns (added, unchanged).
        """
        units = await self._load_units_with_lessons(course_id)
        existing = {row.unit_id for row in await self.get_overrides(classroom_id)}

        added = 0
        for unit in units:
            if unit.id not in existing:
                self._db.add(ClassroomCurriculumOverride(
                    classroom_id=classroom_id,
                    unit_id=unit.id,
                    phase_id=None,
                    custom_order=None,
                    is_hidden=False,
                    synced_at=datetime.utcnow(),
                ))
                added += 1

        await self._db.flush()
        return added, len(existing)
