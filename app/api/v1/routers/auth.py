"""
Auth router — native email/password authentication.

POST /auth/register  → create account + return JWT
POST /auth/login     → verify credentials + return JWT
GET  /auth/me        → return current user from JWT
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import (
    Classroom,
    Interest,
    StudentInterest,
    User,
    UserProfile,
)
from app.services.auth.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/auth")
bearer = HTTPBearer(auto_error=False)


# ── Helpers ────────────────────────────────────────────────────────────────

async def _get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    return result.scalar_one_or_none()


async def _resolve_interest_ids(slugs: list[str], db: AsyncSession) -> list[int]:
    if not slugs:
        return []
    result = await db.execute(select(Interest).where(Interest.slug.in_(slugs)))
    return [i.id for i in result.scalars().all()]


# ── Register ───────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    # Duplicate email check
    existing = await _get_user_by_email(req.email, db)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    # Create user
    user = User(
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        role=req.role,
        name=req.name.strip(),
    )
    db.add(user)
    await db.flush()  # get user.id without committing

    # Create profile
    profile = UserProfile(user_id=user.id, role=req.role, name=req.name.strip())
    db.add(profile)
    await db.flush()

    # Resolve + attach interests (students only)
    if req.role == "student" and req.interests:
        interest_ids = await _resolve_interest_ids(req.interests, db)
        for iid in interest_ids:
            db.add(StudentInterest(user_id=user.id, interest_id=iid))

    # Create classroom (teachers)
    if req.role == "teacher" and req.class_name:
        classroom = Classroom(
            name=req.class_name.strip(),
            teacher_id=user.id,
            code="",
        )
        # Generate a simple 6-char code
        import random, string
        classroom.code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        db.add(classroom)

    await db.commit()

    token = create_access_token(str(user.id), user.email, user.role)
    logger.info("user_registered", user_id=str(user.id), role=user.role)
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        name=user.name,
    )


# ── Login ──────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await _get_user_by_email(req.email, db)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

    token = create_access_token(str(user.id), user.email, user.role)
    logger.info("user_logged_in", user_id=str(user.id), role=user.role)
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        name=user.name,
    )


# ── Me ─────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=MeResponse)
async def me(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> MeResponse:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Fetch interests
    si_result = await db.execute(
        select(Interest).join(StudentInterest, Interest.id == StudentInterest.interest_id)
        .where(StudentInterest.user_id == user_id)
    )
    interest_slugs = [i.slug for i in si_result.scalars().all()]

    # Fetch grade from profile
    profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = profile_result.scalar_one_or_none()

    return MeResponse(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        name=user.name,
        grade_level=None,  # could join Grade here if needed
        interests=interest_slugs,
    )
