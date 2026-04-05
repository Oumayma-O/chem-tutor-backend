"""Exit ticket sessions and student responses."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import ExitTicket, ExitTicketResponse


class ExitTicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, row: ExitTicket) -> ExitTicket:
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_for_class(self, class_id: uuid.UUID) -> Sequence[ExitTicket]:
        result = await self._session.execute(
            select(ExitTicket)
            .where(ExitTicket.class_id == class_id)
            .options(selectinload(ExitTicket.responses))
            .order_by(ExitTicket.created_at.desc())
        )
        return result.scalars().all()

    async def get(self, ticket_id: uuid.UUID) -> ExitTicket | None:
        result = await self._session.execute(
            select(ExitTicket)
            .where(ExitTicket.id == ticket_id)
            .options(selectinload(ExitTicket.responses))
        )
        return result.scalar_one_or_none()


class FewShotCuratedRepository:
    """Admin view of curated few-shot examples."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_page(self, limit: int = 50, offset: int = 0):
        from app.infrastructure.database.models import FewShotExample

        result = await self._session.execute(
            select(FewShotExample)
            .order_by(FewShotExample.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
