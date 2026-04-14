"""
Auth router — native email/password authentication.

POST /auth/register  → create account + return JWT
POST /auth/login     → verify credentials + return JWT
GET  /auth/me        → return current user from JWT
PATCH /auth/profile  → update grade, course, interests
POST /auth/heartbeat → record 1 minute of active session (call every 60 s)
"""

import uuid
from datetime import date, timezone
from datetime import datetime as dt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.api.v1.authz import AuthContext, get_auth_context
from app.core.logging import get_logger
from app.domain.schemas.auth import (
    AccountUpdateRequest,
    LoginRequest,
    MeResponse,
    ProfileUpdateRequest,
    RegisterRequest,
    TokenResponse,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import (
    Classroom,
    ClassroomStudent,
    Interest,
    User,
    UserProfile,
)
from app.infrastructure.database.repositories.student_repo import (
    CourseRepository,
    GradeRepository,
    UserProfileRepository,
)
from app.infrastructure.database.repositories.session_activity_repo import SessionActivityRepository
from app.services.auth.security import (
    create_access_token,
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


async def _resolve_interest_ids(slugs: list[str], db: AsyncSession) -> list[int]:
    if not slugs:
        return []
    result = await db.execute(select(Interest).where(Interest.slug.in_(slugs)))
    return [i.id for i in result.scalars().all()]


async def _build_me_response(user_id: uuid.UUID, db: AsyncSession) -> MeResponse:
    # 1. User row — needed for email (single query)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # 2. Profile + grade + course + interests — 1 round-trip via selectinload in repo
    profile = await UserProfileRepository(db).get_by_id(user_id)
    grade_name: Optional[str] = profile.grade.name if profile and profile.grade else None
    course_name: Optional[str] = profile.course.name if profile and profile.course else None
    grade_level_parts = [p for p in [grade_name, course_name] if p]
    grade_level = " · ".join(grade_level_parts) if grade_level_parts else None
    interest_slugs = (
        [si.interest.slug for si in profile.interests if si.interest]
        if profile else []
    )

    # 3. Classroom — one joined query; load_only avoids SELECT * on classrooms (fewer
    # columns) so /auth/me keeps working if optional classroom columns lag migrations.
    cls_result = await db.execute(
        select(Classroom)
        .options(load_only(Classroom.id, Classroom.name, Classroom.code))
        .join(ClassroomStudent, Classroom.id == ClassroomStudent.classroom_id)
        .where(ClassroomStudent.student_id == user_id)
        .limit(1)
    )
    classroom = cls_result.scalar_one_or_none()

    return MeResponse(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        name=user.name,
        grade_level=grade_level,
        grade=grade_name,
        course=course_name,
        interests=interest_slugs,
        classroom_id=str(classroom.id) if classroom else None,
        classroom_name=classroom.name if classroom else None,
        classroom_code=classroom.code if classroom else None,
        district=user.district,
        school=user.school,
    )


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
        db, email=req.email, password=req.password, role=req.role, name=req.name, commit=False,
    )

    if req.role == "student" and req.interests:
        interest_ids = await _resolve_interest_ids(req.interests, db)
        await UserProfileRepository(db).set_interests(user.id, interest_ids)

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
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> MeResponse:
    return await _build_me_response(auth.user_id, db)


# ── Profile Update ─────────────────────────────────────────────────────────

@router.patch("/profile", response_model=MeResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
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
        interest_ids = await _resolve_interest_ids(req.interests, db)
        await repo.set_interests(auth.user_id, interest_ids)

    logger.info("profile_updated", user_id=str(auth.user_id))
    return await _build_me_response(auth.user_id, db)


# ── Account update (email / password) ─────────────────────────────────────


@router.put("/me", response_model=MeResponse)
@router.patch("/me", response_model=MeResponse)
async def update_account(
    req: AccountUpdateRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> MeResponse:
    """Update the authenticated user's email and/or password."""
    result = await db.execute(select(User).where(User.id == auth.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

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
    logger.info("account_updated", user_id=str(auth.user_id))
    return await _build_me_response(auth.user_id, db)


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
