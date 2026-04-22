"""
Admin dashboard — curriculum, AI logs, curated examples, teacher management.

GET    /admin/chapters
POST   /admin/chapters
PATCH  /admin/units/{unit_id}
DELETE /admin/units/{unit_id}
GET    /admin/logs/generation
GET    /admin/stats
GET    /admin/teachers
POST   /admin/create-teacher
GET    /admin/curated-problems
"""

import uuid

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_admin, require_role
from app.core.logging import get_logger
from app.domain.schemas.analytics import AggregateAnalyticsResponse
from app.domain.schemas.dashboards import AdminStats, AdminTeacherOut, CuratedProblem, EngagementAnalyticsOut, GenerationLogEntry, SystemStats
from app.domain.schemas.phases import CurriculumResponse
from app.domain.schemas.units import UnitCreate, UnitOut
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import User, UserProfile
from app.services.admin.service import AdminService
from app.services.auth.security import hash_password
from app.services.auth.user_factory import create_user
from app.services.unit_catalog_service import create_unit_with_lessons

logger = get_logger(__name__)
router = APIRouter(prefix="/admin")


async def _get_admin_user(db: AsyncSession, auth: AuthContext) -> User:
    """Fetch the admin's User row. Raises 404 if missing."""
    user = await db.scalar(select(User).where(User.id == auth.user_id))
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin user not found.")
    return user


async def _get_admin_school(db: AsyncSession, auth: AuthContext) -> str | None:
    """Return the admin's school for scoping. Superadmins get None (no restriction)."""
    if auth.role == "superadmin":
        return None
    admin_user = await _get_admin_user(db, auth)
    return admin_user.school


class AdminUnitPatch(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    is_active: bool | None = None


@router.get("/chapters", response_model=CurriculumResponse)
async def admin_list_curriculum(
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> CurriculumResponse:
    require_admin(auth)
    return await AdminService(db).get_curriculum(course_id)


@router.post("/chapters", response_model=UnitOut, status_code=status.HTTP_201_CREATED)
async def admin_create_chapter(
    req: UnitCreate,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> UnitOut:
    require_admin(auth)
    await create_unit_with_lessons(db, req)
    from app.api.v1.routers.units import get_unit
    return await get_unit(req.id, db)


@router.patch("/units/{unit_id}", response_model=UnitOut)
async def admin_patch_unit(
    unit_id: str,
    body: AdminUnitPatch,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> UnitOut:
    require_admin(auth)
    try:
        await AdminService(db).patch_unit(unit_id, body.title, body.description, body.is_active)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    from app.api.v1.routers.units import get_unit
    return await get_unit(unit_id, db)


@router.delete("/units/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_unit(
    unit_id: str,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    require_admin(auth)
    try:
        await AdminService(db).delete_unit(unit_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/logs/generation", response_model=list[GenerationLogEntry])
async def admin_generation_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    unit_id: str | None = None,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[GenerationLogEntry]:
    require_admin(auth)
    return await AdminService(db).get_generation_logs(limit, offset, unit_id)


@router.get("/stats", response_model=AdminStats)
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> AdminStats:
    """School-scoped stats for admins; platform-wide for superadmins."""
    require_admin(auth)
    school = await _get_admin_school(db, auth)
    return await AdminService(db).get_admin_stats(school)


class CreateTeacherRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1, max_length=200)


class CreatedTeacherResponse(BaseModel):
    user_id: str
    email: str
    role: str
    name: str
    district: str | None = None
    school: str | None = None


@router.post("/create-teacher", response_model=CreatedTeacherResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_teacher(
    req: CreateTeacherRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> CreatedTeacherResponse:
    """School admin creates a teacher — district/school inherited from the admin."""
    require_admin(auth)

    admin_user = await _get_admin_user(db, auth)

    existing = await db.scalar(select(User).where(User.email == req.email.lower().strip()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    user = await create_user(
        db,
        email=req.email,
        password=req.password,
        role="teacher",
        name=req.full_name,
        district=admin_user.district,
        school=admin_user.school,
    )

    logger.info("teacher_created_by_admin", teacher_id=str(user.id), admin_id=str(auth.user_id))
    return CreatedTeacherResponse(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        name=user.name,
        district=user.district,
        school=user.school,
    )


@router.get("/teachers", response_model=list[AdminTeacherOut])
async def admin_list_teachers(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[AdminTeacherOut]:
    require_admin(auth)
    school = await _get_admin_school(db, auth)
    return await AdminService(db).list_teachers(school=school)


class PatchTeacherRequest(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    is_active: bool | None = None


@router.delete("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_teacher(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    require_admin(auth)
    school = await _get_admin_school(db, auth)
    try:
        await AdminService(db).delete_teacher(teacher_id, school)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.patch("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_patch_teacher(
    teacher_id: uuid.UUID,
    body: PatchTeacherRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    require_admin(auth)
    school = await _get_admin_school(db, auth)
    try:
        await AdminService(db).patch_teacher(
            teacher_id, school, name=body.name, is_active=body.is_active
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/analytics/engagement", response_model=EngagementAnalyticsOut)
async def admin_engagement_analytics(
    scope: Literal["teacher", "school"] = Query(default="school"),
    target: str = Query(..., description="Teacher UUID for scope=teacher; school name for scope=school"),
    timeframe: Literal["last_7_days", "last_30_days", "last_90_days"] = Query(default="last_30_days"),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> EngagementAnalyticsOut:
    """Engagement analytics scoped to the admin's school.

    - ``scope=school`` returns aggregate data for all teachers in the admin's school.
    - ``scope=teacher`` returns data for a single teacher (must belong to admin's school).
    """
    require_admin(auth)
    admin_user = await _get_admin_user(db, auth)
    if not admin_user.school:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Admin account has no school set.",
        )
    return await AdminService(db).get_engagement_analytics(
        scope=scope,
        target=target if scope == "teacher" else admin_user.school,
        timeframe=timeframe,
        requesting_school=admin_user.school,
    )


@router.get("/analytics/aggregate", response_model=AggregateAnalyticsResponse)
async def admin_aggregate_analytics(
    district: str | None = Query(default=None),
    school: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> AggregateAnalyticsResponse:
    """Aggregate performance metrics grouped by district, school, or class.

    Superadmin: grouping resolved from filters (no filter→district, district→school,
    district+school→class). School admin: always groups by class within their school.
    """
    require_admin(auth)
    requesting_school = await _get_admin_school(db, auth)
    from app.services.aggregate_analytics_service import AggregateAnalyticsService
    return await AggregateAnalyticsService(db).get_aggregate(
        district=district,
        school=school,
        requesting_school=requesting_school,
        role=auth.role,
    )


@router.get("/curated-problems", response_model=list[CuratedProblem])
async def admin_curated_problems(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[CuratedProblem]:
    require_admin(auth)
    return await AdminService(db).get_curated_problems(limit, offset)
