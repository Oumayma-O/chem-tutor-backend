"""Auth schemas — register, login, token, current user."""

from typing import Optional

from pydantic import AliasChoices, BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "student" only (public signup)
    username: str = Field(
        max_length=200,
        validation_alias=AliasChoices("username", "name"),
    )
    interests: Optional[list[str]] = None  # interest slugs

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("username cannot be blank")
        return stripped

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v != "student":
            raise ValueError("Public registration is for students only.")
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
    username: str


class ProfileUpdateRequest(BaseModel):
    grade: Optional[str] = None
    course: Optional[str] = None
    interests: Optional[list[str]] = None
    district: Optional[str] = Field(default=None, max_length=300)
    school: Optional[str] = Field(default=None, max_length=300)


class MeResponse(BaseModel):
    user_id: str
    email: str
    role: str
    username: str
    grade_level: Optional[str] = None
    grade: Optional[str] = None
    course: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    classroom_id: Optional[str] = None
    classroom_name: Optional[str] = None
    classroom_code: Optional[str] = None
    district: Optional[str] = None
    school: Optional[str] = None


class AccountUpdateRequest(BaseModel):
    """PUT/PATCH /auth/me — update email, password, and/or username (staff only for username)."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(
        default=None,
        max_length=200,
        validation_alias=AliasChoices(
            "username",
            "name",
            "display_name",
            "displayName",
            "userName",
        ),
    )
    current_password: Optional[str] = Field(default=None, min_length=1)
    new_password: Optional[str] = Field(default=None, min_length=6)

    @field_validator("username")
    @classmethod
    def validate_username_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("username cannot be blank")
        return stripped


class SseTokenResponse(BaseModel):
    sse_token: str
    expires_in_seconds: int
