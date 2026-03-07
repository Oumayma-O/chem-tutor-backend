"""Learning state: ProblemCache, ProblemAttempt, SkillMastery, ThinkingTrackerLog,
MisconceptionLog, UserLessonPlaylist, LessonProgress."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.connection import Base
from app.infrastructure.database.models._helpers import _now, _uuid


class ProblemCache(Base):
    """
    Cached AI-generated problems.
    Cache key: (unit_id, lesson_index, difficulty, level, context_tag).
    """
    __tablename__ = "problem_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    context_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)

    problem_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_problem_cache_key",
            "unit_id", "lesson_index", "difficulty", "level", "context_tag",
        ),
    )


class ProblemAttempt(Base):
    """
    Each time a student works a problem, one row is inserted.
    step_log captures every step: input, correct/incorrect, time_spent, hints_used.
    """
    __tablename__ = "problem_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    class_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)
    problem_id: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=2)

    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

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
    level3_unlocked is a permanent one-way latch — never reverts to False.
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

    level3_unlocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    level3_unlocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    category_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_counts: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recent_scores: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    __table_args__ = (
        UniqueConstraint("user_id", "unit_id", "lesson_index", name="uq_mastery_user_lesson"),
        Index("ix_mastery_user", "user_id"),
    )


class ThinkingTrackerLog(Base):
    """Granular per-step reasoning record from ThinkingAnalysisService."""
    __tablename__ = "thinking_tracker_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)

    step_id: Mapped[str] = mapped_column(String(100), nullable=False)
    step_label: Mapped[str] = mapped_column(String(100), nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)

    student_input: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hints_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    reasoning_pattern: Mapped[str | None] = mapped_column(String(50), nullable=True)

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
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    step_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    __table_args__ = (
        Index("ix_misconception_user", "user_id"),
        Index("ix_misconception_class", "class_id"),
        Index("ix_misconception_unit", "unit_id", "lesson_index"),
    )


class UserLessonPlaylist(Base):
    """Ordered list of problems served to a student for one (user, unit, lesson, level, difficulty) slot."""
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


class LessonProgress(Base):
    """
    Simple lesson completion status per student.
    Used by the frontend sidebar: not-started / in-progress / completed.
    """
    __tablename__ = "lesson_progress"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    unit_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    lesson_index: Mapped[int] = mapped_column(Integer, primary_key=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not-started")

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    __table_args__ = (
        Index("ix_lesson_progress_user", "user_id"),
        Index("ix_lesson_progress_user_unit", "user_id", "unit_id"),
    )
