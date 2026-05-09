"""Auth profile service for /auth/me and profile-related transforms."""

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.domain.schemas.auth import MeResponse
from app.infrastructure.database.models import Classroom, ClassroomStudent, Interest, User
from app.infrastructure.database.repositories.student_repo import UserProfileRepository


class AuthProfileService:
    """Service that assembles profile payloads for auth endpoints."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def resolve_interest_ids(self, slugs: list[str]) -> list[int]:
        if not slugs:
            return []
        result = await self._db.execute(select(Interest).where(Interest.slug.in_(slugs)))
        return [i.id for i in result.scalars().all()]

    async def build_me_response(self, user_id: uuid.UUID) -> MeResponse:
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        profile = await UserProfileRepository(self._db).get_by_id(user_id)
        grade_name: Optional[str] = profile.grade.name if profile and profile.grade else None
        course_name: Optional[str] = profile.course.name if profile and profile.course else None
        grade_level_parts = [p for p in [grade_name, course_name] if p]
        grade_level = " · ".join(grade_level_parts) if grade_level_parts else None
        interest_slugs = (
            [si.interest.slug for si in profile.interests if si.interest]
            if profile else []
        )

        cls_result = await self._db.execute(
            select(Classroom)
            .options(load_only(Classroom.id, Classroom.name, Classroom.code))
            .join(ClassroomStudent, Classroom.id == ClassroomStudent.classroom_id)
            .where(
                ClassroomStudent.student_id == user_id,
                ClassroomStudent.is_blocked == False,  # noqa: E712
            )
            .limit(1)
        )
        classroom = cls_result.scalar_one_or_none()

        user_nm = (user.name or "").strip()
        prof_nm = (profile.name or "").strip() if profile else ""
        # ``users.name`` is canonical; fall back to profile if rows ever diverged.
        resolved_name = user_nm or prof_nm

        return MeResponse(
            user_id=str(user.id),
            email=user.email,
            role=user.role,
            name=resolved_name,
            grade_level=grade_level,
            grade=grade_name,
            course=course_name,
            interests=interest_slugs,
            classroom_id=str(classroom.id) if classroom else None,
            classroom_name=classroom.name if classroom else None,
            classroom_code=classroom.code if classroom else None,
            district=user.district,
            school=user.school,
        )
