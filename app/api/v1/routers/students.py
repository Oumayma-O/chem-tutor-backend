"""
Students router — user profile and interest management.

POST /students/profile         → create or update student profile
GET  /students/{id}/profile    → get profile
GET  /students/{id}/context    → get AI-ready context (grade_level, interests)
GET  /students/lookup/grades   → list grade options
GET  /students/lookup/courses  → list course options
GET  /students/lookup/interests → list interest options
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_self
from app.core.logging import get_logger
from app.domain.schemas.students import (
    CourseOut,
    GradeOut,
    InterestOut,
    StudentContextOut,
    UserProfileCreate,
    UserProfileOut,
    UserProfileUpdate,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import UserProfile
from app.infrastructure.database.repositories.student_repo import (
    CourseRepository,
    GradeRepository,
    InterestRepository,
    UserProfileRepository,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/students")


# ── Lookup tables ──────────────────────────────────────────────

@router.get("/lookup/grades", response_model=list[GradeOut])
async def list_grades(db: AsyncSession = Depends(get_db)) -> list[GradeOut]:
    repo = GradeRepository(db)
    grades = await repo.get_all()
    return [GradeOut(id=g.id, name=g.name, sort_order=g.sort_order) for g in grades]


@router.get("/lookup/courses", response_model=list[CourseOut])
async def list_courses(db: AsyncSession = Depends(get_db)) -> list[CourseOut]:
    repo = CourseRepository(db)
    courses = await repo.get_all()
    return [CourseOut(id=c.id, name=c.name, grade_id=c.grade_id) for c in courses]


@router.get("/lookup/interests", response_model=list[InterestOut])
async def list_interests(db: AsyncSession = Depends(get_db)) -> list[InterestOut]:
    repo = InterestRepository(db)
    interests = await repo.get_all()
    return [InterestOut(id=i.id, slug=i.slug, label=i.label, icon=i.icon) for i in interests]


# ── Profile ────────────────────────────────────────────────────

@router.post("/profile", response_model=UserProfileOut, status_code=status.HTTP_201_CREATED)
async def upsert_profile(
    req: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> UserProfileOut:
    require_self(req.user_id, auth)
    repo = UserProfileRepository(db)

    profile = UserProfile(
        user_id=req.user_id,
        role=req.role,
        name=req.name,
        grade_id=req.grade_id,
        course_id=req.course_id,
    )
    saved = await repo.upsert(profile)

    if req.interest_ids:
        await repo.set_interests(req.user_id, req.interest_ids)

    return await _build_profile_out(saved.user_id, db)


@router.patch("/profile/{user_id}", response_model=UserProfileOut)
async def update_profile(
    user_id: uuid.UUID,
    req: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> UserProfileOut:
    require_self(user_id, auth)
    repo = UserProfileRepository(db)
    profile = await repo.get_by_id(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    if req.name is not None:
        profile.name = req.name
    if req.grade_id is not None:
        profile.grade_id = req.grade_id
    if req.course_id is not None:
        profile.course_id = req.course_id
    await db.flush()

    if req.interest_ids is not None:
        await repo.set_interests(user_id, req.interest_ids)

    return await _build_profile_out(user_id, db)


@router.get("/profile/{user_id}", response_model=UserProfileOut)
async def get_profile(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> UserProfileOut:
    require_self(user_id, auth)
    return await _build_profile_out(user_id, db)


@router.get("/{user_id}/context", response_model=StudentContextOut)
async def get_student_context(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> StudentContextOut:
    """
    Returns the AI-ready context for a student:
    grade_level, course, interests (slugs for context_tag), interest_labels.
    Used by the frontend when calling /tutor/generate-problem.
    """
    require_self(user_id, auth)
    repo = UserProfileRepository(db)
    profile = await repo.get_by_id(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    interests_slugs = [
        si.interest.slug for si in (profile.interests or []) if si.interest
    ]
    interest_labels = [
        si.interest.label for si in (profile.interests or []) if si.interest
    ]

    return StudentContextOut(
        user_id=user_id,
        grade_level=profile.grade.name if profile.grade else None,
        course=profile.course.name if profile.course else None,
        interests=interests_slugs,
        interest_labels=interest_labels,
    )


# ── Helper ─────────────────────────────────────────────────────

async def _build_profile_out(user_id: uuid.UUID, db: AsyncSession) -> UserProfileOut:
    repo = UserProfileRepository(db)
    profile = await repo.get_by_id(user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")

    return UserProfileOut(
        user_id=profile.user_id,
        role=profile.role,
        name=profile.name,
        grade=GradeOut(
            id=profile.grade.id,
            name=profile.grade.name,
            sort_order=profile.grade.sort_order,
        ) if profile.grade else None,
        course=CourseOut(
            id=profile.course.id,
            name=profile.course.name,
            grade_id=profile.course.grade_id,
        ) if profile.course else None,
        interests=[
            InterestOut(
                id=si.interest.id,
                slug=si.interest.slug,
                label=si.interest.label,
                icon=si.interest.icon,
            )
            for si in (profile.interests or [])
            if si.interest
        ],
        created_at=profile.created_at,
    )
