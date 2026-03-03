"""Class insights schemas."""

from pydantic import BaseModel


class GenerateInsightsRequest(BaseModel):
    student_count: int
    class_mastery: float
    error_frequencies: dict[str, int]
    misconception_data: list[dict]


class ClassInsightsOutput(BaseModel):
    insights: list[str]
