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
    # When phase is exit_ticket (no timed practice): quiz window for teacher countdown UI.
    exit_ticket_time_limit_minutes: int | None = None
    exit_ticket_window_started_at: str | None = None
    allow_answer_reveal: bool = True
    max_answer_reveals_per_lesson: int = Field(
        default=6,
        ge=1,
        description="Cap on 3-strikes answer reveals per lesson for this class.",
    )
    min_level1_examples_for_level2: int = Field(
        default=2,
        ge=1,
        description="Unique Level 1 worked examples required before Level 2 is available.",
    )
