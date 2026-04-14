"""Exit ticket sessions and student responses."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Sequence

from sqlalchemy import func, select
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

    async def mark_published(self, ticket_id: uuid.UUID) -> ExitTicket | None:
        """Stamp published_at on a draft ticket. Idempotent — skips if already published."""
        row = await self.get(ticket_id)
        if row is not None and row.published_at is None:
            row.published_at = datetime.now(timezone.utc)
            await self._session.flush()
        return row

    async def count_published_for_class(self, class_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(ExitTicket)
            .where(ExitTicket.class_id == class_id, ExitTicket.published_at.is_not(None))
        )
        return result.scalar_one()

    async def list_for_class(
        self,
        class_id: uuid.UUID,
        *,
        page: int = 1,
        limit: int = 10,
    ) -> Sequence[ExitTicket]:
        """Return published tickets only, newest-first, with optional pagination."""
        offset = (page - 1) * limit
        result = await self._session.execute(
            select(ExitTicket)
            .where(ExitTicket.class_id == class_id, ExitTicket.published_at.is_not(None))
            .options(selectinload(ExitTicket.responses))
            .order_by(ExitTicket.published_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def list_all_published_for_class(
        self,
        class_id: uuid.UUID,
        *,
        unit_id: str | None = None,
        lesson_id: str | None = None,
        since: datetime | None = None,
    ) -> Sequence[ExitTicket]:
        """All published tickets without pagination — used for analytics aggregation.

        Optional `unit_id` and `lesson_id` narrow the results to a specific curriculum scope.
        Optional `since` filters to tickets published on or after that datetime.
        """
        stmt = (
            select(ExitTicket)
            .where(ExitTicket.class_id == class_id, ExitTicket.published_at.is_not(None))
            .options(selectinload(ExitTicket.responses))
            .order_by(ExitTicket.published_at.desc())
        )
        if unit_id:
            stmt = stmt.where(ExitTicket.unit_id == unit_id)
        if lesson_id:
            stmt = stmt.where(ExitTicket.lesson_id == lesson_id)
        if since:
            stmt = stmt.where(ExitTicket.published_at >= since)
        result = await self._session.execute(stmt)
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
