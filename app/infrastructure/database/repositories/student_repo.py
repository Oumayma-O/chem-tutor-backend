"""Repository for user profiles and student interests."""

import uuid
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    Course,
    Grade,
    Interest,
    StudentInterest,
    UserProfile,
)
from app.infrastructure.database.repositories.base import BaseRepository


class UserProfileRepository(BaseRepository[UserProfile]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(UserProfile, session)

    async def get_by_id(self, user_id: uuid.UUID) -> UserProfile | None:
        result = await self._session.execute(
            select(UserProfile)
            .where(UserProfile.user_id == user_id)
            .options(
                selectinload(UserProfile.grade),
                selectinload(UserProfile.course),
                selectinload(UserProfile.interests).selectinload(StudentInterest.interest),
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, profile: UserProfile) -> UserProfile:
        existing = await self.get_by_id(profile.user_id)
        if existing:
            existing.name = profile.name
            existing.role = profile.role
            existing.grade_id = profile.grade_id
            existing.course_id = profile.course_id
            await self._session.flush()
            return existing
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def set_interests(self, user_id: uuid.UUID, interest_ids: list[int]) -> None:
        """Replace all interests for a user."""
        await self._session.execute(
            delete(StudentInterest).where(StudentInterest.user_id == user_id)
        )
        for iid in interest_ids:
            self._session.add(StudentInterest(user_id=user_id, interest_id=iid))
        await self._session.flush()

    async def get_interest_slugs(self, user_id: uuid.UUID) -> list[str]:
        """Return the slug list for a student — used as context_tags by AI services."""
        result = await self._session.execute(
            select(Interest.slug)
            .join(StudentInterest, StudentInterest.interest_id == Interest.id)
            .where(StudentInterest.user_id == user_id)
        )
        return [row[0] for row in result.all()]


class GradeRepository(BaseRepository[Grade]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Grade, session)

    async def get_all(self) -> Sequence[Grade]:
        result = await self._session.execute(
            select(Grade).order_by(Grade.sort_order)
        )
        return result.scalars().all()


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Course, session)

    async def get_all(self) -> Sequence[Course]:
        result = await self._session.execute(
            select(Course).order_by(Course.sort_order)
        )
        return result.scalars().all()


class InterestRepository(BaseRepository[Interest]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Interest, session)

    async def get_all(self) -> Sequence[Interest]:
        result = await self._session.execute(
            select(Interest).order_by(Interest.sort_order)
        )
        return result.scalars().all()
