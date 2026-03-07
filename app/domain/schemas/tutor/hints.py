"""Hint generation schemas."""

from pydantic import BaseModel, Field


class GenerateHintRequest(BaseModel):
    step_id: str
    step_label: str
    step_instruction: str
    student_input: str | None = None
    correct_answer: str
    attempt_count: int = Field(default=1, ge=1)
    problem_context: str | None = None
    interests: list[str] = Field(default_factory=list)
    grade_level: str | None = None
    lesson_context: dict | None = None  # equations, objectives, key_rules, misconceptions (same as problem generation)
    error_category: str | None = None
    misconception_tag: str | None = None


class HintOutput(BaseModel):
    hint: str
    hint_level: int = Field(default=1, ge=1, le=3)
