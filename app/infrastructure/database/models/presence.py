"""Live session presence via heartbeat polling."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.connection import Base
from app.infrastructure.database.models._helpers import _now


class PresenceHeartbeat(Base):
    """
    Last-known activity for a student within a classroom.
    Upserted on each POST /presence/heartbeat (typically every ~30s).
    """

    __tablename__ = "presence_heartbeats"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    step_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        Index("ix_presence_classroom_seen", "classroom_id", "last_seen_at"),
    )
