"""Teacher tools: ExitTicket, ExitTicketResponse, ClassroomSession, CurriculumDocument."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base
from app.infrastructure.database.models._helpers import _now, _uuid


class ExitTicket(Base):
    """Exit ticket session generated for a class by a teacher.

    Lifecycle: generated → draft (published_at=NULL) → published (published_at=<timestamp>).
    Only published tickets appear in the teacher history and are available to students.
    """
    __tablename__ = "exit_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lesson_id: Mapped[str | None] = mapped_column(String(200), nullable=True, default=None, index=True)

    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    time_limit_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    questions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # NULL = draft (generated but never published); non-NULL = published timestamp.
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, index=True
    )

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

    answers: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    time_spent_s: Mapped[int] = mapped_column(default=0, server_default="0")

    exit_ticket: Mapped["ExitTicket"] = relationship(back_populates="responses")

    __table_args__ = (
        UniqueConstraint("exit_ticket_id", "student_id", name="uq_exit_ticket_responses_ticket_student"),
    )


class ClassroomSession(Base):
    """Persisted record of a teacher-initiated session (timed practice, exit ticket, or both).

    Created on publish, ended_at set on stop.  Allows historical analytics
    and timed-practice per-student breakdowns long after the live_session JSONB is cleared.
    """
    __tablename__ = "classroom_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    session_type: Mapped[str] = mapped_column(String(40), nullable=False, default="exit_ticket")
    exit_ticket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exit_tickets.id", ondelete="SET NULL"),
        nullable=True,
    )
    unit_id: Mapped[str] = mapped_column(String(100), nullable=False)
    lesson_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    timed_practice_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_classroom_sessions_class_started", "classroom_id", "started_at"),
    )


class CurriculumDocument(Base):
    """Uploaded curriculum content (PDF, text, standards JSON) for RAG context."""
    __tablename__ = "curriculum_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)

    unit_id: Mapped[str | None] = mapped_column(
        String(100), ForeignKey("units.id"), nullable=True, index=True
    )
    lesson_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("lessons.id"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(300), nullable=True)

    content_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    doc_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
