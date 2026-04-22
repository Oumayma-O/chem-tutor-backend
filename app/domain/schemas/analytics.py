import uuid
from typing import Literal

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
    standard_description: str | None = None
    framework: str
    class_avg: float
    at_risk_count: int
    student_scores: list[StudentStandardScore]


class ClassStandardsMasteryResponse(BaseModel):
    class_id: uuid.UUID
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


# ── Aggregate analytics schemas (district / school / class roll-up) ───────────

class AggregateGroupRow(BaseModel):
    name: str
    group_id: str | None = None  # classroom UUID at class level; None for district/school
    student_count: int
    class_count: int
    avg_mastery: float      # 0.0–1.0
    at_risk_count: int
    problems_solved: int
    hours_active: int       # whole hours


class UnitMasteryRow(BaseModel):
    unit_id: str
    unit_title: str | None
    avg_mastery: float      # 0.0–1.0
    student_count: int


class AggregateAnalyticsResponse(BaseModel):
    grouping: Literal["district", "school", "class"]
    groups: list[AggregateGroupRow]
    total_students: int
    total_classes: int
    total_problems_solved: int
    total_hours_active: int
    overall_avg_mastery: float  # weighted by student_count
    overall_at_risk_count: int
    weakest_units: list[UnitMasteryRow]  # bottom 8, sorted ASC by avg_mastery
    mastery_distribution: dict[str, int]  # "0-50","50-70","70-85","85-100" — student counts
