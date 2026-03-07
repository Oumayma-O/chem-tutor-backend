import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class StartAttemptRequest(BaseModel):
    user_id: uuid.UUID
    class_id: uuid.UUID | None = None
    unit_id: str
    lesson_index: int
    problem_id: str
    difficulty: str = "medium"
    level: int = Field(default=2, ge=1, le=3)


class StartAttemptResponse(BaseModel):
    attempt_id: uuid.UUID


class CompleteAttemptRequest(BaseModel):
    attempt_id: uuid.UUID
    user_id: uuid.UUID
    unit_id: str
    lesson_index: int
    score: float = Field(ge=0.0, le=1.0)
    step_log: list[dict]
    level: int = Field(default=2, ge=1, le=3)


class CategoryScores(BaseModel):
    """Per-dimension mastery breakdown shown in the Mastery Score panel."""
    conceptual: float = 0.0
    procedural: float = 0.0
    computational: float = 0.0
    representation: float = 0.0


class MasteryState(BaseModel):
    user_id: uuid.UUID
    unit_id: str
    lesson_index: int
    mastery_score: float
    attempts_count: int
    consecutive_correct: int
    current_difficulty: str
    error_counts: dict[str, int]
    recent_scores: list[float]
    category_scores: CategoryScores
    updated_at: datetime

    # Derived fields
    has_mastered: bool           # True if mastery_score >= threshold
    level3_unlocked: bool        # Permanently True once unlocked — never reverts
    level3_unlocked_at: datetime | None
    should_advance: bool         # True if ready to move to next lesson
    recommended_difficulty: str


class ProgressionDecision(BaseModel):
    """Returned to the frontend after a completed attempt."""
    mastery: MasteryState
    attempt_score: float
    should_advance: bool
    level3_just_unlocked: bool   # True only on the attempt that first crossed the threshold
    recommended_next_difficulty: str
    feedback_message: str


# ── Lesson Progress ────────────────────────────────────────────

class LessonProgressOut(BaseModel):
    lesson_index: int
    status: Literal["not-started", "in-progress", "completed"]


# Backward-compat alias
TopicProgressOut = LessonProgressOut


class SetTopicStatusRequest(BaseModel):
    status: Literal["not-started", "in-progress", "completed"]


class UnlockLevel3Response(BaseModel):
    level3_unlocked: bool


# ── Mid-problem progress (resume after logout) ────────────────

class SaveStepRequest(BaseModel):
    """Checkpoint: persist the current step_log for an in-progress attempt."""
    attempt_id: uuid.UUID
    step_log: list[dict]


class SaveStepResponse(BaseModel):
    """Live mastery snapshot computed from in-progress step work."""
    mastery: MasteryState
    attempt_score: float
    attempted_steps: int


class ResumeAttemptResponse(BaseModel):
    """
    Returned when the student logs back in mid-problem.
    The frontend uses problem_id to look up the problem in the user's playlist
    and step_log to restore completed steps.
    """
    attempt_id: uuid.UUID
    problem_id: str
    level: int
    step_log: list[dict]        # steps already completed (in order)
