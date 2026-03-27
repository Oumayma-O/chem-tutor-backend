"""Hint generation schemas."""

from pydantic import BaseModel, Field


class GenerateHintRequest(BaseModel):
    step_id: str
    step_label: str
    step_instruction: str
    step_explanation: str | None = None
    student_input: str | None = None
    correct_answer: str
    attempt_count: int = Field(default=1, ge=1)
    problem_context: str | None = None
    interests: list[str] = Field(default_factory=list)
    grade_level: str | None = None
    # Structured pedagogy: replaces full lesson_context for hint generation
    key_rule: str | None = None  # the single rule/formula most relevant to this step
    error_category: str | None = None
    misconception_tag: str | None = None  # optional; included only when high-confidence
    validation_feedback: str | None = None  # from validate-step; strongly recommended to avoid a second validation pass
    # Step progress — when set, hints stay scoped to THIS step (no repeating full theory from step 1)
    step_number: int | None = Field(default=None, ge=1)
    total_steps: int | None = Field(default=None, ge=1)
    step_type: str | None = None
    prior_steps_summary: str | None = None  # short text: what earlier steps already covered


class HintOutput(BaseModel):
    hint: str
    hint_level: int = Field(default=1, ge=1, le=3)
