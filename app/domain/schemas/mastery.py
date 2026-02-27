import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class StartAttemptRequest(BaseModel):
    user_id: uuid.UUID
    class_id: uuid.UUID | None = None
    chapter_id: str
    topic_index: int
    problem_id: str
    difficulty: str = "medium"
    level: int = Field(default=2, ge=1, le=3)


class StartAttemptResponse(BaseModel):
    attempt_id: uuid.UUID


class CompleteAttemptRequest(BaseModel):
    attempt_id: uuid.UUID
    user_id: uuid.UUID
    chapter_id: str
    topic_index: int
    score: float = Field(ge=0.0, le=1.0)
    step_log: list[dict]
    level: int = Field(default=2, ge=1, le=3)


class CategoryScores(BaseModel):
    """Per-dimension mastery breakdown shown in the Mastery Score panel."""
    conceptual: float = 0.5
    procedural: float = 0.5
    computational: float = 0.5
    representation: float = 0.5


class MasteryState(BaseModel):
    user_id: uuid.UUID
    chapter_id: str
    topic_index: int
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
    should_advance: bool         # True if ready to move to next topic
    recommended_difficulty: str


class ProgressionDecision(BaseModel):
    """Returned to the frontend after a completed attempt."""
    mastery: MasteryState
    attempt_score: float
    should_advance: bool
    level3_just_unlocked: bool   # True only on the attempt that first crossed the threshold
    recommended_next_difficulty: str
    feedback_message: str
