"""
One-time migration: rename DB tables
  chapters → units
  topics   → lessons

PostgreSQL automatically updates FK constraints that reference renamed tables,
so no FK surgery is needed.

Run once:
  python -m scripts.migrate_rename_tables
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
        # Check which renames are still needed
        result = await conn.execute(
            text("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('chapters', 'topics', 'units', 'lessons')
            """)
        )
        existing = {row[0] for row in result.fetchall()}
        print(f"Existing tables: {existing}")

        if "chapters" in existing and "units" not in existing:
            await conn.execute(text("ALTER TABLE chapters RENAME TO units"))
            print("  ✓ chapters → units")
        elif "units" in existing:
            print("  · units already exists, skipping chapters rename")

        if "topics" in existing and "lessons" not in existing:
            await conn.execute(text("ALTER TABLE topics RENAME TO lessons"))
            print("  ✓ topics → lessons")
        elif "lessons" in existing:
            print("  · lessons already exists, skipping topics rename")

    await engine.dispose()
    print("\n✅  Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
