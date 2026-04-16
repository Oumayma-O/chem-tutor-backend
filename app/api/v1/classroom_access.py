"""HTTP-facing helpers for classroom authorization (teacher / student)."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, require_teacher_or_admin
from app.infrastructure.database.models import Classroom, ClassroomStudent, User
from app.services.classroom.access import require_classroom_owned_by_teacher


def _admin_may_access_classroom(actor: User, classroom_teacher: User) -> bool:
    """School admin access check.

    - Admin with no school/district configured → unrestricted (platform-level admin,
      includes all dev/testing accounts with blank org fields).
    - Admin with school/district set → must match the classroom owner's org exactly.
    """
    asch = (actor.school or "").strip()
    ad = (actor.district or "").strip()
    if not asch and not ad:
        return True  # no org restriction configured — treat as platform-wide admin
    td = (classroom_teacher.district or "").strip()
    tsch = (classroom_teacher.school or "").strip()
    return ad == td and asch == tsch


async def ensure_teacher_classroom(
    db: AsyncSession,
    auth: AuthContext,
    class_id: uuid.UUID,
):
    """
    Require a teacher/admin JWT and verify classroom access.

    - Teachers: classroom.teacher_id must equal the JWT subject.
    - School admins: classroom owner's district/school must match the admin's.
    - Superadmins: unrestricted (platform operations).
    """
    require_teacher_or_admin(auth)
    classroom = await db.scalar(select(Classroom).where(Classroom.id == class_id))
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")

    if auth.role == "teacher":
        if classroom.teacher_id != auth.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class.")
        return classroom

    if auth.role == "superadmin":
        return classroom

    actor = await db.scalar(select(User).where(User.id == auth.user_id))
    owner = await db.scalar(select(User).where(User.id == classroom.teacher_id))
    if actor is None or owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")

    if not _admin_may_access_classroom(actor, owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your organization's classroom.",
        )
    return classroom


async def ensure_student_enrolled(
    db: AsyncSession,
    student_id: uuid.UUID,
    class_id: uuid.UUID,
) -> None:
    """Raise 404 if the student is not enrolled in the class."""
    r = await db.scalar(
        select(ClassroomStudent.classroom_id).where(
            ClassroomStudent.student_id == student_id,
            ClassroomStudent.classroom_id == class_id,
        )
    )
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled in this class.")
