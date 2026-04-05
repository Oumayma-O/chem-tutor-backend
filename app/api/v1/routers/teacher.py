"""
Teacher dashboard API — classes, roster, live presence.

GET  /teacher/classes
POST /teacher/classes
GET  /teacher/classes/{classroom_id}/roster
GET  /teacher/classes/{classroom_id}/live
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_teacher
from app.domain.schemas.live_session import LiveSessionOut, LiveSessionPublishRequest
from app.infrastructure.database.connection import get_db
from app.services.classroom import live_session as live_session_svc
from app.domain.schemas.classrooms import ClassroomOut
from app.domain.schemas.dashboards import (
    LiveStudentEntry,
    RosterStudentEntry,
    TeacherClassCreate,
    TeacherClassOut,
)
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository
from app.services.mastery_service import MasteryService
from app.services.teacher.service import TeacherService

router = APIRouter(prefix="/teacher")


def _teacher_service(db: AsyncSession = Depends(get_db)) -> TeacherService:
    mastery = MasteryService(
        mastery_repo=MasteryRepository(db),
        attempt_repo=AttemptRepository(db),
        misconception_repo=MisconceptionRepository(db),
    )
    return TeacherService(db, mastery)


@router.get("/classes", response_model=list[TeacherClassOut])
async def list_teacher_classes(
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
) -> list[TeacherClassOut]:
    require_teacher(auth)
    return await svc.list_classes(auth.user_id)


@router.post("/classes", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
async def create_teacher_class(
    req: TeacherClassCreate,
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
) -> ClassroomOut:
    require_teacher(auth)
    return await svc.create_class(req.name, auth.user_id, req.unit_id)


@router.get("/classes/{classroom_id}/roster", response_model=list[RosterStudentEntry])
async def get_class_roster(
    classroom_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
) -> list[RosterStudentEntry]:
    require_teacher(auth)
    try:
        return await svc.get_roster(classroom_id, auth.user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/classes/{classroom_id}/live", response_model=list[LiveStudentEntry])
async def get_class_live(
    classroom_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
    within_seconds: int = Query(default=60, ge=10, le=300),
) -> list[LiveStudentEntry]:
    require_teacher(auth)
    try:
        return await svc.get_live(classroom_id, auth.user_id, within_seconds)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.post(
    "/classrooms/{classroom_id}/live-session/publish",
    response_model=LiveSessionOut,
)
async def publish_classroom_live_session(
    classroom_id: uuid.UUID,
    req: LiveSessionPublishRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> LiveSessionOut:
    """Publish exit ticket (+ optional timed practice) for student live-session polling."""
    require_teacher(auth)
    try:
        return await live_session_svc.publish_live_session(
            db,
            classroom_id,
            auth.user_id,
            req.exit_ticket_id,
            req.timed_practice_enabled,
            req.timed_practice_minutes,
            req.unit_id,
            req.lesson_index,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.post(
    "/classrooms/{classroom_id}/live-session/stop",
    response_model=LiveSessionOut,
)
async def stop_classroom_live_session(
    classroom_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> LiveSessionOut:
    require_teacher(auth)
    try:
        return await live_session_svc.stop_live_session(db, classroom_id, auth.user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
