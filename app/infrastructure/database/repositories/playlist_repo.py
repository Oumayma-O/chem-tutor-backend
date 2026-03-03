"""Repository for user topic playlists."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserTopicPlaylist

# Pedagogical caps: max new problems a student can generate per level/slot.
# After the cap, they can only navigate their existing playlist.
#   L1 (worked examples) : 3 — see the solution pattern, then do it yourself
#   L2 (faded)           : 5 — enough practice variety before mastery check
#   L3 (challenge)       : 5 — high-effort problems; spaced practice elsewhere
MAX_PROBLEMS_PER_LEVEL: dict[int, int] = {1: 3, 2: 5, 3: 5}


class UserTopicPlaylistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self,
        user_id: uuid.UUID,
        chapter_id: str,
        topic_index: int,
        level: int,
        difficulty: str,
    ) -> UserTopicPlaylist | None:
        result = await self._session.execute(
            select(UserTopicPlaylist).where(
                UserTopicPlaylist.user_id == user_id,
                UserTopicPlaylist.chapter_id == chapter_id,
                UserTopicPlaylist.topic_index == topic_index,
                UserTopicPlaylist.level == level,
                UserTopicPlaylist.difficulty == difficulty,
            )
        )
        return result.scalar_one_or_none()

    async def append_and_advance(
        self,
        user_id: uuid.UUID,
        chapter_id: str,
        topic_index: int,
        level: int,
        difficulty: str,
        problem_data: dict,
    ) -> UserTopicPlaylist:
        """Append a new problem to the end of the playlist and advance current_index to it."""
        existing = await self.get(user_id, chapter_id, topic_index, level, difficulty)
        now = datetime.utcnow()
        new_problems = (list(existing.problems) if existing else []) + [problem_data]
        new_index = len(new_problems) - 1

        stmt = (
            insert(UserTopicPlaylist)
            .values(
                user_id=user_id,
                chapter_id=chapter_id,
                topic_index=topic_index,
                level=level,
                difficulty=difficulty,
                problems=new_problems,
                current_index=new_index,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "chapter_id", "topic_index", "level", "difficulty"],
                set_={"problems": new_problems, "current_index": new_index, "updated_at": now},
            )
            .returning(UserTopicPlaylist)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def update_index(
        self,
        playlist: UserTopicPlaylist,
        new_index: int,
    ) -> UserTopicPlaylist:
        """Update current_index only (for prev/next navigation through seen problems)."""
        now = datetime.utcnow()
        stmt = (
            insert(UserTopicPlaylist)
            .values(
                user_id=playlist.user_id,
                chapter_id=playlist.chapter_id,
                topic_index=playlist.topic_index,
                level=playlist.level,
                difficulty=playlist.difficulty,
                problems=playlist.problems,
                current_index=new_index,
                updated_at=now,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "chapter_id", "topic_index", "level", "difficulty"],
                set_={"current_index": new_index, "updated_at": now},
            )
            .returning(UserTopicPlaylist)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
