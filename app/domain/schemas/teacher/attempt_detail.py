"""Schemas for the attempt detail endpoint (teacher drill-down view)."""

import uuid

from pydantic import BaseModel


class AttemptStepDetail(BaseModel):
    """Per-step diagnostic data for a single problem attempt."""

    step_label: str
    instruction: str
    correct_answer: str | None
    attempts: int
    hints_used: int
    was_revealed: bool
    is_correct: bool
    first_attempt_correct: bool
    time_spent_seconds: float | None


class AttemptDetailOut(BaseModel):
    """Full attempt detail response returned to the teacher dashboard."""

    attempt_id: uuid.UUID
    problem_statement: str | None
    title: str | None
    steps: list[AttemptStepDetail]
    overall_score: float | None
    level: int
    difficulty: str
