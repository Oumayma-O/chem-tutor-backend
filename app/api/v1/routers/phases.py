"""
Phases router — curriculum phase management and classroom customisation.

GET  /phases                              → list phases (optionally by course)
POST /phases                              → create phase (admin only)
PATCH /phases/{phase_id}                  → update phase name / order / color
DELETE /phases/{phase_id}                 → delete phase

GET  /phases/curriculum                   → fetch full curriculum (global or classroom)
POST /phases/curriculum/overrides         → bulk upsert classroom overrides
DELETE /phases/curriculum/overrides/{unit_id} → remove one override
POST /phases/curriculum/sync              → pull new global units into a classroom
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_admin
from app.core.logging import get_logger
from app.domain.schemas.phases import (
    BulkOverrideRequest,
    CurriculumResponse,
    OverrideOut,
    PhaseCreate,
    PhaseOut,
    PhaseUpdate,
    SyncResult,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import Phase
from app.infrastructure.database.repositories.phase_repo import (
    ClassroomCurriculumRepository,
    PhaseRepository,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/phases")


# ── Phase CRUD ────────────────────────────────────────────────

@router.get("", response_model=list[PhaseOut])
async def list_phases(
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[PhaseOut]:
    repo = PhaseRepository(db)
    phases = await repo.get_all(course_id=course_id)
    return [PhaseOut.model_validate(p) for p in phases]


@router.post("", response_model=PhaseOut, status_code=status.HTTP_201_CREATED)
async def create_phase(
    req: PhaseCreate,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PhaseOut:
    require_admin(auth)
    repo = PhaseRepository(db)
    phase = await repo.create(Phase(
        name=req.name,
        description=req.description,
        course_id=req.course_id,
        sort_order=req.sort_order,
        color=req.color,
    ))
    return PhaseOut.model_validate(phase)


@router.patch("/{phase_id}", response_model=PhaseOut)
async def update_phase(
    phase_id: int,
    req: PhaseUpdate,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> PhaseOut:
    require_admin(auth)
    repo = PhaseRepository(db)
    phase = await repo.get_by_id(phase_id)
    if phase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found.")
    phase = await repo.update(phase, **req.model_dump(exclude_none=True))
    return PhaseOut.model_validate(phase)


@router.delete("/{phase_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_phase(
    phase_id: int,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    require_admin(auth)
    repo = PhaseRepository(db)
    phase = await repo.get_by_id(phase_id)
    if phase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phase not found.")
    await repo.delete(phase)


# ── Curriculum fetch ──────────────────────────────────────────

@router.get("/curriculum", response_model=CurriculumResponse)
async def get_curriculum(
    course_id: int | None = Query(default=None, description="Filter by course"),
    classroom_id: uuid.UUID | None = Query(
        default=None,
        description="Classroom UUID — if provided, applies teacher overrides",
    ),
    db: AsyncSession = Depends(get_db),
) -> CurriculumResponse:
    """
    Fetch the full phase-grouped curriculum.

    - No classroom_id  → returns global default ordering.
    - With classroom_id → merges teacher overrides: hidden units removed,
      phase / order overrides applied.
    """
    repo = ClassroomCurriculumRepository(db)
    data = await repo.fetch_curriculum(
        course_id=course_id,
        classroom_id=classroom_id,
    )
    return CurriculumResponse(**data)


# ── Classroom overrides ───────────────────────────────────────

@router.post(
    "/curriculum/overrides",
    response_model=list[OverrideOut],
    status_code=status.HTTP_200_OK,
)
async def upsert_overrides(
    classroom_id: uuid.UUID = Query(...),
    req: BulkOverrideRequest = ...,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[OverrideOut]:
    """
    Upsert one or more overrides for a classroom.
    Missing fields (phase_id, custom_order) default to None = use global defaults.
    """
    require_admin(auth)
    repo = ClassroomCurriculumRepository(db)
    results = []
    for item in req.overrides:
        override = await repo.upsert_override(
            classroom_id=classroom_id,
            unit_id=item.unit_id,
            phase_id=item.phase_id,
            custom_order=item.custom_order,
            is_hidden=item.is_hidden,
        )
        results.append(override)
    return [
        OverrideOut(
            id=str(o.id),
            classroom_id=str(o.classroom_id),
            unit_id=o.unit_id,
            phase_id=o.phase_id,
            custom_order=o.custom_order,
            is_hidden=o.is_hidden,
        )
        for o in results
    ]


@router.delete(
    "/curriculum/overrides/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_override(
    unit_id: str,
    classroom_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    """Remove a single override — the unit reverts to global defaults."""
    require_admin(auth)
    repo = ClassroomCurriculumRepository(db)
    deleted = await repo.delete_override(classroom_id=classroom_id, unit_id=unit_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Override not found.")


@router.post("/curriculum/sync", response_model=SyncResult)
async def sync_curriculum(
    classroom_id: uuid.UUID = Query(...),
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> SyncResult:
    """
    'Sync with Global Default' — pull any newly added units from the global
    curriculum into the classroom's override table (with default values).
    Existing overrides are untouched.
    """
    require_admin(auth)
    repo = ClassroomCurriculumRepository(db)
    added, unchanged = await repo.sync_from_global(
        classroom_id=classroom_id,
        course_id=course_id,
    )
    logger.info("curriculum_synced", classroom_id=str(classroom_id), added=added)
    return SyncResult(added=added, unchanged=unchanged)
