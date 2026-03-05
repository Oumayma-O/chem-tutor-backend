"""
SQLAlchemy ORM models for the Chemistry Tutor backend.

Table groups:
  - Auth              : users (email/password auth)
  - Lookup data       : grades, courses, interests
  - User profiles     : user_profiles, student_interests
  - Content catalog   : phases, units, lessons, standards, lesson_standards
  - Classrooms        : classrooms, classroom_students,
                        classroom_curriculum_overrides
  - Problem cache     : problem_cache
  - Learning state    : problem_attempts, skill_mastery,
                        misconception_logs, thinking_tracker_logs
  - Teacher tools     : exit_tickets, exit_ticket_responses
  - RAG               : curriculum_documents
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


# ── Helpers ───────────────────────────────────────────────────

def _uuid() -> uuid.UUID:
    return uuid.uuid4()

def _now() -> datetime:
    return datetime.utcnow()


# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════

class User(Base):
    """Native auth user — email + bcrypt password.  Replaces Supabase auth."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ══════════════════════════════════════════════════════════════
# LOOKUP TABLES
# ══════════════════════════════════════════════════════════════

class Grade(Base):
    """Academic grade / level.  e.g. 'Middle School', 'AP / Advanced'."""
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user_profiles: Mapped[list["UserProfile"]] = relationship(back_populates="grade")
    units: Mapped[list["Unit"]] = relationship(back_populates="grade")


class Course(Base):
    """Chemistry course type.  e.g. 'General Chemistry', 'AP Chemistry'."""
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grades.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user_profiles: Mapped[list["UserProfile"]] = relationship(back_populates="course")
    units: Mapped[list["Unit"]] = relationship(back_populates="course")


class Interest(Base):
    """Student interest for contextual problem generation."""
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Slug used as context_tag in problem generation (e.g. "sports", "music")
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)   # Display: "Food & Cooking"
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)  # emoji or lucide name
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


# ══════════════════════════════════════════════════════════════
# USER PROFILES
# ══════════════════════════════════════════════════════════════

class UserProfile(Base):
    """
    Minimal user profile.  Auth (email/password) lives in Supabase.
    user_id is the Supabase auth.users UUID — no FK constraint here.
    """
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")  # student|teacher
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grades.id"), nullable=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    grade: Mapped["Grade | None"] = relationship(back_populates="user_profiles")
    course: Mapped["Course | None"] = relationship(back_populates="user_profiles")
    interests: Mapped[list["StudentInterest"]] = relationship(back_populates="user")

    __table_args__ = (
        Index("ix_user_profiles_role", "role"),
    )


class StudentInterest(Base):
    """Junction: student ↔ interest (many-to-many)."""
    __tablename__ = "student_interests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    interest_id: Mapped[int] = mapped_column(
        ForeignKey("interests.id", ondelete="CASCADE"),
        primary_key=True,
    )

    user: Mapped["UserProfile"] = relationship(back_populates="interests")
    interest: Mapped["Interest"] = relationship()


# ══════════════════════════════════════════════════════════════
# CONTENT CATALOG  (phases, units, lessons, standards, lesson_standards)
# ══════════════════════════════════════════════════════════════

class Phase(Base):
    """
    A curriculum phase groups related units under a named milestone
    (e.g. 'Phase 1: The Basics').

    Phases are course-specific: AP Chemistry has 9 units across 3 phases;
    Standard Chemistry has 15+ units across more phases.
    course_id = NULL means the phase applies to all courses.
    """
    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id"), nullable=True, index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Optional display color hint (CSS color / Tailwind class)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    course: Mapped["Course | None"] = relationship()
    units: Mapped[list["Unit"]] = relationship(
        back_populates="phase",
        order_by="Unit.order_within_phase",
        foreign_keys="Unit.phase_id",
    )

    __table_args__ = (
        UniqueConstraint("course_id", "sort_order", name="uq_phase_course_order"),
    )


class Unit(Base):
    """
    A top-level curriculum unit (e.g. 'Chemical Kinetics').
    id is a URL-safe slug: 'chemical-kinetics'.
    """
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)      # emoji
    gradient: Mapped[str | None] = mapped_column(String(200), nullable=True) # CSS gradient

    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grades.id"), nullable=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)

    # Phase grouping — nullable so existing rows survive the migration
    phase_id: Mapped[int | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Position within the phase (0-based).  Falls back to sort_order when NULL.
    order_within_phase: Mapped[int | None] = mapped_column(Integer, nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_coming_soon: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    grade: Mapped["Grade | None"] = relationship(back_populates="units")
    course: Mapped["Course | None"] = relationship(back_populates="units")
    phase: Mapped["Phase | None"] = relationship(
        back_populates="units", foreign_keys=[phase_id]
    )
    unit_lessons: Mapped[list["UnitLesson"]] = relationship(
        back_populates="unit", cascade="all, delete-orphan",
        order_by="UnitLesson.lesson_order",
    )

    __table_args__ = (
        Index("ix_units_grade_course", "grade_id", "course_id"),
        Index("ix_units_phase", "phase_id"),
    )


class Lesson(Base):
    """
    A lesson within a unit (e.g. 'Zero-Order Kinetics').
    lesson_index is 0-based and stable — used as the FK key everywhere.
    """
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-based, stable

    key_equations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    objectives: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Stable human-readable slug (e.g. "L-mole-molar-mass-1step")
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    is_ap_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Bridge: AP lesson extends this Standard lesson (slug). NULL = not an extension.
    extension_of: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    # True when this lesson has an associated simulation.
    has_simulation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Cached reference card — generated once by the LLM chain, never regenerated
    # unless manually cleared.  NULL = not yet generated.
    reference_card_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    unit_lessons: Mapped[list["UnitLesson"]] = relationship(back_populates="lesson")
    standards: Mapped[list["LessonStandard"]] = relationship(back_populates="lesson")

    __table_args__ = (
        UniqueConstraint("unit_id", "lesson_index", name="uq_lesson_unit_index"),
        Index("ix_lessons_unit", "unit_id"),
    )


class UnitLesson(Base):
    """
    Junction: unit ↔ lesson (many-to-many via unit_lessons table).
    lesson_order is 0-based display position within a given unit.
    """
    __tablename__ = "unit_lessons"

    unit_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("units.id", ondelete="CASCADE"), primary_key=True
    )
    lesson_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    lesson_order: Mapped[int] = mapped_column(Integer, nullable=False)

    unit: Mapped["Unit"] = relationship(back_populates="unit_lessons")
    lesson: Mapped["Lesson"] = relationship(back_populates="unit_lessons")

    __table_args__ = (
        Index("ix_unit_lessons_unit", "unit_id"),
    )


class Standard(Base):
    """Curriculum standard (NGSS, CA, AP, etc.)."""
    __tablename__ = "standards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)  # "NGSS HS-PS1-5"
    framework: Mapped[str] = mapped_column(String(50), nullable=False)  # "NGSS" | "CA" | "AP"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    lessons: Mapped[list["LessonStandard"]] = relationship(back_populates="standard")


class LessonStandard(Base):
    """Junction: lesson ↔ standard (many-to-many)."""
    __tablename__ = "lesson_standards"

    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    standard_id: Mapped[int] = mapped_column(
        ForeignKey("standards.id", ondelete="CASCADE"), primary_key=True
    )

    lesson: Mapped["Lesson"] = relationship(back_populates="standards")
    standard: Mapped["Standard"] = relationship(back_populates="lessons")


# ══════════════════════════════════════════════════════════════
# CLASSROOMS
# ══════════════════════════════════════════════════════════════

class Classroom(Base):
    """
    Teacher-managed classroom.
    Students join via a short alphanumeric `code`.
    """
    __tablename__ = "classrooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Optional unit focus
    unit_id: Mapped[str | None] = mapped_column(
        String(100), ForeignKey("units.id"), nullable=True
    )

    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)  # join code
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    students: Mapped[list["ClassroomStudent"]] = relationship(back_populates="classroom")
    unit: Mapped["Unit | None"] = relationship()


class ClassroomStudent(Base):
    """Junction: classroom ↔ student (many-to-many)."""
    __tablename__ = "classroom_students"

    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        primary_key=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    classroom: Mapped["Classroom"] = relationship(back_populates="students")

    __table_args__ = (
        Index("ix_classroom_students_student", "student_id"),
    )


class ClassroomCurriculumOverride(Base):
    """
    Per-classroom overrides on top of the global phase/unit ordering.

    Design intent
    ─────────────
    • Content (lessons, videos, text) lives only in `units` / `lessons`.
    • This table only stores *ordering* and *visibility* overrides.
    • A missing row means "use global default" — teachers don't need a row
      for every unit, only for units they've customised.

    Override semantics
    ──────────────────
    • phase_id    — move this unit to a different phase for this class.
                    NULL = keep the unit's default phase.
    • custom_order — position within the (possibly overridden) phase.
                    NULL = use unit.order_within_phase.
    • is_hidden   — exclude unit from students' view entirely.
    • synced_at   — last time this row was refreshed from global defaults
                    (used by the "Sync with Global Default" UX action).
    """
    __tablename__ = "classroom_curriculum_overrides"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    unit_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Move unit to a different phase for this classroom (NULL = keep default)
    phase_id: Mapped[int | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"), nullable=True
    )
    # Override display position within the phase (NULL = use unit.order_within_phase)
    custom_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    classroom: Mapped["Classroom"] = relationship()
    unit: Mapped["Unit"] = relationship()
    phase: Mapped["Phase | None"] = relationship()

    __table_args__ = (
        UniqueConstraint("classroom_id", "unit_id", name="uq_cco_classroom_unit"),
        Index("ix_cco_classroom", "classroom_id"),
        Index("ix_cco_unit", "unit_id"),
    )


# ══════════════════════════════════════════════════════════════
# PROBLEM CACHE  (Level 1 worked examples + generated problems)
# ══════════════════════════════════════════════════════════════

class ProblemCache(Base):
    """
    Cached AI-generated problems.

    Level 1 (worked examples) are expensive to generate → cached and reused.
    Level 2/3 problems may also be cached for performance.

    Cache key: (unit_id, lesson_index, difficulty, level, context_tag).
    Entries expire after `expires_at`; NULL = never expires.
    """
    __tablename__ = "problem_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 | 2 | 3
    context_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Full ProblemOutput JSON
    problem_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_problem_cache_key",
            "unit_id", "lesson_index", "difficulty", "level", "context_tag",
        ),
    )


# ══════════════════════════════════════════════════════════════
# LEARNING STATE
# ══════════════════════════════════════════════════════════════

class ProblemAttempt(Base):
    """
    Each time a student works a problem, one row is inserted.
    step_log (JSONB) captures every step: input, correct/incorrect, time_spent, hints_used.
    """
    __tablename__ = "problem_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    class_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)
    problem_id: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=2)  # 1 | 2 | 3

    # Outcome
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0–1.0

    # JSONB payload: list of StepLog objects
    step_log: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_attempts_user_unit", "user_id", "unit_id", "lesson_index"),
        Index("ix_attempts_user_level", "user_id", "level"),
    )


class SkillMastery(Base):
    """
    Rolling mastery score per (user, unit, lesson).
    Updated after each completed attempt.

    level3_unlocked: permanently True once mastery >= threshold on hard difficulty.
                     This flag is irreversible — never set back to False.
    """
    __tablename__ = "skill_mastery"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)

    mastery_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attempts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    consecutive_correct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")

    # Permanent Level 3 unlock — once True, stays True
    level3_unlocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    level3_unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Per-category mastery scores (0.0–1.0)
    # {conceptual: 0.58, procedural: 0.70, computational: 0.50}
    category_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # JSONB: {conceptual: int, procedural: int, computational: int, representation: int}
    error_counts: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # JSONB: last N attempt scores for rolling average
    recent_scores: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    __table_args__ = (
        UniqueConstraint("user_id", "unit_id", "lesson_index", name="uq_mastery_user_lesson"),
        Index("ix_mastery_user", "user_id"),
    )


class ThinkingTrackerLog(Base):
    """
    Granular per-step reasoning record from ThinkingAnalysisService.

    Stored separately from step_log for queryability.
    Used for the Thinking Tracker panel in the UI.
    """
    __tablename__ = "thinking_tracker_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)

    step_id: Mapped[str] = mapped_column(String(100), nullable=False)
    step_label: Mapped[str] = mapped_column(String(100), nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Substitution|Calculation|Units|…

    student_input: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hints_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Cognitive classification from ThinkingAnalysisService
    reasoning_pattern: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Procedural | Conceptual | Units | Arithmetic | …

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_thinking_user_unit", "user_id", "unit_id", "lesson_index"),
    )


class MisconceptionLog(Base):
    """Granular error record per incorrect step."""
    __tablename__ = "misconception_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    class_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    error_category: Mapped[str] = mapped_column(String(50), nullable=False)
    error_subcategory: Mapped[str | None] = mapped_column(String(100), nullable=True)
    misconception_tag: Mapped[str | None] = mapped_column(String(100), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)  # blocking|slowing|minor
    step_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_misconception_user", "user_id"),
        Index("ix_misconception_class", "class_id"),
        Index("ix_misconception_unit", "unit_id", "lesson_index"),
    )


# ══════════════════════════════════════════════════════════════
# RAG CONTEXT  (curriculum documents)
# ══════════════════════════════════════════════════════════════

class CurriculumDocument(Base):
    """
    Uploaded curriculum content (PDF, text, standards JSON).
    Text is extracted and stored for LLM RAG context injection.

    """
    __tablename__ = "curriculum_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    unit_id: Mapped[str | None] = mapped_column(
        String(100), ForeignKey("units.id"), nullable=True, index=True
    )
    lesson_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("lessons.id"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # pdf|text|standards_json
    filename: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Extracted plain text (used for RAG)
    content_text: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Structured metadata (standards codes, equations, skills extracted)
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    # e.g. {"standards": ["NGSS HS-PS1-5"], "equations": ["[A]t = [A]0 - kt"], "skills": [...]}

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ══════════════════════════════════════════════════════════════
# TEACHER TOOLS
# ══════════════════════════════════════════════════════════════

class ExitTicket(Base):
    """
    An exit ticket session generated for a class by a teacher.
    Questions are stored in JSONB for simplicity (small fixed sets).
    """
    __tablename__ = "exit_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    time_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # JSONB list of question objects
    questions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    responses: Mapped[list["ExitTicketResponse"]] = relationship(back_populates="exit_ticket")


class ExitTicketResponse(Base):
    """Student submission for one exit ticket session."""
    __tablename__ = "exit_ticket_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exit_ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exit_tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # JSONB: list of {question_id, answer, is_correct, time_spent_seconds}
    answers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)   # 0.0–1.0
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    exit_ticket: Mapped["ExitTicket"] = relationship(back_populates="responses")


# ══════════════════════════════════════════════════════════════
# USER LESSON PLAYLISTS  (per-user ordered problem history)
# ══════════════════════════════════════════════════════════════

class UserLessonPlaylist(Base):
    """
    Ordered list of problems served to a student for one
    (user, unit, lesson, level, difficulty) slot.

    - problems: JSONB array of full ProblemOutput dicts, in order seen
    - current_index: where the user currently is (0-based)
    - Capped at MAX_PROBLEMS_PER_LEVEL[level] entries (playlist_repo)
    """
    __tablename__ = "user_lesson_playlists"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    unit_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    lesson_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[int] = mapped_column(Integer, primary_key=True)
    difficulty: Mapped[str] = mapped_column(String(20), primary_key=True)

    problems: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    current_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    __table_args__ = (
        Index("ix_playlist_user_unit", "user_id", "unit_id"),
    )


# ══════════════════════════════════════════════════════════════
# LESSON PROGRESS  (simple per-student lesson status)
# ══════════════════════════════════════════════════════════════

class LessonProgress(Base):
    """
    Simple lesson completion status per student.
    Separate from SkillMastery (which tracks detailed mastery scores).
    Used by the frontend sidebar to show not-started / in-progress / completed.
    """
    __tablename__ = "lesson_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    unit_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    lesson_index: Mapped[int] = mapped_column(Integer, primary_key=True)

    # "not-started" | "in-progress" | "completed"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not-started")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    __table_args__ = (
        Index("ix_lesson_progress_user", "user_id"),
        Index("ix_lesson_progress_user_unit", "user_id", "unit_id"),
    )


# ══════════════════════════════════════════════════════════════
# GENERATION LOGS  (benchmarking / prompt monitoring)
# ══════════════════════════════════════════════════════════════

class GenerationLog(Base):
    """
    One row per problem generation call.
    Tracks provider, model, prompt version, and wall-clock time so you can
    benchmark different providers / prompt revisions side-by-side.
    """
    __tablename__ = "generation_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    # What was generated
    problem_id: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)

    # Who generated it
    provider: Mapped[str] = mapped_column(String(50), nullable=False)   # openai|anthropic|gemini
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # How long it took (seconds, 3 decimal places)
    execution_time_s: Mapped[float] = mapped_column(Float, nullable=False)

    # Full generated output for offline comparison
    problem_json: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_gen_logs_provider_model", "provider", "model_name"),
        Index("ix_gen_logs_prompt_version", "prompt_version"),
        Index("ix_gen_logs_unit_lesson", "unit_id", "lesson_index"),
    )


# ══════════════════════════════════════════════════════════════
# PROMPT VERSIONS  (audit trail for prompt changes)
# ══════════════════════════════════════════════════════════════

class PromptVersion(Base):
    """
    One row per prompt version string (v1, v2, …).
    Inserted automatically on startup when PROMPT_VERSION changes.
    Lets you join generation_logs → prompt_versions to see exactly
    which template was active for any given generation.
    """
    __tablename__ = "prompt_versions"

    version: Mapped[str] = mapped_column(String(20), primary_key=True)  # "v1", "v2", …
    template: Mapped[str] = mapped_column(Text, nullable=False)          # full system prompt text
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
