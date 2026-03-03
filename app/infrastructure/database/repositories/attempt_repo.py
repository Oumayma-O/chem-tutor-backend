import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import MisconceptionLog, ProblemAttempt
from app.infrastructure.database.repositories.base import BaseRepository


class AttemptRepository(BaseRepository[ProblemAttempt]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ProblemAttempt, session)

    async def get_user_attempts(
        self,
        user_id: uuid.UUID,
        chapter_id: str,
        topic_index: int,
        limit: int = 20,
    ) -> Sequence[ProblemAttempt]:
        result = await self._session.execute(
            select(ProblemAttempt)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.chapter_id == chapter_id,
                ProblemAttempt.topic_index == topic_index,
            )
            .order_by(ProblemAttempt.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent_scores(
        self,
        user_id: uuid.UUID,
        chapter_id: str,
        topic_index: int,
        window: int = 5,
    ) -> list[float]:
        """Returns up to `window` most recent scores for mastery computation."""
        result = await self._session.execute(
            select(ProblemAttempt.score)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.chapter_id == chapter_id,
                ProblemAttempt.topic_index == topic_index,
                ProblemAttempt.is_complete == True,
                ProblemAttempt.score.is_not(None),
            )
            .order_by(ProblemAttempt.completed_at.desc())
            .limit(window)
        )
        rows = result.scalars().all()
        return [float(s) for s in rows]

    async def mark_complete(
        self,
        attempt_id: uuid.UUID,
        score: float,
        step_log: list[dict],
    ) -> None:
        await self._session.execute(
            update(ProblemAttempt)
            .where(ProblemAttempt.id == attempt_id)
            .values(
                is_complete=True,
                score=score,
                step_log=step_log,
                completed_at=datetime.utcnow(),
            )
        )

    async def update_step_log(
        self,
        attempt_id: uuid.UUID,
        step_log: list[dict],
    ) -> None:
        """Persist mid-problem progress so the student can resume after logout."""
        await self._session.execute(
            update(ProblemAttempt)
            .where(ProblemAttempt.id == attempt_id, ProblemAttempt.is_complete == False)  # noqa: E712
            .values(step_log=step_log)
        )

    async def get_in_progress(
        self,
        user_id: uuid.UUID,
        chapter_id: str,
        topic_index: int,
        level: int,
    ) -> ProblemAttempt | None:
        """Return the latest incomplete attempt for a (user, chapter, topic, level) slot."""
        result = await self._session.execute(
            select(ProblemAttempt)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.chapter_id == chapter_id,
                ProblemAttempt.topic_index == topic_index,
                ProblemAttempt.level == level,
                ProblemAttempt.is_complete == False,  # noqa: E712
            )
            .order_by(ProblemAttempt.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_class_attempts(
        self,
        class_id: uuid.UUID,
        chapter_id: str,
        topic_index: int | None = None,
    ) -> Sequence[ProblemAttempt]:
        q = select(ProblemAttempt).where(
            ProblemAttempt.class_id == class_id,
            ProblemAttempt.chapter_id == chapter_id,
            ProblemAttempt.is_complete == True,
        )
        if topic_index is not None:
            q = q.where(ProblemAttempt.topic_index == topic_index)
        result = await self._session.execute(q.order_by(ProblemAttempt.completed_at.desc()))
        return result.scalars().all()


class MisconceptionRepository(BaseRepository[MisconceptionLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(MisconceptionLog, session)

    async def get_class_misconceptions(
        self,
        class_id: uuid.UUID,
        chapter_id: str,
        topic_index: int | None = None,
    ) -> Sequence[MisconceptionLog]:
        q = select(MisconceptionLog).where(
            MisconceptionLog.class_id == class_id,
            MisconceptionLog.chapter_id == chapter_id,
        )
        if topic_index is not None:
            q = q.where(MisconceptionLog.topic_index == topic_index)
        result = await self._session.execute(q)
        return result.scalars().all()

    async def get_user_error_counts(
        self, user_id: uuid.UUID, chapter_id: str
    ) -> dict[str, int]:
        """Returns {category: count} for a student in a chapter."""
        result = await self._session.execute(
            select(MisconceptionLog.error_category)
            .where(
                MisconceptionLog.user_id == user_id,
                MisconceptionLog.chapter_id == chapter_id,
            )
        )
        counts: dict[str, int] = {}
        for (cat,) in result.all():
            counts[cat] = counts.get(cat, 0) + 1
        return counts
