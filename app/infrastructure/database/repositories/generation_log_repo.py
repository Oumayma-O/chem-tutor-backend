"""Read-only access to generation_logs for admin auditing."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import GenerationLog, User


class GenerationLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_recent(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        unit_id: str | None = None,
    ) -> list[GenerationLog]:
        q = select(GenerationLog).order_by(GenerationLog.created_at.desc())
        if unit_id:
            q = q.where(GenerationLog.unit_id == unit_id)
        q = q.offset(offset).limit(limit)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def count_total(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(GenerationLog))
        return int(result.scalar_one())

    async def count_since(self, since: datetime) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(GenerationLog)
            .where(GenerationLog.created_at >= since)
        )
        return int(result.scalar_one())


class UserStatsRepository:
    """Lightweight aggregates for SystemStats."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_by_roles(self) -> dict[str, int]:
        result = await self._session.execute(
            select(User.role, func.count())
            .group_by(User.role)
        )
        rows = result.all()
        out: dict[str, int] = {"student": 0, "teacher": 0, "admin": 0}
        for role, n in rows:
            if role in out:
                out[role] = int(n)
        total_result = await self._session.execute(select(func.count()).select_from(User))
        out["total"] = int(total_result.scalar_one())
        return out
