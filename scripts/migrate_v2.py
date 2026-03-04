"""
Migration v2 — Master Lesson Library schema changes.

  1. Add `slug` VARCHAR(100) UNIQUE NOT NULL to lessons
  2. Add `is_ap_only` BOOLEAN NOT NULL DEFAULT FALSE to lessons
  3. Create `unit_lessons` junction table (unit_id, lesson_id, lesson_order)

Run once before re-seeding:
  python -m scripts.migrate_v2
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.config import get_settings

settings = get_settings()


async def migrate() -> None:
    engine = create_async_engine(settings.database_url, echo=False)

    async with engine.begin() as conn:
        print("Running migration v2...")

        # 1. Add slug to lessons (nullable first so existing rows don't fail)
        await conn.execute(text(
            "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS slug VARCHAR(100)"
        ))
        print("  ✓ lessons.slug column added")

        # 2. Add is_ap_only to lessons
        await conn.execute(text(
            "ALTER TABLE lessons ADD COLUMN IF NOT EXISTS is_ap_only BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        print("  ✓ lessons.is_ap_only column added")

        # 3. Backfill slugs for existing lessons (generate from id + title)
        #    Pattern: 'L-{unit_id}-{topic_index}' as a safe temporary slug
        await conn.execute(text(
            "UPDATE lessons SET slug = 'L-legacy-' || id::text WHERE slug IS NULL"
        ))
        print("  ✓ legacy slugs backfilled")

        # 4. Make slug NOT NULL + UNIQUE now that all rows are filled
        await conn.execute(text(
            "ALTER TABLE lessons ALTER COLUMN slug SET NOT NULL"
        ))
        # Add unique constraint only if it doesn't exist
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_lessons_slug'
                ) THEN
                    ALTER TABLE lessons ADD CONSTRAINT uq_lessons_slug UNIQUE (slug);
                END IF;
            END $$
        """))
        print("  ✓ lessons.slug NOT NULL + UNIQUE")

        # 5. Create unit_lessons junction table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS unit_lessons (
                unit_id     VARCHAR(100) NOT NULL REFERENCES units(id) ON DELETE CASCADE,
                lesson_id   INTEGER      NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
                lesson_order INTEGER     NOT NULL,
                PRIMARY KEY (unit_id, lesson_id)
            )
        """))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_unit_lessons_unit ON unit_lessons(unit_id)"
        ))
        print("  ✓ unit_lessons table created")

    await engine.dispose()
    print("\n✅  Migration v2 complete. Now run: python -m scripts.seed")


if __name__ == "__main__":
    asyncio.run(migrate())
