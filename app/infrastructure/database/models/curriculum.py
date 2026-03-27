"""Content catalog: Phase, Unit, Lesson, UnitLesson, Standard, LessonStandard."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base
from app.infrastructure.database.models._helpers import _now, _uuid

if TYPE_CHECKING:
    from app.infrastructure.database.models.lookup import Course, Grade


class Phase(Base):
    """
    A curriculum phase groups related units under a named milestone.
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
    id is a URL-safe slug: 'unit-chemical-kinetics'.
    """
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gradient: Mapped[str | None] = mapped_column(String(200), nullable=True)

    grade_id: Mapped[int | None] = mapped_column(ForeignKey("grades.id"), nullable=True)
    course_id: Mapped[int | None] = mapped_column(ForeignKey("courses.id"), nullable=True)

    phase_id: Mapped[int | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"), nullable=True, index=True
    )
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
    slug is a human-readable stable identifier (e.g. 'L-mole-molar-mass-1step').
    """
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False)

    key_equations: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    objectives: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    key_rules: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    misconceptions: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    # Cognitive blueprint for problem generation (solver | recipe | architect | detective | lawyer)
    blueprint: Mapped[str] = mapped_column(String(20), nullable=False, default="solver")
    # Tools available to the student for this lesson
    required_tools: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    is_ap_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    extension_of: Mapped[str | None] = mapped_column(String(100), nullable=True, default=None)
    has_simulation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Cached reference card — generated once by LLM, NULL = not yet generated
    reference_card_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    unit_lessons: Mapped[list["UnitLesson"]] = relationship(back_populates="lesson")
    standards: Mapped[list["LessonStandard"]] = relationship(back_populates="lesson")

    __table_args__ = (
        Index("ix_lessons_index", "lesson_index"),
    )


class UnitLesson(Base):
    """Junction: unit ↔ lesson (many-to-many). lesson_order is display position within the unit."""
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
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_core: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

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
