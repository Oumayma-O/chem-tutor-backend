"""
One-time migration: finish the chapter→unit / topic→lesson DB rename.

Tables renamed:
  chapters              → units            (if still old)
  topics                → lessons          (if still old)
  topic_standards       → lesson_standards
  user_topic_playlists  → user_lesson_playlists
  topic_progress        → lesson_progress

Columns renamed in every table that has them:
  chapter_id  → unit_id
  topic_index → lesson_index
  topic_id    → lesson_id      (curriculum_documents, lesson_standards)

Constraint / index names updated to match new column names.

Run once (inside Docker or locally):
  python -m scripts.migrate_rename_tables
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

settings = get_settings()


# ── helpers ───────────────────────────────────────────────────

async def _table_exists(conn, name: str) -> bool:
    r = await conn.execute(text(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=:t"
    ), {"t": name})
    return r.fetchone() is not None


async def _column_exists(conn, table: str, col: str) -> bool:
    r = await conn.execute(text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
    ), {"t": table, "c": col})
    return r.fetchone() is not None


async def _constraint_exists(conn, constraint: str) -> bool:
    r = await conn.execute(text(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE constraint_schema='public' AND constraint_name=:c"
    ), {"c": constraint})
    return r.fetchone() is not None


async def _index_exists(conn, index: str) -> bool:
    r = await conn.execute(text(
        "SELECT 1 FROM pg_indexes "
        "WHERE schemaname='public' AND indexname=:i"
    ), {"i": index})
    return r.fetchone() is not None


async def rename_table(conn, old: str, new: str) -> None:
    if await _table_exists(conn, old) and not await _table_exists(conn, new):
        await conn.execute(text(f'ALTER TABLE "{old}" RENAME TO "{new}"'))
        print(f"  ✓ table {old} → {new}")
    elif await _table_exists(conn, new):
        print(f"  · {new} already exists, skip")
    else:
        print(f"  · {old} not found, skip")


async def rename_column(conn, table: str, old_col: str, new_col: str) -> None:
    if not await _table_exists(conn, table):
        return
    if await _column_exists(conn, table, old_col):
        await conn.execute(text(
            f'ALTER TABLE "{table}" RENAME COLUMN "{old_col}" TO "{new_col}"'
        ))
        print(f"  ✓ {table}.{old_col} → {new_col}")
    elif await _column_exists(conn, table, new_col):
        print(f"  · {table}.{new_col} already renamed, skip")


# ── main ──────────────────────────────────────────────────────

async def migrate() -> None:
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:

        print("\n── Table renames ───────────────────────────────────────")
        await rename_table(conn, "chapters", "units")
        await rename_table(conn, "topics", "lessons")
        await rename_table(conn, "topic_standards", "lesson_standards")
        await rename_table(conn, "user_topic_playlists", "user_lesson_playlists")
        await rename_table(conn, "topic_progress", "lesson_progress")

        print("\n── Column renames: chapter_id → unit_id ────────────────")
        tables_with_chapter_id = [
            "lessons", "problem_cache", "problem_attempts",
            "skill_mastery", "thinking_tracker_logs", "misconception_logs",
            "curriculum_documents", "exit_tickets", "user_lesson_playlists",
            "lesson_progress", "generation_logs", "classrooms",
        ]
        for tbl in tables_with_chapter_id:
            await rename_column(conn, tbl, "chapter_id", "unit_id")

        print("\n── Column renames: topic_index → lesson_index ──────────")
        tables_with_topic_index = [
            "lessons", "problem_cache", "problem_attempts",
            "skill_mastery", "thinking_tracker_logs", "misconception_logs",
            "exit_tickets", "user_lesson_playlists",
            "lesson_progress", "generation_logs",
        ]
        for tbl in tables_with_topic_index:
            await rename_column(conn, tbl, "topic_index", "lesson_index")

        print("\n── Column renames: topic_id → lesson_id ────────────────")
        await rename_column(conn, "lesson_standards", "topic_id", "lesson_id")
        await rename_column(conn, "curriculum_documents", "topic_id", "lesson_id")

        print("\n── Constraint renames ──────────────────────────────────")
        # uq_topic_chapter_index → uq_lesson_unit_index (lessons table)
        if await _constraint_exists(conn, "uq_topic_chapter_index"):
            await conn.execute(text(
                "ALTER TABLE lessons RENAME CONSTRAINT "
                '"uq_topic_chapter_index" TO "uq_lesson_unit_index"'
            ))
            print("  ✓ uq_topic_chapter_index → uq_lesson_unit_index")

        # uq_mastery_user_topic → uq_mastery_user_lesson (skill_mastery table)
        if await _constraint_exists(conn, "uq_mastery_user_topic"):
            await conn.execute(text(
                "ALTER TABLE skill_mastery RENAME CONSTRAINT "
                '"uq_mastery_user_topic" TO "uq_mastery_user_lesson"'
            ))
            print("  ✓ uq_mastery_user_topic → uq_mastery_user_lesson")

        print("\n── Index renames ───────────────────────────────────────")
        index_renames = [
            ("ix_topics_chapter",            "ix_lessons_unit"),
            ("ix_problem_cache_key",          "ix_problem_cache_key"),        # rebuilt below if needed
            ("ix_attempts_user_chapter",      "ix_attempts_user_unit"),
            ("ix_mastery_user",               "ix_mastery_user"),             # no change
            ("ix_thinking_user_chapter",      "ix_thinking_user_unit"),
            ("ix_misconception_chapter",      "ix_misconception_unit"),
            ("ix_playlist_user_chapter",      "ix_playlist_user_unit"),
            ("ix_topic_progress_user_chapter","ix_lesson_progress_user_unit"),
            ("ix_gen_logs_chapter_topic",     "ix_gen_logs_unit_lesson"),
        ]
        for old_ix, new_ix in index_renames:
            if old_ix == new_ix:
                continue
            if await _index_exists(conn, old_ix):
                await conn.execute(text(f'ALTER INDEX "{old_ix}" RENAME TO "{new_ix}"'))
                print(f"  ✓ index {old_ix} → {new_ix}")
            elif await _index_exists(conn, new_ix):
                print(f"  · {new_ix} already renamed, skip")

    await engine.dispose()
    print("\n✅  Migration complete.\n")


if __name__ == "__main__":
    asyncio.run(migrate())
