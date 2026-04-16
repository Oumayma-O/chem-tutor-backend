"""
Units router — content catalog management.

GET  /units       → list all active units (filtered by grade/course)
GET  /units/{id}  → unit detail with lessons
POST /units       → create unit (admin only)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_admin
from app.core.logging import get_logger
from app.domain.schemas.standards import StandardOut
from app.domain.schemas.units import (
    LessonCreate,
    LessonOut,
    UnitCreate,
    UnitListItem,
    UnitOut,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import Lesson, LessonStandard, Standard, Unit, UnitLesson
from app.infrastructure.database.repositories.unit_repo import (
    LessonRepository,
    StandardRepository,
    UnitRepository,
)
from app.services.unit_catalog_service import create_unit_with_lessons

logger = get_logger(__name__)
router = APIRouter(prefix="/units")


# ── Unit Endpoints ─────────────────────────────────────────────

@router.get("", response_model=list[UnitListItem])
async def list_units(
    grade_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[UnitListItem]:
    repo = UnitRepository(db)
    units = await repo.get_all_active(grade_id=grade_id, course_id=course_id)
    return [
        UnitListItem(
            id=u.id,
            title=u.title or "",
            description=u.description or "",
            icon=u.icon or "📚",
            gradient=u.gradient,
            grade_id=u.grade_id,
            course_id=u.course_id,
            course_name=u.course.name if u.course else None,
            sort_order=u.sort_order,
            is_active=u.is_active,
            is_coming_soon=u.is_coming_soon,
            lesson_count=len(u.unit_lessons),
            skill_count=sum(len(ul.lesson.objectives or []) for ul in u.unit_lessons),
            lesson_titles=[ul.lesson.title for ul in sorted(u.unit_lessons, key=lambda x: x.lesson_order)],
        )
        for u in units
    ]


@router.get("/{unit_id}", response_model=UnitOut)
async def get_unit(
    unit_id: str,
    db: AsyncSession = Depends(get_db),
) -> UnitOut:
    repo = UnitRepository(db)
    unit = await repo.get_by_id(unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found.")

    lessons_out = []
    for ul in sorted(unit.unit_lessons, key=lambda x: x.lesson_order):
        l = ul.lesson
        stds = [
            StandardOut(
                code=ls.standard.code,
                framework=ls.standard.framework,
                title=ls.standard.title or None,
                description=ls.standard.description,
                category=ls.standard.category,
                is_core=ls.standard.is_core,
            )
            for ls in (l.standards or [])
            if ls.standard
        ]
        lessons_out.append(
            LessonOut(
                id=l.id,
                unit_id=unit.id,
                title=l.title,
                description=l.description,
                lesson_index=ul.lesson_order,
                slug=l.slug,
                is_ap_only=l.is_ap_only,
                objectives=l.objectives or [],
                key_equations=l.key_equations or [],
                key_rules=l.key_rules or [],
                misconceptions=l.misconceptions or [],
                blueprint=l.blueprint or "solver",
                has_simulation=l.has_simulation,
                standards=stds,
                is_active=l.is_active,
                required_tools=l.required_tools or [],
            )
        )

    return UnitOut(
        id=unit.id,
        title=unit.title,
        description=unit.description,
        icon=unit.icon,
        gradient=unit.gradient,
        grade_id=unit.grade_id,
        course_id=unit.course_id,
        course_name=unit.course.name if unit.course else None,
        sort_order=unit.sort_order,
        is_active=unit.is_active,
        is_coming_soon=unit.is_coming_soon,
        lessons=lessons_out,
    )


@router.post("", response_model=UnitOut, status_code=status.HTTP_201_CREATED)
async def create_unit(
    req: UnitCreate,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> UnitOut:
    require_admin(auth)
    await create_unit_with_lessons(db, req)
    return await get_unit(req.id, db)


