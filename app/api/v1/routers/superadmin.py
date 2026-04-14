"""
Super Admin — create and manage school admin accounts.

POST   /superadmin/create-school-admin
GET    /superadmin/school-admins
DELETE /superadmin/school-admins/{admin_id}
PATCH  /superadmin/school-admins/{admin_id}
"""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_superadmin
from app.core.logging import get_logger
from app.domain.schemas.dashboards import EngagementAnalyticsOut, SuperadminStats
from app.domain.schemas.enums import USDistrict
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import User, UserProfile
from app.services.admin.service import AdminService
from app.services.auth.security import hash_password
from app.services.auth.user_factory import create_user

logger = get_logger(__name__)
router = APIRouter(prefix="/superadmin")


class CreateSchoolAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1, max_length=200)
    district: USDistrict
    school: str = Field(min_length=1, max_length=300)


class CreatedUserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    name: str
    district: str | None = None
    school: str | None = None


@router.post("/create-school-admin", response_model=CreatedUserResponse, status_code=status.HTTP_201_CREATED)
async def create_school_admin(
    req: CreateSchoolAdminRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> CreatedUserResponse:
    require_superadmin(auth)

    existing = await db.scalar(select(User).where(User.email == req.email.lower().strip()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

    user = await create_user(
        db,
        email=req.email,
        password=req.password,
        role="admin",
        name=req.full_name,
        district=req.district.value,
        school=req.school,
    )

    logger.info("school_admin_created", admin_id=str(user.id), by=str(auth.user_id))
    return CreatedUserResponse(
        user_id=str(user.id),
        email=user.email,
        role=user.role,
        name=user.name,
        district=user.district,
        school=user.school,
    )


class SchoolAdminOut(BaseModel):
    user_id: uuid.UUID
    name: str
    email: str
    district: str | None = None
    school: str | None = None
    is_active: bool
    created_at: str


class PatchSchoolAdminRequest(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    district: str | None = Field(default=None, max_length=300)
    school: str | None = Field(default=None, max_length=300)
    is_active: bool | None = None


@router.get("/school-admins", response_model=list[SchoolAdminOut])
async def list_school_admins(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[SchoolAdminOut]:
    require_superadmin(auth)
    result = await db.execute(
        select(User).where(User.role == "admin").order_by(User.created_at.desc())
    )
    admins = result.scalars().all()
    return [
        SchoolAdminOut(
            user_id=a.id,
            name=a.name,
            email=a.email,
            district=a.district,
            school=a.school,
            is_active=a.is_active,
            created_at=a.created_at.isoformat(),
        )
        for a in admins
    ]


@router.delete("/school-admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_admin(
    admin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    require_superadmin(auth)
    user = await db.scalar(select(User).where(User.id == admin_id, User.role == "admin"))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School admin not found.")
    await db.delete(user)
    await db.commit()
    logger.info("school_admin_deleted", admin_id=str(admin_id), by=str(auth.user_id))


@router.patch("/school-admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_school_admin(
    admin_id: uuid.UUID,
    body: PatchSchoolAdminRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    require_superadmin(auth)
    user = await db.scalar(select(User).where(User.id == admin_id, User.role == "admin"))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School admin not found.")
    if body.name is not None:
        user.name = body.name
    if body.district is not None:
        user.district = body.district
    if body.school is not None:
        user.school = body.school
    if body.is_active is not None:
        user.is_active = body.is_active
    await db.commit()
    logger.info("school_admin_patched", admin_id=str(admin_id), by=str(auth.user_id))


@router.get("/analytics/engagement", response_model=EngagementAnalyticsOut)
async def superadmin_engagement_analytics(
    scope: Literal["teacher", "school", "district"] = Query(default="district"),
    target: str = Query(..., description="Teacher UUID, school name, or district name depending on scope"),
    timeframe: Literal["last_7_days", "last_30_days", "last_90_days"] = Query(default="last_30_days"),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> EngagementAnalyticsOut:
    """Platform-wide engagement analytics. Superadmins can query any scope."""
    require_superadmin(auth)
    return await AdminService(db).get_engagement_analytics(
        scope=scope,
        target=target,
        timeframe=timeframe,
        requesting_school=None,  # no school restriction for superadmin
    )


@router.get("/stats", response_model=SuperadminStats)
async def superadmin_stats(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> SuperadminStats:
    """Global platform stats: admins, teachers, active classes, enrolled students,
    distinct districts and schools derived from admin accounts."""
    require_superadmin(auth)
    return await AdminService(db).get_superadmin_stats()
