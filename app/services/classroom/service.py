"""Classroom service — create, join, list, remove."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.classrooms import (
    ClassroomListItem,
    ClassroomOut,
    ClassroomStudentOut,
    JoinClassroomResponse,
)
from app.infrastructure.database.models import Classroom, User
from app.infrastructure.database.repositories.classroom_repo import (
    ClassroomRepository,
    ClassroomStudentRepository,
)

logger = get_logger(__name__)


def _to_classroom_out(classroom: Classroom, student_count: int) -> ClassroomOut:
    return ClassroomOut(
        id=classroom.id,
        name=classroom.name,
        teacher_id=classroom.teacher_id,
        unit_id=classroom.unit_id,
        code=classroom.code,
        is_active=classroom.is_active,
        student_count=student_count,
        created_at=classroom.created_at,
    )


class ClassroomService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ClassroomRepository(session)
        self._students = ClassroomStudentRepository(session)

    async def create(
        self,
        name: str,
        teacher_id: uuid.UUID,
        unit_id: str | None,
    ) -> ClassroomOut:
        classroom = Classroom(name=name, teacher_id=teacher_id, unit_id=unit_id, code="")
        created = await self._repo.create_with_code(classroom)
        logger.info("classroom_created", classroom=str(created.id), teacher=str(teacher_id))
        return _to_classroom_out(created, student_count=0)

    async def get(self, classroom_id: uuid.UUID) -> ClassroomOut | None:
        classroom = await self._repo.get_by_id_with_students(classroom_id)
        if classroom is None:
            return None
        return _to_classroom_out(classroom, student_count=len(classroom.students))

    async def list_for_teacher(self, teacher_id: uuid.UUID) -> list[ClassroomListItem]:
        classrooms = await self._repo.get_by_teacher(teacher_id)
        return [
            ClassroomListItem(
                id=c.id,
                name=c.name,
                code=c.code,
                unit_id=c.unit_id,
                student_count=len(c.students),
                is_active=c.is_active,
            )
            for c in classrooms
        ]

    async def join(self, code: str, student_id: uuid.UUID) -> JoinClassroomResponse:
        classroom = await self._repo.get_by_code(code)
        if classroom is None or not classroom.is_active:
            raise LookupError("No active classroom found with that code.")
        await self._students.enroll(classroom.id, student_id)

        # Inherit district/school from the teacher who owns the classroom.
        teacher = await self._session.scalar(
            select(User).where(User.id == classroom.teacher_id)
        )
        if teacher:
            student = await self._session.scalar(
                select(User).where(User.id == student_id)
            )
            if student:
                student.district = teacher.district
                student.school = teacher.school

        logger.info("student_joined_classroom", student=str(student_id), classroom=str(classroom.id))
        return JoinClassroomResponse(
            classroom_id=classroom.id,
            classroom_name=classroom.name,
            unit_id=classroom.unit_id,
        )

    async def list_for_student(self, student_id: uuid.UUID) -> list[ClassroomListItem]:
        classrooms = await self._repo.get_student_classrooms(student_id)
        return [
            ClassroomListItem(
                id=c.id,
                name=c.name,
                code=c.code,
                unit_id=c.unit_id,
                student_count=0,
                is_active=c.is_active,
            )
            for c in classrooms
        ]

    async def is_enrolled(self, classroom_id: uuid.UUID, student_id: uuid.UUID) -> bool:
        return await self._students.is_enrolled(classroom_id, student_id)

    async def remove_student(
        self, classroom_id: uuid.UUID, student_id: uuid.UUID
    ) -> None:
        """Raises LookupError if student is not enrolled."""
        removed = await self._students.remove_membership(classroom_id, student_id)
        if not removed:
            raise LookupError("Student not enrolled in this classroom.")
        await self._session.commit()

    async def list_students(self, classroom_id: uuid.UUID) -> list[ClassroomStudentOut]:
        members = await self._students.get_class_students(classroom_id)
        return [
            ClassroomStudentOut(student_id=m.student_id, joined_at=m.joined_at)
            for m in members
        ]

    async def delete(self, classroom_id: uuid.UUID, teacher_id: uuid.UUID) -> None:
        """Soft-delete: set is_active=False. Raises LookupError / PermissionError."""
        classroom = await self._repo.get_by_id_with_students(classroom_id)
        if classroom is None:
            raise LookupError("Classroom not found.")
        if classroom.teacher_id != teacher_id:
            raise PermissionError("Not your classroom.")
        classroom.is_active = False
        await self._session.commit()
        logger.info("classroom_deleted", classroom=str(classroom_id), teacher=str(teacher_id))

    async def get_raw(self, classroom_id: uuid.UUID):
        """Return raw ORM model (with students loaded) for ownership checks."""
        return await self._repo.get_by_id_with_students(classroom_id)
