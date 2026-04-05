"""
Auth router — native email/password authentication.

POST /auth/register  → create account + return JWT
POST /auth/login     → verify credentials + return JWT
GET  /auth/me        → return current user from JWT
PATCH /auth/profile  → update grade, course, interests
"""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context
from app.core.logging import get_logger
from app.domain.schemas.auth import (
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
from app.infrastructure.database.repositories.classroom_repo import ClassroomRepository
from app.infrastructure.database.repositories.student_repo import (
    CourseRepository,
    GradeRepository,
    UserProfileRepository,
)
from app.services.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)

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

    # 3. Classroom — one joined query instead of two serial fetches
    cls_result = await db.execute(
        select(Classroom)
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

    user = User(
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        role=req.role,
        name=req.name.strip(),
    )
    db.add(user)
    await db.flush()

    profile = UserProfile(user_id=user.id, role=req.role, name=req.name.strip())
    db.add(profile)
    await db.flush()

    # Resolve grade + course via repo (eliminates duplicated ilike logic)
    if req.grade is not None and req.grade.strip():
        grade_row = await GradeRepository(db).get_by_name(req.grade.strip())
        if grade_row:
            profile.grade_id = grade_row.id
    if req.course is not None and req.course.strip():
        course_row = await CourseRepository(db).get_by_name(req.course.strip())
        if course_row:
            profile.course_id = course_row.id

    if req.role == "student" and req.interests:
        interest_ids = await _resolve_interest_ids(req.interests, db)
        await UserProfileRepository(db).set_interests(user.id, interest_ids)

    if req.role == "teacher" and req.class_name:
        classroom = Classroom(
            name=req.class_name.strip(),
            teacher_id=user.id,
            code="",
        )
        await ClassroomRepository(db).create_with_code(classroom)

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

    await db.flush()

    if req.interests is not None:
        interest_ids = await _resolve_interest_ids(req.interests, db)
        await repo.set_interests(auth.user_id, interest_ids)

    logger.info("profile_updated", user_id=str(auth.user_id))
    return await _build_me_response(auth.user_id, db)
