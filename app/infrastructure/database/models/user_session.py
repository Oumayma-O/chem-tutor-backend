"""User session activity model — daily login & time-on-platform tracking."""

import uuid
from datetime import date

from sqlalchemy import Date, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.connection import Base
from app.infrastructure.database.models._helpers import _uuid


class UserSessionActivity(Base):
    """One row per (user, calendar day). Accumulates via heartbeat upserts.

    The frontend calls ``POST /auth/heartbeat`` every 60 seconds while the
    app is open.  Each call increments ``total_minutes_active`` by 1.  A new
    row for today means a new login, so ``login_count`` starts at 1 and is
    never updated after the initial INSERT.
    """
    __tablename__ = "user_session_activity"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_minutes_active: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", "session_date", name="uq_user_session_date"),
        Index("ix_user_session_user_date", "user_id", "session_date"),
    )
