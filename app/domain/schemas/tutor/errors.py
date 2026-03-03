"""Error classification schemas — thinking tracker + misconception tagging."""

from typing import Literal
from pydantic import BaseModel


class ThinkingEntry(BaseModel):
    """One recorded step from the student's thinking session."""
    step_id: str
    step_label: str
    student_input: str
    is_correct: bool
    time_spent_seconds: int = 0
    attempt_count: int = 1


class StepError(BaseModel):
    """Classified error for one incorrect step."""
    step_id: str
    step_label: str
    error_category: str        # "conceptual" | "procedural" | "computational" | "units"
    error_subcategory: str | None = None
    misconception_tag: str | None = None
    severity: Literal["blocking", "slowing", "minor"] | None = None


class ClassifyErrorsRequest(BaseModel):
    steps: list[ThinkingEntry]
    problem_context: str
    all_steps: list[dict]


class ErrorClassificationOutput(BaseModel):
    errors: list[StepError]
    insight: str
    safety_flag: bool = False
