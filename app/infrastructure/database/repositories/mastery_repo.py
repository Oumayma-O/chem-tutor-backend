import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import LessonProgress, SkillMastery
from app.infrastructure.database.repositories.base import BaseRepository


class MasteryRepository(BaseRepository[SkillMastery]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SkillMastery, session)

    async def get_for_topic(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
    ) -> SkillMastery | None:
        result = await self._session.execute(
            select(SkillMastery).where(
                SkillMastery.user_id == user_id,
                SkillMastery.unit_id == unit_id,
                SkillMastery.lesson_index == lesson_index,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_for_user(self, user_id: uuid.UUID) -> Sequence[SkillMastery]:
        result = await self._session.execute(
            select(SkillMastery).where(SkillMastery.user_id == user_id)
        )
        return result.scalars().all()

    async def upsert(self, mastery: SkillMastery) -> SkillMastery:
        """
        Insert or update mastery record using PostgreSQL ON CONFLICT.
        Safe under concurrent requests.

        NOTE: level3_unlocked is only SET to True here — never updated back to False.
        The `set_` clause only writes it when it's True (one-way latch).
        """
        set_clause: dict = {
            "mastery_score": mastery.mastery_score,
            "attempts_count": mastery.attempts_count,
            "consecutive_correct": mastery.consecutive_correct,
            "current_difficulty": mastery.current_difficulty,
            "error_counts": mastery.error_counts,
            "category_scores": mastery.category_scores,
            "recent_scores": mastery.recent_scores,
            "updated_at": mastery.updated_at,
        }
        # Level 3 unlock is a one-way latch — only update when setting to True
        if mastery.level3_unlocked:
            set_clause["level3_unlocked"] = True
            set_clause["level3_unlocked_at"] = mastery.level3_unlocked_at

        now = mastery.updated_at or datetime.utcnow()
        stmt = (
            insert(SkillMastery)
            .values(
                id=mastery.id,
                user_id=mastery.user_id,
                unit_id=mastery.unit_id,
                lesson_index=mastery.lesson_index,
                mastery_score=mastery.mastery_score,
                attempts_count=mastery.attempts_count,
                consecutive_correct=mastery.consecutive_correct,
                current_difficulty=mastery.current_difficulty,
                level3_unlocked=mastery.level3_unlocked,
                level3_unlocked_at=mastery.level3_unlocked_at,
                category_scores=mastery.category_scores or {},
                error_counts=mastery.error_counts or {},
                recent_scores=mastery.recent_scores or [],
                updated_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_mastery_user_lesson",
                set_=set_clause,
            )
            .returning(SkillMastery)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_class_mastery(
        self,
        user_ids: list[uuid.UUID],
        unit_id: str,
    ) -> Sequence[SkillMastery]:
        """Bulk fetch mastery for a list of students in a unit."""
        result = await self._session.execute(
            select(SkillMastery).where(
                SkillMastery.user_id.in_(user_ids),
                SkillMastery.unit_id == unit_id,
            )
        )
        return result.scalars().all()


class TopicProgressRepository:
    """CRUD for the lesson_progress table."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_unit_progress(
        self,
        user_id: uuid.UUID,
        unit_id: str,
    ) -> list[LessonProgress]:
        result = await self._session.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == user_id,
                LessonProgress.unit_id == unit_id,
            )
        )
        return list(result.scalars().all())

    async def get_all_for_user(self, user_id: uuid.UUID) -> list[LessonProgress]:
        result = await self._session.execute(
            select(LessonProgress).where(LessonProgress.user_id == user_id)
        )
        return list(result.scalars().all())

    async def upsert_status(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        status: str,
    ) -> LessonProgress:
        stmt = (
            insert(LessonProgress)
            .values(
                user_id=user_id,
                unit_id=unit_id,
                lesson_index=lesson_index,
                status=status,
                updated_at=datetime.utcnow(),
            )
            .on_conflict_do_update(
                index_elements=["user_id", "unit_id", "lesson_index"],
                set_={"status": status, "updated_at": datetime.utcnow()},
            )
            .returning(LessonProgress)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
