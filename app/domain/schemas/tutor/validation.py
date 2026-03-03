"""Answer validation schemas."""

from pydantic import BaseModel


class ValidateAnswerRequest(BaseModel):
    student_answer: str
    correct_answer: str
    step_label: str
    step_type: str | None = None
    problem_context: str | None = None


class ValidationOutput(BaseModel):
    is_correct: bool
    feedback: str | None = None
    student_value: str | None = None
    correct_value: str | None = None
    unit_correct: bool | None = None
    validation_method: str | None = None
