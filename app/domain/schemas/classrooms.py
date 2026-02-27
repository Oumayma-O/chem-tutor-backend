"""Pydantic schemas for classroom management."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    teacher_id: uuid.UUID
    chapter_id: str | None = None


class ClassroomOut(BaseModel):
    id: uuid.UUID
    name: str
    teacher_id: uuid.UUID
    chapter_id: str | None
    code: str
    is_active: bool
    student_count: int
    created_at: datetime


class JoinClassroomRequest(BaseModel):
    student_id: uuid.UUID
    code: str = Field(min_length=4, max_length=10)


class JoinClassroomResponse(BaseModel):
    classroom_id: uuid.UUID
    classroom_name: str
    chapter_id: str | None


class ClassroomStudentOut(BaseModel):
    student_id: uuid.UUID
    joined_at: datetime


class ClassroomListItem(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    chapter_id: str | None
    student_count: int
    is_active: bool
