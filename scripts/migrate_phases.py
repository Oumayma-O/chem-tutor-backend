"""
Migration: introduce Phase-based curriculum grouping.

Run with:
    docker compose exec app python -m scripts.migrate_phases

What it does
────────────
1. CREATE TABLE phases
2. ALTER TABLE units    ADD COLUMN phase_id            INT REFERENCES phases(id) ON DELETE SET NULL
3. ALTER TABLE units    ADD COLUMN order_within_phase  INT
4. CREATE TABLE classroom_curriculum_overrides
5. CREATE supporting indexes and constraints

Safe to run multiple times — each step checks existence first.
"""

import asyncio
import sys

from sqlalchemy import text

sys.path.insert(0, ".")

from app.infrastructure.database.connection import engine


# ── Helpers ───────────────────────────────────────────────────

async def column_exists(conn, table: str, column: str) -> bool:
    r = await conn.execute(text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return r.fetchone() is not None


async def table_exists(conn, table: str) -> bool:
    r = await conn.execute(text(
        "SELECT 1 FROM information_schema.tables WHERE table_name = :t"
    ), {"t": table})
    return r.fetchone() is not None


async def index_exists(conn, index: str) -> bool:
    r = await conn.execute(text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :i"
    ), {"i": index})
    return r.fetchone() is not None


async def constraint_exists(conn, table: str, constraint: str) -> bool:
    r = await conn.execute(text(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE table_name = :t AND constraint_name = :c"
    ), {"t": table, "c": constraint})
    return r.fetchone() is not None


# ── Migration steps ───────────────────────────────────────────

async def step_phases_table(conn) -> None:
    if await table_exists(conn, "phases"):
        print("  [skip] phases table already exists")
        return
    await conn.execute(text("""
        CREATE TABLE phases (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(200) NOT NULL,
            description TEXT,
            course_id   INTEGER REFERENCES courses(id),
            sort_order  INTEGER NOT NULL DEFAULT 0,
            color       VARCHAR(50),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_phase_course_order UNIQUE (course_id, sort_order)
        )
    """))
    await conn.execute(text(
        "CREATE INDEX ix_phases_course ON phases (course_id)"
    ))
    print("  [done] created phases table")


async def step_units_phase_columns(conn) -> None:
    if not await column_exists(conn, "units", "phase_id"):
        await conn.execute(text(
            "ALTER TABLE units ADD COLUMN phase_id INTEGER "
            "REFERENCES phases(id) ON DELETE SET NULL"
        ))
        await conn.execute(text(
            "CREATE INDEX ix_units_phase ON units (phase_id)"
        ))
        print("  [done] added units.phase_id")
    else:
        print("  [skip] units.phase_id already exists")

    if not await column_exists(conn, "units", "order_within_phase"):
        await conn.execute(text(
            "ALTER TABLE units ADD COLUMN order_within_phase INTEGER"
        ))
        print("  [done] added units.order_within_phase")
    else:
        print("  [skip] units.order_within_phase already exists")


async def step_cco_table(conn) -> None:
    if await table_exists(conn, "classroom_curriculum_overrides"):
        print("  [skip] classroom_curriculum_overrides table already exists")
        return

    await conn.execute(text("""
        CREATE TABLE classroom_curriculum_overrides (
            id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            classroom_id UUID NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
            unit_id      VARCHAR(100) NOT NULL REFERENCES units(id) ON DELETE CASCADE,
            phase_id     INTEGER REFERENCES phases(id) ON DELETE SET NULL,
            custom_order INTEGER,
            is_hidden    BOOLEAN NOT NULL DEFAULT FALSE,
            synced_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_cco_classroom_unit UNIQUE (classroom_id, unit_id)
        )
    """))
    await conn.execute(text(
        "CREATE INDEX ix_cco_classroom ON classroom_curriculum_overrides (classroom_id)"
    ))
    await conn.execute(text(
        "CREATE INDEX ix_cco_unit ON classroom_curriculum_overrides (unit_id)"
    ))
    print("  [done] created classroom_curriculum_overrides table")


# ── Entry point ───────────────────────────────────────────────

async def run() -> None:
    print("Starting phases migration…")
    async with engine.begin() as conn:
        await step_phases_table(conn)
        await step_units_phase_columns(conn)
        await step_cco_table(conn)
    print("Migration complete.")


if __name__ == "__main__":
    asyncio.run(run())
