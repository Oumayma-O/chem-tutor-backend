"""Error classification schemas — thinking tracker + misconception tagging."""

from typing import Literal
from pydantic import BaseModel, model_validator


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
    category: str | None = None
    subcategory: str | None = None
    description: str | None = None
    concept_missing: str | None = None
    suggested_intervention: str | None = None
    misconception_tag: str | None = None
    severity: Literal["blocking", "slowing", "minor"] | None = None

    @model_validator(mode="after")
    def populate_compat_fields(self) -> "StepError":
        """Expose compatibility keys expected by older/newer clients."""
        if self.category is None:
            self.category = self.error_category
        if self.subcategory is None:
            self.subcategory = self.error_subcategory
        return self


class ClassifyErrorsRequest(BaseModel):
    steps: list[ThinkingEntry]
    problem_context: str
    all_steps: list[dict]


class ErrorClassificationOutput(BaseModel):
    errors: list[StepError]
    insight: str
    safety_flag: bool = False
