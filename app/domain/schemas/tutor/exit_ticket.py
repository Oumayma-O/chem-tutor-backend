"""Exit ticket schemas — tutor output types and LLM generation bundles."""

from typing import Literal
from pydantic import BaseModel, Field


class ExitTicketQuestion(BaseModel):
    id: str
    question: str
    type: Literal["mcq", "short_answer"] = "mcq"
    correct_answer: str
    explanation: str | None = None
    unit: str | None = None


class GenerateExitTicketRequest(BaseModel):
    unit_id: str
    lesson_name: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    format: Literal["mcq", "short_answer", "mixed"] = "mcq"
    question_count: int = Field(default=3, ge=1, le=10)
    lesson_context: dict | None = None  # equations, objectives, key_rules, misconceptions (same as problem generation)


class ExitTicketOutput(BaseModel):
    questions: list[ExitTicketQuestion] = Field(min_length=1)


# ── LLM generation bundle (teacher topic-based flow) ─────────

from app.domain.schemas.tutor.problems import MCQOption  # noqa: E402 — shared across practice + exit tickets


class ExitTicketQuestionLLM(BaseModel):
    """Raw LLM output shape for a single teacher exit ticket question."""
    id: str = ""
    prompt: str
    question_type: str = "short_answer"
    # MCQ: list of MCQOption objects (each carries text + is_correct + misconception_tag).
    # Numeric/short-answer: leave empty.
    mcq_options: list[MCQOption] = Field(default_factory=list)
    # For numeric questions: the expected physical unit (e.g. 'g', 'mol/L', 'kJ/mol').
    unit: str | None = None
    correct_answer: str | None = None
    points: float = 1.0


class ExitTicketGenerationBundle(BaseModel):
    questions: list[ExitTicketQuestionLLM]
