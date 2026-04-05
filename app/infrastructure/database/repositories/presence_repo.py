"""Presence heartbeat upsert and live queries."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import PresenceHeartbeat


class PresenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_heartbeat(
        self,
        user_id: uuid.UUID,
        classroom_id: uuid.UUID,
        step_id: str | None,
    ) -> PresenceHeartbeat:
        now = datetime.now(timezone.utc)
        stmt = (
            insert(PresenceHeartbeat)
            .values(
                user_id=user_id,
                classroom_id=classroom_id,
                step_id=step_id,
                last_seen_at=now,
            )
            .on_conflict_do_update(
                index_elements=["user_id", "classroom_id"],
                set_={"step_id": step_id, "last_seen_at": now},
            )
            .returning(PresenceHeartbeat)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def list_active_in_classroom(
        self,
        classroom_id: uuid.UUID,
        within_seconds: int = 60,
    ) -> list[PresenceHeartbeat]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=within_seconds)
        result = await self._session.execute(
            select(PresenceHeartbeat).where(
                PresenceHeartbeat.classroom_id == classroom_id,
                PresenceHeartbeat.last_seen_at >= cutoff,
            )
        )
        return list(result.scalars().all())

    async def clear_for_user_classroom(self, user_id: uuid.UUID, classroom_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(PresenceHeartbeat).where(
                PresenceHeartbeat.user_id == user_id,
                PresenceHeartbeat.classroom_id == classroom_id,
            )
        )
