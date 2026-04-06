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
    StudentAnalyticsOut,
    StudentAttemptOut,
    TeacherClassCreate,
    TeacherClassOut,
    TeacherClassPatch,
)
from app.infrastructure.database.repositories.attempt_repo import AttemptRepository
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


@router.patch("/classes/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def patch_teacher_class(
    classroom_id: uuid.UUID,
    req: TeacherClassPatch,
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
) -> None:
    require_teacher(auth)
    try:
        await svc.patch_class(classroom_id, auth.user_id, req)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


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


@router.get("/classes/{classroom_id}/students/{student_id}/analytics", response_model=StudentAnalyticsOut)
async def get_student_analytics(
    classroom_id: uuid.UUID,
    student_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
    db: AsyncSession = Depends(get_db),
) -> StudentAnalyticsOut:
    """Return recent attempts + mastery snapshot for one student (teacher-only)."""
    require_teacher(auth)
    try:
        classroom = await svc._classrooms.get_by_id_with_students(classroom_id)
    except Exception:
        classroom = None
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    if classroom.teacher_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class.")

    snap = await svc._mastery.get_student_mastery_snapshot(student_id, classroom.unit_id)

    attempt_repo = AttemptRepository(db)
    # Fetch up to 10 most recent attempts across all lessons for this student/unit.
    from sqlalchemy import select
    from app.infrastructure.database.models.learning import ProblemAttempt
    result = await db.execute(
        select(ProblemAttempt)
        .where(ProblemAttempt.user_id == student_id)
        .order_by(ProblemAttempt.started_at.desc())
        .limit(10)
    )
    rows = result.scalars().all()

    return StudentAnalyticsOut(
        student_id=student_id,
        overall_mastery=snap.overall_mastery,
        category_scores=snap.category_scores.model_dump() if hasattr(snap.category_scores, "model_dump") else dict(snap.category_scores),
        recent_attempts=[
            StudentAttemptOut(
                id=r.id,
                unit_id=r.unit_id,
                lesson_index=r.lesson_index,
                level=r.level,
                score=r.score,
                is_complete=r.is_complete,
                started_at=r.started_at,
            )
            for r in rows
        ],
        lessons_with_data=snap.lessons_with_data,
    )


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
