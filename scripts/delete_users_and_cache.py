"""
Delete all user accounts and problem cache.

Wipes every user-owned row (auth, profiles, attempts, mastery, playlists, progress,
misconceptions, thinking logs) plus the shared problem cache and generation logs.
Content tables (chapters, topics, standards, curriculum documents) are left intact.

Usage:
  python -m scripts.delete_users_and_cache          # confirms before deleting
  python -m scripts.delete_users_and_cache --force  # skips confirmation
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.infrastructure.database.models import (
    ExitTicketResponse,
    ExitTicket,
    ClassroomStudent,
    Classroom,
    StudentInterest,
    UserProfile,
    User,
    MisconceptionLog,
    ThinkingTrackerLog,
    ProblemAttempt,
    SkillMastery,
    TopicProgress,
    UserTopicPlaylist,
    ProblemCache,
    GenerationLog,
)


_TABLES_IN_ORDER = [
    # Dependent rows first (FK children before parents)
    ExitTicketResponse,
    ExitTicket,
    ClassroomStudent,
    Classroom,
    StudentInterest,
    MisconceptionLog,
    ThinkingTrackerLog,
    ProblemAttempt,
    SkillMastery,
    TopicProgress,
    UserTopicPlaylist,
    UserProfile,
    User,
    # Shared cache / logs (no FK to users)
    ProblemCache,
    GenerationLog,
]


async def run(force: bool = False) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    if not force:
        print("This will permanently delete ALL users, their data, and the problem cache.")
        confirm = input("Type 'yes' to continue: ").strip().lower()
        if confirm != "yes":
            print("Aborted.")
            await engine.dispose()
            return

    async with Session() as session:
        counts: dict[str, int] = {}
        for model in _TABLES_IN_ORDER:
            tname = model.__tablename__  # type: ignore[attr-defined]
            result = await session.execute(delete(model))
            counts[tname] = result.rowcount  # type: ignore[attr-defined]

        # Reset alembic_version only if you also want migrations to re-run (opt-in)
        await session.commit()

    await engine.dispose()

    print("\nDeleted rows:")
    for tname, n in counts.items():
        if n:
            print(f"  {tname:<35} {n:>6} rows")
    print("\nDone. Content tables (chapters, topics, etc.) are untouched.")


if __name__ == "__main__":
    force = "--force" in sys.argv
    asyncio.run(run(force=force))
