import uuid
from pydantic import BaseModel, Field


class StudentMasterySummary(BaseModel):
    student_id: uuid.UUID
    mastery_score: float
    attempts_count: int
    error_counts: dict[str, int]
    top_misconceptions: list[str]
    is_at_risk: bool


class TopicBreakdown(BaseModel):
    topic_index: int
    avg_mastery: float
    student_count: int
    completion_rate: float


class ClassAnalyticsResponse(BaseModel):
    class_id: uuid.UUID
    chapter_id: str
    student_count: int
    avg_mastery: float
    at_risk_count: int
    error_frequency: dict[str, int]      # {category: total_count}
    top_misconceptions: list[str]        # Top 5 misconception_tags
    topic_breakdown: list[TopicBreakdown]
    students: list[StudentMasterySummary]
    ai_insights: list[str]               # From generate-class-insights


class ClassAnalyticsRequest(BaseModel):
    class_id: uuid.UUID
    chapter_id: str
    topic_index: int | None = None
    include_ai_insights: bool = True
