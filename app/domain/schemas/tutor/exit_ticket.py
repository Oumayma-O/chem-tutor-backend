"""Exit ticket schemas."""

from typing import Literal
from pydantic import BaseModel, Field


class QCMOption(BaseModel):
    id: str
    text: str


class ExitTicketQuestion(BaseModel):
    id: str
    question: str
    type: Literal["mcq", "short_answer"] = "mcq"
    options: list[QCMOption] | None = None
    correct_answer: str
    explanation: str | None = None


class GenerateExitTicketRequest(BaseModel):
    unit_id: str
    topic_name: str
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    format: Literal["mcq", "short_answer", "mixed"] = "mcq"
    question_count: int = Field(default=3, ge=1, le=10)


class ExitTicketOutput(BaseModel):
    questions: list[ExitTicketQuestion] = Field(min_length=1)
