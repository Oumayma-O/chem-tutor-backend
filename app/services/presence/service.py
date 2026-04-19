"""Presence service — student heartbeat and enrollment check."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.classroom_repo import ClassroomStudentRepository
from app.infrastructure.database.repositories.presence_repo import PresenceRepository


class PresenceService:
    def __init__(self, session: AsyncSession) -> None:
        self._students = ClassroomStudentRepository(session)
        self._presence = PresenceRepository(session)

    async def record_heartbeat(
        self,
        user_id: uuid.UUID,
        classroom_id: uuid.UUID,
        step_id: str | None,
    ) -> None:
        """Raises PermissionError if student is not enrolled or is blocked."""
        row = await self._students.get_membership(classroom_id, user_id)
        if row is None:
            raise PermissionError("Not enrolled in this classroom.")
        if row.is_blocked:
            raise PermissionError("You have been blocked from this classroom.")
        await self._presence.upsert_heartbeat(user_id, classroom_id, step_id)
