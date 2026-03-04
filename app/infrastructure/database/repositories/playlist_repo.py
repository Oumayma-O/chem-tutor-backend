"""Repository for user lesson playlists."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserLessonPlaylist

# Pedagogical caps: max new problems a student can generate per level/slot.
# After the cap, they can only navigate their existing playlist.
#   L1 (worked examples) : 3 — see the solution pattern, then do it yourself
#   L2 (faded)           : 5 — enough practice variety before mastery check
#   L3 (challenge)       : 5 — high-effort problems; spaced practice elsewhere
MAX_PROBLEMS_PER_LEVEL: dict[int, int] = {1: 3, 2: 5, 3: 5}


class UserLessonPlaylistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        level: int,
        difficulty: str,
    ) -> UserLessonPlaylist | None:
        result = await self._session.execute(
            select(UserLessonPlaylist).where(
                UserLessonPlaylist.user_id == user_id,
                UserLessonPlaylist.unit_id == unit_id,
                UserLessonPlaylist.lesson_index == lesson_index,
                UserLessonPlaylist.level == level,
                UserLessonPlaylist.difficulty == difficulty,
            )
        )
        return result.scalar_one_or_none()

    async def append_and_advance(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        level: int,
        difficulty: str,
        problem_data: dict,
    ) -> UserLessonPlaylist:
        """Append a new problem to the end of the playlist and advance current_index to it."""
        existing = await self.get(user_id, unit_id, lesson_index, level, difficulty)
        now = datetime.utcnow()
        new_problems = (list(existing.problems) if existing else []) + [problem_data]
        new_index = len(new_problems) - 1

        stmt = (
            insert(UserLessonPlaylist)
            .values(
                user_id=user_id,
                unit_id=unit_id,
                lesson_index=lesson_index,
                level=level,
                difficulty=difficulty,
                problems=new_problems,
                current_index=new_index,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "unit_id", "lesson_index", "level", "difficulty"],
                set_={"problems": new_problems, "current_index": new_index, "updated_at": now},
            )
            .returning(UserLessonPlaylist)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update_index(
        self,
        playlist: UserLessonPlaylist,
        new_index: int,
    ) -> UserLessonPlaylist:
        """Update current_index only (for prev/next navigation through seen problems)."""
        now = datetime.utcnow()
        stmt = (
            insert(UserLessonPlaylist)
            .values(
                user_id=playlist.user_id,
                unit_id=playlist.unit_id,
                lesson_index=playlist.lesson_index,
                level=playlist.level,
                difficulty=playlist.difficulty,
                problems=playlist.problems,
                current_index=new_index,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "unit_id", "lesson_index", "level", "difficulty"],
                set_={"current_index": new_index, "updated_at": now},
            )
            .returning(UserLessonPlaylist)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()


