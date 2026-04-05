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
        """Raises PermissionError if student is not enrolled in the classroom."""
        if not await self._students.is_enrolled(classroom_id, user_id):
            raise PermissionError("Not enrolled in this classroom.")
        await self._presence.upsert_heartbeat(user_id, classroom_id, step_id)
