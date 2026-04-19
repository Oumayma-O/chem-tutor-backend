"""Repository for classrooms and classroom-student membership."""

import secrets
import string
import uuid
from typing import Sequence

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import Classroom, ClassroomStudent
from app.infrastructure.database.repositories.base import BaseRepository


def _generate_code(length: int = 6) -> str:
    """Generate a random alphanumeric join code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


class ClassroomRepository(BaseRepository[Classroom]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Classroom, session)

    async def create_with_code(self, classroom: Classroom) -> Classroom:
        """Create a classroom with a unique join code."""
        for _ in range(10):  # retry on collision
            code = _generate_code()
            existing = await self.get_by_code(code)
            if existing is None:
                classroom.code = code
                self._session.add(classroom)
                await self._session.flush()
                return classroom
        raise RuntimeError("Could not generate a unique classroom code after 10 attempts")

    async def get_by_code(self, code: str) -> Classroom | None:
        result = await self._session.execute(
            select(Classroom).where(Classroom.code == code.upper())
        )
        return result.scalar_one_or_none()

    async def get_active_by_teacher_and_name(
        self, teacher_id: uuid.UUID, name: str
    ) -> Classroom | None:
        result = await self._session.execute(
            select(Classroom).where(
                Classroom.teacher_id == teacher_id,
                Classroom.is_active == True,  # noqa: E712
                Classroom.name.ilike(name),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_teacher(self, teacher_id: uuid.UUID) -> Sequence[Classroom]:
        result = await self._session.execute(
            select(Classroom)
            .where(Classroom.teacher_id == teacher_id, Classroom.is_active == True)  # noqa: E712
            .options(selectinload(Classroom.students))
            .order_by(Classroom.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_id_with_students(self, classroom_id: uuid.UUID) -> Classroom | None:
        result = await self._session.execute(
            select(Classroom)
            .where(Classroom.id == classroom_id)
            .options(selectinload(Classroom.students))
        )
        return result.scalar_one_or_none()

    async def get_student_classrooms(self, student_id: uuid.UUID) -> Sequence[Classroom]:
        """All classrooms a student is enrolled in."""
        result = await self._session.execute(
            select(Classroom)
            .join(ClassroomStudent, ClassroomStudent.classroom_id == Classroom.id)
            .where(ClassroomStudent.student_id == student_id, Classroom.is_active == True)  # noqa: E712
            .order_by(Classroom.created_at.desc())
        )
        return result.scalars().all()


class ClassroomStudentRepository(BaseRepository[ClassroomStudent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ClassroomStudent, session)

    async def get_membership(
        self, classroom_id: uuid.UUID, student_id: uuid.UUID
    ) -> ClassroomStudent | None:
        result = await self._session.execute(
            select(ClassroomStudent).where(
                ClassroomStudent.classroom_id == classroom_id,
                ClassroomStudent.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def is_enrolled(self, classroom_id: uuid.UUID, student_id: uuid.UUID) -> bool:
        return await self.get_membership(classroom_id, student_id) is not None

    async def enroll(self, classroom_id: uuid.UUID, student_id: uuid.UUID) -> ClassroomStudent:
        # Check if student was previously enrolled (possibly blocked)
        result = await self._session.execute(
            select(ClassroomStudent).where(
                ClassroomStudent.classroom_id == classroom_id,
                ClassroomStudent.student_id == student_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            if existing.is_blocked:
                raise PermissionError("You have been blocked from this classroom.")
            return existing

        membership = ClassroomStudent(classroom_id=classroom_id, student_id=student_id)
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def set_blocked(
        self, classroom_id: uuid.UUID, student_id: uuid.UUID, blocked: bool,
    ) -> bool:
        """Set or clear the blocked flag. Returns True if the row was found."""
        result = await self._session.execute(
            select(ClassroomStudent).where(
                ClassroomStudent.classroom_id == classroom_id,
                ClassroomStudent.student_id == student_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        row.is_blocked = blocked
        await self._session.flush()
        return True

    async def get_class_students(self, classroom_id: uuid.UUID) -> Sequence[ClassroomStudent]:
        result = await self._session.execute(
            select(ClassroomStudent)
            .where(ClassroomStudent.classroom_id == classroom_id)
            .order_by(ClassroomStudent.joined_at)
        )
        return result.scalars().all()

    async def remove_membership(self, classroom_id: uuid.UUID, student_id: uuid.UUID) -> bool:
        """Remove a student from a classroom. Returns True if a row was deleted."""
        result = await self._session.execute(
            delete(ClassroomStudent).where(
                ClassroomStudent.classroom_id == classroom_id,
                ClassroomStudent.student_id == student_id,
            )
        )
        return (result.rowcount or 0) > 0
