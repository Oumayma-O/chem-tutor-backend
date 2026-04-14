"""Shared classroom access checks (no FastAPI imports)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Classroom, ClassroomStudent
from app.infrastructure.database.repositories.classroom_repo import ClassroomRepository


async def require_classroom_owned_by_teacher(
    db: AsyncSession,
    class_id: uuid.UUID,
    teacher_id: uuid.UUID,
) -> Classroom:
    """
    Return the classroom if it exists and is owned by ``teacher_id``.

    Raises:
        LookupError: classroom does not exist.
        PermissionError: classroom belongs to another teacher.
    """
    c_repo = ClassroomRepository(db)
    classroom = await c_repo.get_by_id_with_students(class_id)
    if classroom is None:
        raise LookupError("Classroom not found.")
    if classroom.teacher_id != teacher_id:
        raise PermissionError("Not your class.")
    return classroom
