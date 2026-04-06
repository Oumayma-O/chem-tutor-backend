"""
Pydantic models for Teacher / Admin dashboards and exit tickets.

Maps to PostgreSQL tables: exit_tickets, exit_ticket_responses, skill_mastery,
generation_logs, few_shot_examples, presence_heartbeats.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Exit tickets ──────────────────────────────────────────────


class ExitTicketQuestion(BaseModel):
    """One generated or stored exit-ticket question."""

    id: str = Field(description="Stable id within the ticket session")
    prompt: str
    question_type: str = Field(default="short_answer", description="mcq | short_answer | numeric")
    options: list[str] = Field(default_factory=list, description="For MCQ: option texts in order")
    option_misconception_tags: list[str | None] | None = Field(
        default=None,
        description="Index-aligned distractor tags for MCQ options. Null for the correct option.",
    )
    correct_answer: str | None = None
    points: float = 1.0
    unit: str | None = Field(default=None, description="Physical unit for numeric questions (e.g. 'g', 'kJ/mol')")


class ExitTicketConfig(BaseModel):
    """Exit ticket session metadata + questions (JSON in DB)."""

    id: uuid.UUID
    class_id: uuid.UUID
    teacher_id: uuid.UUID
    unit_id: str
    lesson_index: int = 0
    lesson_id: str | None = Field(default=None, description="Curriculum lesson slug (e.g. 'L-kinetics-zero-order')")
    difficulty: str = "medium"
    time_limit_minutes: int = 10
    is_active: bool = False
    questions: list[ExitTicketQuestion] = Field(default_factory=list)
    # None = draft; set = published timestamp
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ExitTicketResponseItem(BaseModel):
    """One student's submission (row in exit_ticket_responses)."""

    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str | None = None
    student_email: str | None = None
    answers: list[dict] = Field(default_factory=list)
    score: float | None = None
    submitted_at: datetime


class ExitTicketAnalytics(BaseModel):
    """Aggregated stats for a class's exit tickets."""

    class_id: uuid.UUID
    total_sessions: int = 0
    total_submissions: int = 0
    average_score: float | None = None
    last_activity_at: datetime | None = None


# ── Per-ticket misconception analytics ────────────────────────


class MisconceptionHit(BaseModel):
    tag: str
    count: int


class QuestionMisconceptionSummary(BaseModel):
    question_id: str
    prompt: str
    hits: list[MisconceptionHit]


class MisconceptionAnalytics(BaseModel):
    class_id: uuid.UUID
    ticket_id: uuid.UUID
    questions: list[QuestionMisconceptionSummary]


# ── Teacher dashboard ─────────────────────────────────────────


class CategorySnapshot(BaseModel):
    conceptual: float = 0.0
    procedural: float = 0.0
    computational: float = 0.0


class MasterySnapshot(BaseModel):
    """Per-student mastery for roster / class views."""

    overall_mastery: float = 0.0
    category_scores: CategorySnapshot = Field(default_factory=CategorySnapshot)
    lessons_with_data: int = 0


class RosterStudentEntry(BaseModel):
    student_id: uuid.UUID
    name: str
    email: str | None = None
    joined_at: datetime
    mastery: MasterySnapshot
    at_risk: bool = False


class ClassSummaryStats(BaseModel):
    """Aggregates for a teacher class card."""

    classroom_id: uuid.UUID
    avg_mastery: float = 0.0
    total_students: int = 0
    at_risk_count: int = 0
    category_breakdown: CategorySnapshot = Field(default_factory=CategorySnapshot)


class TeacherClassOut(BaseModel):
    """One row for GET /teacher/classes."""

    id: uuid.UUID
    name: str
    code: str
    unit_id: str | None
    student_count: int
    is_active: bool
    calculator_enabled: bool = True
    created_at: datetime
    stats: ClassSummaryStats
    # Snapshot of `classrooms.live_session` for Exit Tickets tab (timed practice + exit-only sessions).
    timed_mode_active: bool = False
    timed_practice_minutes: int | None = None
    timed_started_at: str | None = None
    active_exit_ticket_id: str | None = None
    session_phase: str | None = None
    exit_ticket_time_limit_minutes: int | None = None
    exit_ticket_window_started_at: str | None = None


class LiveStudentEntry(BaseModel):
    """Student visible on the Live panel (recent heartbeat)."""

    student_id: uuid.UUID
    name: str
    email: str | None = None
    step_id: str | None = None
    last_seen_at: datetime


# ── Admin ───────────────────────────────────────────────────


class SystemStats(BaseModel):
    total_users: int = 0
    students: int = 0
    teachers: int = 0
    admins: int = 0
    total_generation_logs: int = 0
    generations_last_24h: int = 0
    total_classrooms: int = 0


class AdminTeacherClassSummary(BaseModel):
    """One classroom row for admin teacher list."""

    id: uuid.UUID
    name: str
    class_code: str


class AdminTeacherOut(BaseModel):
    """Teacher account + classes for GET /admin/teachers."""

    user_id: uuid.UUID
    display_name: str
    email: str
    grade_level: str | None = None
    created_at: datetime
    classes: list[AdminTeacherClassSummary] = Field(default_factory=list)


class GenerationLogEntry(BaseModel):
    id: uuid.UUID
    problem_id: str
    unit_id: str
    lesson_index: int
    level: int
    difficulty: str
    provider: str
    model_name: str
    prompt_version: str
    execution_time_s: float
    created_at: datetime


class CuratedProblem(BaseModel):
    """Few-shot / curated example row (few_shot_examples).

    Content fields are copied from ``example_json`` for admin display.
    """

    id: int
    unit_id: str
    lesson_index: int
    difficulty: str
    level: int
    strategy: str | None = None
    variant_index: int = 1
    is_active: bool = True
    promoted: bool = False
    created_at: datetime
    title: str | None = None
    statement: str | None = None
    steps: list[dict] = Field(default_factory=list)
    course_name: str | None = None
    """Display name of the chemistry course (from units.course)."""
    chapter_name: str | None = None
    """Unit title — used as the \"chapter\" in admin grouping."""


# ── Student analytics (teacher view) ────────────────────────


class StudentAttemptOut(BaseModel):
    """One problem attempt row for the teacher's student detail panel."""

    id: uuid.UUID
    unit_id: str
    lesson_index: int
    level: int
    score: float | None
    is_complete: bool
    started_at: datetime


class StudentAnalyticsOut(BaseModel):
    """Per-student analytics returned to the teacher dashboard."""

    student_id: uuid.UUID
    overall_mastery: float
    category_scores: dict
    recent_attempts: list[StudentAttemptOut]
    lessons_with_data: int


# ── Requests ────────────────────────────────────────────────


class HeartbeatRequest(BaseModel):
    classroom_id: uuid.UUID
    step_id: str | None = Field(default=None, max_length=120)


class TeacherClassCreate(BaseModel):
    """Create class for authenticated teacher (no teacher_id in body)."""

    name: str = Field(min_length=1, max_length=200)
    unit_id: str | None = None


class TeacherClassPatch(BaseModel):
    """Partial update for PATCH /teacher/classes/{id}."""

    calculator_enabled: bool | None = None


class ExitTicketGenerateRequest(BaseModel):
    classroom_id: uuid.UUID
    unit_id: str = Field(min_length=1, description="Curriculum unit (chapter) ID — required")
    lesson_index: int = Field(ge=0, description="0-based lesson position within the unit — required")
    lesson_id: str | None = Field(default=None, description="Curriculum lesson slug, auto-resolved from unit_id + lesson_index")
    difficulty: str = "medium"
    question_count: int = Field(default=4, ge=1, le=10)
    time_limit_minutes: int = 10


class ExitTicketPersistRequest(BaseModel):
    """Optional: persist generated questions as a new exit ticket session."""

    classroom_id: uuid.UUID
    unit_id: str
    lesson_index: int = 0
    difficulty: str = "medium"
    time_limit_minutes: int = 10
    questions: list[ExitTicketQuestion]


class ExitTicketBundleOut(BaseModel):
    ticket: ExitTicketConfig
    responses: list[ExitTicketResponseItem]


class ExitTicketsForClassOut(BaseModel):
    analytics: ExitTicketAnalytics
    items: list[ExitTicketBundleOut]
    page: int = 1
    total_pages: int = 1


class ExitTicketGenerateResponse(BaseModel):
    """Returned after AI generation; ticket is persisted."""

    ticket: ExitTicketConfig


# ── Classroom sessions (persisted history) ───────────────────


class ClassroomSessionOut(BaseModel):
    """One persisted session row for GET /teacher/classes/{id}/sessions."""

    id: uuid.UUID
    classroom_id: uuid.UUID
    session_type: str
    exit_ticket_id: uuid.UUID | None = None
    unit_id: str
    lesson_index: int
    timed_practice_minutes: int | None = None
    started_at: datetime
    ended_at: datetime | None = None


# ── Aggregate misconception analytics ────────────────────────


class AggregateMisconceptionItem(BaseModel):
    tag: str
    count: int
    pct: float = Field(description="Percentage of total wrong answers attributed to this tag")


class AggregateMisconceptionAnalytics(BaseModel):
    class_id: uuid.UUID
    total_wrong: int
    items: list[AggregateMisconceptionItem]


# ── Timed practice analytics ─────────────────────────────────


class LevelStats(BaseModel):
    count: int = 0
    avg_score: float = 0.0


class StudentTimedPracticeRow(BaseModel):
    student_id: uuid.UUID
    student_name: str | None = None
    levels: dict[int, LevelStats] = Field(default_factory=dict)
    total_count: int = 0


class TimedPracticeAnalytics(BaseModel):
    session_id: uuid.UUID
    unit_id: str
    lesson_index: int
    rows: list[StudentTimedPracticeRow]

