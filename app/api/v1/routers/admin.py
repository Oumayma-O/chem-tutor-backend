"""
Admin dashboard — curriculum, AI logs, curated examples.

GET    /admin/chapters
POST   /admin/chapters
PATCH  /admin/units/{unit_id}
DELETE /admin/units/{unit_id}
GET    /admin/logs/generation
GET    /admin/stats
GET    /admin/teachers
GET    /admin/curated-problems
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_admin
from app.domain.schemas.dashboards import AdminTeacherOut, CuratedProblem, GenerationLogEntry, SystemStats
from app.domain.schemas.phases import CurriculumResponse
from app.domain.schemas.units import UnitCreate, UnitOut
from app.infrastructure.database.connection import get_db
from app.services.admin.service import AdminService
from app.services.unit_catalog_service import create_unit_with_lessons

router = APIRouter(prefix="/admin")


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


@router.get("/stats", response_model=SystemStats)
async def admin_system_stats(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> SystemStats:
    require_admin(auth)
    return await AdminService(db).get_system_stats()


@router.get("/teachers", response_model=list[AdminTeacherOut])
async def admin_list_teachers(
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[AdminTeacherOut]:
    require_admin(auth)
    return await AdminService(db).list_teachers()


@router.get("/curated-problems", response_model=list[CuratedProblem])
async def admin_curated_problems(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[CuratedProblem]:
    require_admin(auth)
    return await AdminService(db).get_curated_problems(limit, offset)
