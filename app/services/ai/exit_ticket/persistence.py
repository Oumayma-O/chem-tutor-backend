"""Exit ticket persistence and listing (PostgreSQL)."""

import uuid
from datetime import datetime
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
        lesson_id: str | None = None,
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
            lesson_id=lesson_id,
            difficulty=difficulty,
            time_limit_minutes=time_limit_minutes,
            is_active=is_active,
            questions=questions,
        )
        return await self._repo.create(row)

    async def mark_published(self, ticket_id: uuid.UUID) -> ExitTicket | None:
        return await self._repo.mark_published(ticket_id)

    async def list_for_class(
        self,
        class_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[ExitTicket]:
        return await self._repo.list_for_class(class_id, page=page, limit=limit)

    async def list_all_published_for_class(
        self,
        class_id: uuid.UUID,
        *,
        unit_id: str | None = None,
        lesson_id: str | None = None,
        since: datetime | None = None,
    ) -> Sequence[ExitTicket]:
        return await self._repo.list_all_published_for_class(
            class_id, unit_id=unit_id, lesson_id=lesson_id, since=since
        )

    async def count_published_for_class(self, class_id: uuid.UUID) -> int:
        return await self._repo.count_published_for_class(class_id)
