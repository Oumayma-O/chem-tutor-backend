"""Auth schemas — register, login, token, current user."""

from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str  # "student" | "teacher"
    name: str
    grade_level: Optional[str] = None   # display string e.g. "High School (9–10)"
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
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    name: str


class MeResponse(BaseModel):
    user_id: str
    email: str
    role: str
    name: str
    grade_level: Optional[str] = None
    interests: list[str] = []
