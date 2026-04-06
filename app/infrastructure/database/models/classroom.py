"""Classroom models: Classroom, ClassroomStudent, ClassroomCurriculumOverride."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base
from app.infrastructure.database.models._helpers import _now, _uuid


class Classroom(Base):
    """Teacher-managed classroom. Students join via a short alphanumeric code."""
    __tablename__ = "classrooms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    unit_id: Mapped[str | None] = mapped_column(
        String(100), ForeignKey("units.id"), nullable=True
    )

    code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    calculator_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # Teacher publish (exit ticket + optional timed practice); students poll GET /classrooms/me/live-session
    live_session: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

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
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    classroom: Mapped["Classroom"] = relationship(back_populates="students")

    __table_args__ = (
        Index("ix_classroom_students_student", "student_id"),
    )


class ClassroomCurriculumOverride(Base):
    """
    Per-classroom overrides on top of the global phase/unit ordering.
    A missing row means 'use global default'.
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

    phase_id: Mapped[int | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"), nullable=True
    )
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
