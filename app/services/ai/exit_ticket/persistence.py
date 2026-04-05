"""Exit ticket persistence and listing (PostgreSQL)."""

import uuid
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ExitTicket
from app.infrastructure.database.repositories.exit_ticket_repo import ExitTicketRepository


class ExitTicketPersistenceService:
    """Storage and retrieval for teacher exit ticket sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ExitTicketRepository(session)

    async def create_ticket(
        self,
        *,
        class_id: uuid.UUID,
        teacher_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        difficulty: str,
        time_limit_minutes: int,
        questions: list[dict],
        is_active: bool = True,
    ) -> ExitTicket:
        row = ExitTicket(
            class_id=class_id,
            teacher_id=teacher_id,
            unit_id=unit_id,
            lesson_index=lesson_index,
            difficulty=difficulty,
            time_limit_minutes=time_limit_minutes,
            is_active=is_active,
            questions=questions,
        )
        return await self._repo.create(row)

    async def list_for_class(self, class_id: uuid.UUID) -> Sequence[ExitTicket]:
        return await self._repo.list_for_class(class_id)
