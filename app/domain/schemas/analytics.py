import uuid
from pydantic import BaseModel, Field


# ── Standards mastery schemas ─────────────────────────────────────────────────

class StudentStandardScore(BaseModel):
    """One student's average mastery across all lessons that map to a standard."""
    student_id: uuid.UUID
    mastery_score: float


class StandardMasteryItem(BaseModel):
    """Aggregated mastery for a single standard across the class."""
    standard_code: str
    standard_title: str | None
    framework: str
    class_avg: float
    at_risk_count: int
    student_scores: list[StudentStandardScore]


class ClassStandardsMasteryResponse(BaseModel):
    class_id: uuid.UUID
    unit_id: str | None
    standards: list[StandardMasteryItem]


class StudentStandardMasteryItem(BaseModel):
    """One standard's mastery from a student's own perspective."""
    standard_code: str
    standard_title: str | None
    framework: str
    mastery_score: float
    lesson_count: int
    is_mastered: bool


class StudentStandardsMasteryResponse(BaseModel):
    student_id: uuid.UUID
    standards: list[StudentStandardMasteryItem]


# ── Existing class analytics schemas ─────────────────────────────────────────

class StudentMasterySummary(BaseModel):
    student_id: uuid.UUID
    mastery_score: float
    attempts_count: int
    error_counts: dict[str, int]
    top_misconceptions: list[str]
    is_at_risk: bool


class LessonBreakdown(BaseModel):
    lesson_index: int
    avg_mastery: float
    student_count: int
    completion_rate: float


class ClassAnalyticsResponse(BaseModel):
    class_id: uuid.UUID
    unit_id: str
    student_count: int
    avg_mastery: float
    at_risk_count: int
    error_frequency: dict[str, int]      # {category: total_count}
    top_misconceptions: list[str]        # Top 5 misconception_tags
    lesson_breakdown: list[LessonBreakdown] = Field(validation_alias="topic_breakdown")
    students: list[StudentMasterySummary]
    ai_insights: list[str]               # From generate-class-insights


class ClassAnalyticsRequest(BaseModel):
    class_id: uuid.UUID
    unit_id: str
    lesson_index: int | None = None
    include_ai_insights: bool = True
