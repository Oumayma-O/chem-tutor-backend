"""Answer validation schemas."""

from pydantic import AliasChoices, BaseModel, Field, field_validator


class ValidateAnswerRequest(BaseModel):
    student_answer: str
    correct_answer: str
    step_label: str
    step_type: str | None = None
    problem_context: str | None = None
    step_instruction: str | None = None


class ValidationOutput(BaseModel):
    is_correct: bool
    feedback: str | None = None
    student_value: str | None = None
    correct_value: str | None = None
    unit_correct: bool | None = None
    validation_method: str | None = None
    processing_s: float | None = None  # LLM call duration in seconds (None = resolved locally)


class LlmEquivalenceJudgment(BaseModel):
    """Structured LLM output for Phase 2 (equivalence + short diagnostic feedback)."""

    is_actually_correct: bool
    feedback: str | None = Field(
        default=None,
        validation_alias=AliasChoices("feedback", "hint"),
    )

    @field_validator("feedback", mode="before")
    @classmethod
    def _cap_feedback_words(cls, v: str | None) -> str | None:
        if v is None:
            return None
        t = str(v).strip()
        if not t:
            return None
        words = t.split()
        if len(words) <= 20:
            return t
        return " ".join(words[:20])
