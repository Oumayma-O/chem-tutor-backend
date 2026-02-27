"""Pydantic schemas for student / user profile management."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class InterestOut(BaseModel):
    id: int
    slug: str
    label: str
    icon: str | None = None


class GradeOut(BaseModel):
    id: int
    name: str
    sort_order: int


class CourseOut(BaseModel):
    id: int
    name: str
    grade_id: int | None


class UserProfileCreate(BaseModel):
    user_id: uuid.UUID
    role: Literal["student", "teacher"] = "student"
    name: str = Field(min_length=1, max_length=200)
    grade_id: int | None = None
    course_id: int | None = None
    interest_ids: list[int] = Field(default_factory=list)


class UserProfileUpdate(BaseModel):
    name: str | None = None
    grade_id: int | None = None
    course_id: int | None = None
    interest_ids: list[int] | None = None


class UserProfileOut(BaseModel):
    user_id: uuid.UUID
    role: str
    name: str
    grade: GradeOut | None = None
    course: CourseOut | None = None
    interests: list[InterestOut] = Field(default_factory=list)
    created_at: datetime


class StudentContextOut(BaseModel):
    """
    Flattened profile context used by AI services.
    Returned by GET /students/{id}/context.
    """
    user_id: uuid.UUID
    grade_level: str | None    # Grade.name
    course: str | None         # Course.name
    interests: list[str]       # Interest.slug list  (used as context_tags)
    interest_labels: list[str] # Interest.label list (display names)
