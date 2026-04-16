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
        unit_id: str,
        lesson_index: int,
        limit: int = 20,
    ) -> Sequence[ProblemAttempt]:
        result = await self._session.execute(
            select(ProblemAttempt)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.unit_id == unit_id,
                ProblemAttempt.lesson_index == lesson_index,
            )
            .order_by(ProblemAttempt.started_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_recent_scores(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        window: int = 5,
        min_level: int = 2,
    ) -> list[float]:
        """Returns up to `window` most recent scores for mastery computation.

        Level 1 (worked examples) is excluded by default — the student is
        observing, not demonstrating competence, so it should not count toward mastery.
        """
        result = await self._session.execute(
            select(ProblemAttempt.score)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.unit_id == unit_id,
                ProblemAttempt.lesson_index == lesson_index,
                ProblemAttempt.is_complete == True,
                ProblemAttempt.score.is_not(None),
                ProblemAttempt.level >= min_level,
            )
            .order_by(ProblemAttempt.completed_at.desc())
            .limit(window)
        )
        rows = result.scalars().all()
        return [float(s) for s in rows]

    async def get_recent_scores_for_level(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        level: int,
        window: int = 5,
        passing_score: float = 0.0,
    ) -> list[float]:
        """Returns up to `window` most recent completed scores for a specific level.

        Pass `passing_score` > 0 to exclude low-quality attempts from band-filling.
        """
        q = (
            select(ProblemAttempt.score)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.unit_id == unit_id,
                ProblemAttempt.lesson_index == lesson_index,
                ProblemAttempt.is_complete == True,  # noqa: E712
                ProblemAttempt.score.is_not(None),
                ProblemAttempt.level == level,
            )
            .order_by(ProblemAttempt.completed_at.desc())
            .limit(window)
        )
        if passing_score > 0:
            q = q.where(ProblemAttempt.score >= passing_score)
        result = await self._session.execute(q)
        rows = result.scalars().all()
        return [float(s) for s in rows]

    async def get_max_level_attempted(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
    ) -> int:
        """Return the highest level the student has a completed attempt for (1–3). 0 if none."""
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.max(ProblemAttempt.level))
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.unit_id == unit_id,
                ProblemAttempt.lesson_index == lesson_index,
                ProblemAttempt.is_complete == True,
            )
        )
        return int(result.scalar() or 0)

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
        unit_id: str,
        lesson_index: int,
        level: int,
    ) -> ProblemAttempt | None:
        """Return the latest incomplete attempt for a (user, unit, lesson, level) slot."""
        result = await self._session.execute(
            select(ProblemAttempt)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.unit_id == unit_id,
                ProblemAttempt.lesson_index == lesson_index,
                ProblemAttempt.level == level,
                ProblemAttempt.is_complete == False,  # noqa: E712
            )
            .order_by(ProblemAttempt.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_problem(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        level: int,
        problem_id: str,
    ) -> ProblemAttempt | None:
        """Return the most recent attempt for one exact playlist problem."""
        result = await self._session.execute(
            select(ProblemAttempt)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.unit_id == unit_id,
                ProblemAttempt.lesson_index == lesson_index,
                ProblemAttempt.level == level,
                ProblemAttempt.problem_id == problem_id,
            )
            .order_by(ProblemAttempt.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_problems(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        level: int,
        problem_ids: list[str],
    ) -> dict[str, ProblemAttempt]:
        """Return latest attempt per problem_id for a playlist slot."""
        if not problem_ids:
            return {}
        result = await self._session.execute(
            select(ProblemAttempt)
            .where(
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.unit_id == unit_id,
                ProblemAttempt.lesson_index == lesson_index,
                ProblemAttempt.level == level,
                ProblemAttempt.problem_id.in_(problem_ids),
            )
            .order_by(ProblemAttempt.problem_id.asc(), ProblemAttempt.started_at.desc())
        )
        latest: dict[str, ProblemAttempt] = {}
        for attempt in result.scalars().all():
            pid = attempt.problem_id
            if pid not in latest:
                latest[pid] = attempt
        return latest

    async def get_class_attempts(
        self,
        class_id: uuid.UUID,
        unit_id: str,
        lesson_index: int | None = None,
    ) -> Sequence[ProblemAttempt]:
        q = select(ProblemAttempt).where(
            ProblemAttempt.class_id == class_id,
            ProblemAttempt.unit_id == unit_id,
            ProblemAttempt.is_complete == True,
        )
        if lesson_index is not None:
            q = q.where(ProblemAttempt.lesson_index == lesson_index)
        result = await self._session.execute(q.order_by(ProblemAttempt.completed_at.desc()))
        return result.scalars().all()


class MisconceptionRepository(BaseRepository[MisconceptionLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(MisconceptionLog, session)

    async def get_class_misconceptions(
        self,
        class_id: uuid.UUID,
        unit_id: str,
        lesson_index: int | None = None,
    ) -> Sequence[MisconceptionLog]:
        q = select(MisconceptionLog).where(
            MisconceptionLog.class_id == class_id,
            MisconceptionLog.unit_id == unit_id,
        )
        if lesson_index is not None:
            q = q.where(MisconceptionLog.lesson_index == lesson_index)
        result = await self._session.execute(q)
        return result.scalars().all()

    async def get_user_error_counts(
        self, user_id: uuid.UUID, unit_id: str
    ) -> dict[str, int]:
        """Returns {category: count} for a student in a unit."""
        result = await self._session.execute(
            select(MisconceptionLog.error_category)
            .where(
                MisconceptionLog.user_id == user_id,
                MisconceptionLog.unit_id == unit_id,
            )
        )
        counts: dict[str, int] = {}
        for (cat,) in result.all():
            counts[cat] = counts.get(cat, 0) + 1
        return counts
