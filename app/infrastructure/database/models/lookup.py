"""Lookup tables: Grade, Course, Interest."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


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
    grade_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user_profiles: Mapped[list["UserProfile"]] = relationship(back_populates="course")
    units: Mapped[list["Unit"]] = relationship(back_populates="course")


class Interest(Base):
    """Student interest for contextual problem generation."""
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
