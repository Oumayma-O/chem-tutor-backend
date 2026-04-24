"""
Auth router — native email/password authentication.

POST /auth/register  → create account + return JWT
POST /auth/login     → verify credentials + return JWT
GET  /auth/me        → return current user from JWT
PUT/PATCH /auth/me   → update email, password, and/or username (staff only)
PATCH /auth/profile  → update grade, course, interests
POST /auth/heartbeat → record 1 minute of active session (call every 60 s)
"""

import uuid
from datetime import date, timezone
from datetime import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context
from app.core.logging import get_logger
from app.domain.schemas.auth import (
    AccountUpdateRequest,
    LoginRequest,
    MeResponse,
    ProfileUpdateRequest,
    RegisterRequest,
    SseTokenResponse,
    TokenResponse,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import User, UserProfile
from app.infrastructure.database.repositories.student_repo import (
    CourseRepository,
    GradeRepository,
    UserProfileRepository,
)
from app.infrastructure.database.repositories.session_activity_repo import SessionActivityRepository
from app.services.auth.profile_service import AuthProfileService
from app.services.auth.security import (
    create_access_token,
    create_sse_token,
    hash_password,
    verify_password,
)
from app.services.auth.user_factory import create_user

logger = get_logger(__name__)
router = APIRouter(prefix="/auth")


# ── Helpers ────────────────────────────────────────────────────────────────

async def _get_user_by_email(email: str, db: AsyncSession) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    return result.scalar_one_or_none()


def _profile_service(db: AsyncSession = Depends(get_db)) -> AuthProfileService:
    return AuthProfileService(db)


# ── Register ───────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = await _get_user_by_email(req.email, db)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = await create_user(
        db, email=req.email, password=req.password, role=req.role, name=req.username, commit=False,
    )

    if req.role == "student" and req.interests:
        interest_ids = await AuthProfileService(db).resolve_interest_ids(req.interests)
        await UserProfileRepository(db).set_interests(user.id, interest_ids)

    token = create_access_token(str(user.id), user.email, user.role)
    logger.info("user_registered", user_id=str(user.id), role=user.role)
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        username=user.name,
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
        username=user.name,
    )


# ── Me ─────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=MeResponse)
async def me(
    response: Response,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    profile_svc: AuthProfileService = Depends(_profile_service),
) -> MeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return await profile_svc.build_me_response(auth.user_id)


# ── Profile Update ─────────────────────────────────────────────────────────

@router.patch("/profile", response_model=MeResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    profile_svc: AuthProfileService = Depends(_profile_service),
) -> MeResponse:
    repo = UserProfileRepository(db)
    profile = await repo.get_by_id(auth.user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    if req.grade is not None:
        grade_row = await GradeRepository(db).get_by_name(req.grade.strip())
        if grade_row:
            profile.grade_id = grade_row.id

    if req.course is not None:
        course_row = await CourseRepository(db).get_by_name(req.course.strip())
        if course_row:
            profile.course_id = course_row.id

    # Update teacher onboarding fields on the User row
    if req.district is not None or req.school is not None:
        result = await db.execute(select(User).where(User.id == auth.user_id))
        user = result.scalar_one_or_none()
        if user:
            if req.district is not None:
                user.district = req.district.strip() or None
            if req.school is not None:
                user.school = req.school.strip() or None

    await db.flush()

    if req.interests is not None:
        interest_ids = await profile_svc.resolve_interest_ids(req.interests)
        await repo.set_interests(auth.user_id, interest_ids)

    logger.info("profile_updated", user_id=str(auth.user_id))
    return await profile_svc.build_me_response(auth.user_id)


# ── Account update (email / password / display name) ───────────────────────


_STAFF_ROLES = frozenset({"teacher", "admin", "superadmin"})


@router.put("/me", response_model=MeResponse)
@router.patch("/me", response_model=MeResponse)
async def update_account(
    req: AccountUpdateRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    profile_svc: AuthProfileService = Depends(_profile_service),
) -> MeResponse:
    """Update the authenticated user's email, password, and/or username."""
    result = await db.execute(select(User).where(User.id == auth.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if req.username is not None:
        if user.role not in _STAFF_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers and administrators can change their username.",
            )
        user.name = req.username
        profile_row = await UserProfileRepository(db).get_by_id(auth.user_id)
        if profile_row:
            profile_row.name = req.username
        else:
            db.add(UserProfile(user_id=user.id, role=user.role, name=req.username))

    if req.email is not None:
        normalized = req.email.lower().strip()
        if normalized != user.email:
            taken = await db.scalar(select(User).where(User.email == normalized))
            if taken:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use.")
            user.email = normalized

    if req.new_password is not None:
        if not req.current_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="current_password is required to set a new password.",
            )
        if not verify_password(req.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect.")
        user.password_hash = hash_password(req.new_password)

    await db.commit()
    await db.refresh(user)
    logger.info("account_updated", user_id=str(auth.user_id))
    response.headers["Cache-Control"] = "private, no-store"
    return await profile_svc.build_me_response(auth.user_id)


@router.post("/sse-token", response_model=SseTokenResponse)
async def issue_sse_token(
    auth: AuthContext = Depends(get_auth_context),
) -> SseTokenResponse:
    ttl_seconds = 120
    token = create_sse_token(
        user_id=str(auth.user_id),
        email=auth.email or "",
        role=auth.role,
        ttl_seconds=ttl_seconds,
    )
    return SseTokenResponse(sse_token=token, expires_in_seconds=ttl_seconds)


# ── Heartbeat ──────────────────────────────────────────────────────────────

@router.post("/heartbeat", status_code=204)
async def heartbeat(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    """Record one minute of active session for the current user.

    The frontend should call this endpoint every 60 seconds while the user
    has the app open.  The first call of a calendar day counts as a login;
    subsequent calls only increment ``total_minutes_active``.
    """
    today: date = dt.now(timezone.utc).date()
    await SessionActivityRepository(db).record_heartbeat(auth.user_id, today)
