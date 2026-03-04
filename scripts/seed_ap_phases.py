"""
Seed: AP Chemistry default phases + unit assignments.

Run with:
    docker compose exec app python -m scripts.seed_ap_phases

What it does
────────────
1. Looks up (or creates) the AP Chemistry course row.
2. Creates the 3 canonical AP Chemistry phases.
3. Assigns existing unit rows to phases via UPDATE units SET phase_id = ...

This is idempotent — re-running will update phase names / order without
duplicating rows, and will reassign unit phase_ids.

AP Chemistry curriculum (College Board, 9 official units)
──────────────────────────────────────────────────────────
Phase 1 — Foundations of Matter (Units 1–3)
  1. Atomic Structure and Properties
  2. Molecular and Ionic Compound Structure and Properties
  3. Intermolecular Forces and Properties

Phase 2 — Reactions and Energy (Units 4–7)
  4. Chemical Reactions
  5. Kinetics
  6. Thermodynamics
  7. Equilibrium

Phase 3 — Advanced Concepts (Units 8–9)
  8. Acids and Bases
  9. Applications of Thermodynamics

The unit_ids below must match the slugs already in your `units` table.
Adjust the UNIT_SLUG_MAP if your slugs differ.
"""

import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, ".")

from app.infrastructure.database.connection import engine


# ── Adjust these slugs to match your units.id values ─────────

AP_PHASES = [
    {
        "name": "Phase 1: Foundations of Matter",
        "description": "Atomic structure, bonding, and intermolecular forces.",
        "sort_order": 0,
        "color": "#6366f1",   # indigo
        "units": [
            # (unit_id slug, order_within_phase)
            ("atomic-structure-properties",         0),
            ("molecular-ionic-structure-properties", 1),
            ("intermolecular-forces-properties",    2),
        ],
    },
    {
        "name": "Phase 2: Reactions and Energy",
        "description": "Chemical reactions, kinetics, thermodynamics, and equilibrium.",
        "sort_order": 1,
        "color": "#f59e0b",   # amber
        "units": [
            ("chemical-reactions",  0),
            ("kinetics",            1),
            ("thermodynamics",      2),
            ("equilibrium",         3),
        ],
    },
    {
        "name": "Phase 3: Advanced Concepts",
        "description": "Acids, bases, and applications of thermodynamics.",
        "sort_order": 2,
        "color": "#10b981",   # emerald
        "units": [
            ("acids-and-bases",              0),
            ("applications-thermodynamics",  1),
        ],
    },
]


# ── Helpers ───────────────────────────────────────────────────

async def get_or_create_course(conn, name: str) -> int:
    r = await conn.execute(
        text("SELECT id FROM courses WHERE name = :n"), {"n": name}
    )
    row = r.fetchone()
    if row:
        return row[0]
    r = await conn.execute(
        text("INSERT INTO courses (name, sort_order) VALUES (:n, 99) RETURNING id"),
        {"n": name},
    )
    return r.fetchone()[0]


async def upsert_phase(conn, course_id: int, phase: dict) -> int:
    """Insert or update a phase; returns its id."""
    r = await conn.execute(
        text(
            "SELECT id FROM phases WHERE course_id = :cid AND sort_order = :so"
        ),
        {"cid": course_id, "so": phase["sort_order"]},
    )
    row = r.fetchone()
    if row:
        phase_id = row[0]
        await conn.execute(text("""
            UPDATE phases
               SET name        = :name,
                   description = :desc,
                   color       = :color
             WHERE id = :id
        """), {
            "name":  phase["name"],
            "desc":  phase["description"],
            "color": phase["color"],
            "id":    phase_id,
        })
        print(f"  [updated] phase '{phase['name']}' (id={phase_id})")
    else:
        r = await conn.execute(text("""
            INSERT INTO phases (name, description, course_id, sort_order, color)
            VALUES (:name, :desc, :cid, :so, :color)
            RETURNING id
        """), {
            "name":  phase["name"],
            "desc":  phase["description"],
            "cid":   course_id,
            "so":    phase["sort_order"],
            "color": phase["color"],
        })
        phase_id = r.fetchone()[0]
        print(f"  [created] phase '{phase['name']}' (id={phase_id})")
    return phase_id


async def assign_units(conn, phase_id: int, units: list[tuple[str, int]]) -> None:
    for unit_id, order in units:
        r = await conn.execute(
            text("SELECT id FROM units WHERE id = :uid"), {"uid": unit_id}
        )
        if not r.fetchone():
            print(f"    [warn] unit '{unit_id}' not found — skipping")
            continue
        await conn.execute(text("""
            UPDATE units
               SET phase_id           = :pid,
                   order_within_phase = :ord
             WHERE id = :uid
        """), {"pid": phase_id, "ord": order, "uid": unit_id})
        print(f"    [assigned] {unit_id} → phase {phase_id}, order {order}")


# ── Entry point ───────────────────────────────────────────────

async def run() -> None:
    print("Seeding AP Chemistry phases…")
    async with engine.begin() as conn:
        course_id = await get_or_create_course(conn, "AP Chemistry")
        print(f"AP Chemistry course id = {course_id}")

        for phase_data in AP_PHASES:
            phase_id = await upsert_phase(conn, course_id, phase_data)
            await assign_units(conn, phase_id, phase_data["units"])

    print("\nSeed complete.")
    print(
        "\nNOTE: If your unit slugs differ from the defaults, edit the "
        "AP_PHASES['units'] lists in this script to match your units.id values."
    )


if __name__ == "__main__":
    asyncio.run(run())
