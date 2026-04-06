"""Classroom live session — teacher publish + student poll."""

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.schemas.dashboards import ExitTicketConfig


class LiveSessionPublishRequest(BaseModel):
    exit_ticket_id: uuid.UUID
    timed_practice_enabled: bool = False
    timed_practice_minutes: int | None = None
    unit_id: str
    lesson_index: int = Field(ge=0)


class LiveSessionDismissIn(BaseModel):
    """Student acknowledged closing timed / exit-ticket UI (analytics; optional future server state)."""

    anchor_key: str = Field(min_length=1, max_length=512)


class LiveSessionOut(BaseModel):
    """Matches frontend `MyClassroomLiveSession`."""

    classroom_id: uuid.UUID
    timed_mode_active: bool = False
    timed_practice_minutes: int | None = None
    timed_started_at: str | None = None
    active_exit_ticket_id: str | None = None
    session_phase: Literal["idle", "timed_practice", "exit_ticket"] = "idle"
    unit_id: str | None = None
    lesson_index: int | None = None
    exit_ticket: ExitTicketConfig | None = None
