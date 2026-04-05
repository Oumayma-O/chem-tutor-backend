"""User models: User (native auth), UserProfile, StudentInterest."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base
from app.infrastructure.database.models._helpers import _now, _uuid


class User(Base):
    """Native auth user — email + bcrypt password."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class UserProfile(Base):
    """
    Extended profile (grade, course, interests). ``user_id`` matches ``users.id`` from native auth.
    """
    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
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
