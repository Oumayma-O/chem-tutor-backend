"""Repository for problem cache (Level 1 worked examples and generated problems)."""

import random
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ProblemCache
from app.infrastructure.database.repositories.base import BaseRepository


class ProblemCacheRepository(BaseRepository[ProblemCache]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProblemCache, session)

    async def find(
        self,
        chapter_id: str,
        topic_index: int,
        difficulty: str,
        level: int,
        context_tag: str | None = None,
    ) -> Sequence[ProblemCache]:
        """
        Return all unexpired cached problems matching the key.
        context_tag=None matches both NULL entries and NULL-only (generic) entries.
        """
        now = datetime.utcnow()
        q = select(ProblemCache).where(
            ProblemCache.chapter_id == chapter_id,
            ProblemCache.topic_index == topic_index,
            ProblemCache.difficulty == difficulty,
            ProblemCache.level == level,
        )
        # Expire check
        q = q.where(
            (ProblemCache.expires_at == None) | (ProblemCache.expires_at > now)  # noqa: E711
        )
        if context_tag is not None:
            # Try exact match first; caller picks randomly for variety
            q = q.where(ProblemCache.context_tag == context_tag)
        else:
            q = q.where(ProblemCache.context_tag == None)  # noqa: E711

        result = await self._session.execute(q.order_by(ProblemCache.created_at.desc()))
        return result.scalars().all()

    async def pick_random(
        self,
        chapter_id: str,
        topic_index: int,
        difficulty: str,
        level: int,
        context_tag: str | None = None,
        exclude_ids: set[str] | None = None,
    ) -> ProblemCache | None:
        """
        Pick one cached problem at random (for variety).
        Falls back to generic (context_tag=None) if no contextual match.
        exclude_ids: ProblemOutput.id strings to deprioritise (prefer unseen).
        """
        def _pick(rows: list[ProblemCache]) -> ProblemCache:
            if exclude_ids:
                unseen = [r for r in rows if r.problem_data.get("id") not in exclude_ids]
                return random.choice(unseen if unseen else rows)
            return random.choice(rows)

        rows = await self.find(chapter_id, topic_index, difficulty, level, context_tag)
        if rows:
            return _pick(list(rows))

        if context_tag is not None:
            generic = await self.find(chapter_id, topic_index, difficulty, level, None)
            if generic:
                return _pick(list(generic))

        return None

    async def save(
        self,
        chapter_id: str,
        topic_index: int,
        difficulty: str,
        level: int,
        context_tag: str | None,
        problem_data: dict,
        expires_at: datetime | None = None,
    ) -> ProblemCache:
        entry = ProblemCache(
            chapter_id=chapter_id,
            topic_index=topic_index,
            difficulty=difficulty,
            level=level,
            context_tag=context_tag,
            problem_data=problem_data,
            expires_at=expires_at,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def count(
        self,
        chapter_id: str,
        topic_index: int,
        difficulty: str,
        level: int,
        context_tag: str | None = None,
    ) -> int:
        rows = await self.find(chapter_id, topic_index, difficulty, level, context_tag)
        return len(rows)
