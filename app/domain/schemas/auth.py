"""Auth schemas — register, login, token, current user."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "student" | "teacher"
    name: str
    grade_level: Optional[str] = None   # display string e.g. "High School (9–10)"
    grade: Optional[str] = None         # grade name for profile (e.g. "12th Grade")
    course: Optional[str] = None        # course name for profile (e.g. "AP Chemistry")
    class_name: Optional[str] = None    # teacher only
    interests: Optional[list[str]] = None  # interest slugs

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("student", "teacher"):
            raise ValueError("role must be 'student' or 'teacher'")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    name: str


class ProfileUpdateRequest(BaseModel):
    grade: Optional[str] = None
    course: Optional[str] = None
    interests: Optional[list[str]] = None


class MeResponse(BaseModel):
    user_id: str
    email: str
    role: str
    name: str
    grade_level: Optional[str] = None
    grade: Optional[str] = None
    course: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    classroom_id: Optional[str] = None
    classroom_name: Optional[str] = None
    classroom_code: Optional[str] = None
