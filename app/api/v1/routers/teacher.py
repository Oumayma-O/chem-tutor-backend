"""
Teacher dashboard API — classes, roster, live presence, session history.

GET  /teacher/classes
POST /teacher/classes
GET  /teacher/classes/{classroom_id}/roster
GET  /teacher/classes/{classroom_id}/live
GET  /teacher/classes/{classroom_id}/live/stream
GET  /teacher/classes/{classroom_id}/sessions
GET  /teacher/classes/{classroom_id}/sessions/{session_id}/practice-analytics
GET  /teacher/classes/{classroom_id}/sessions/{session_id}/practice-analytics/stream
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, get_auth_context_from_query, require_teacher, require_teacher_or_admin
from app.api.v1.classroom_access import ensure_student_enrolled, ensure_teacher_classroom
from app.domain.schemas.live_session import LiveSessionOut, LiveSessionPublishRequest
from app.core.sse_stream import SSE_STREAM_HEADERS, sse_json_poll_events
from app.infrastructure.database.connection import get_db, sse_poll_session
from app.services.classroom import live_session as live_session_svc
from app.domain.schemas.classrooms import ClassroomOut
from app.domain.schemas.dashboards import (
    ClassroomSessionOut,
    LiveStudentEntry,
    RosterStudentEntry,
    StudentAnalyticsOut,
    TeacherClassCreate,
    TeacherClassOut,
    TeacherClassPatch,
    TimedPracticeAnalytics,
)
from app.infrastructure.database.models import ClassroomSession
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository
from app.services.mastery_service import MasteryService
from app.services.teacher.service import TeacherService

router = APIRouter(prefix="/teacher")


def _build_teacher_service(db: AsyncSession) -> TeacherService:
    mastery = MasteryService(
        mastery_repo=MasteryRepository(db),
        attempt_repo=AttemptRepository(db),
        misconception_repo=MisconceptionRepository(db),
    )
    return TeacherService(db, mastery)


def _teacher_service(db: AsyncSession = Depends(get_db)) -> TeacherService:
    return _build_teacher_service(db)


def _teacher_service_from_session(db: AsyncSession) -> TeacherService:
    return _build_teacher_service(db)


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
    unit_id: str | None = Query(default=None, description="Scope mastery to this unit. Omit or 'all' for global."),
    lesson_index: int | None = Query(default=None, ge=0, description="Scope mastery to this lesson within the unit."),
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
    db: AsyncSession = Depends(get_db),
) -> list[RosterStudentEntry]:
    require_teacher_or_admin(auth)
    await ensure_teacher_classroom(db, auth, classroom_id)
    teacher_id = auth.user_id if auth.role == "teacher" else None
    filter_unit = unit_id if (unit_id and unit_id != "all") else None
    try:
        return await svc.get_roster(classroom_id, teacher_id, unit_id=filter_unit, lesson_index=lesson_index)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


_roster_adapter = TypeAdapter(list[RosterStudentEntry])


@router.get("/classes/{classroom_id}/roster/stream")
async def stream_class_roster(
    classroom_id: uuid.UUID,
    unit_id: str | None = Query(default=None, description="Scope mastery to this unit."),
    lesson_index: int | None = Query(default=None, ge=0, description="Scope mastery to this lesson."),
    auth: AuthContext = Depends(get_auth_context_from_query),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """SSE: push roster with mastery scores when they change."""
    require_teacher_or_admin(auth)
    await ensure_teacher_classroom(db, auth, classroom_id)
    teacher_id: uuid.UUID | None = auth.user_id if auth.role == "teacher" else None
    filter_unit = unit_id if (unit_id and unit_id != "all") else None

    async def event_stream():
        async def poll_json() -> str:
            async with sse_poll_session() as sdb:
                ssvc = _teacher_service_from_session(sdb)
                rows = await ssvc.get_roster(
                    classroom_id, teacher_id, unit_id=filter_unit, lesson_index=lesson_index,
                )
            return _roster_adapter.dump_json(rows).decode()

        async for chunk in sse_json_poll_events(
            poll_json=poll_json,
            interval_seconds=5.0,
            log_event="teacher_roster_sse_error",
        ):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=dict(SSE_STREAM_HEADERS),
    )


@router.get("/classes/{classroom_id}/students/{student_id}/analytics", response_model=StudentAnalyticsOut)
async def get_student_analytics(
    classroom_id: uuid.UUID,
    student_id: uuid.UUID,
    unit_id: str | None = Query(default=None, description="Filter by chapter/unit. Omit or 'all' for all chapters."),
    lesson_index: int | None = Query(default=None, ge=0, description="Scope to a specific lesson within the unit."),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
    db: AsyncSession = Depends(get_db),
) -> StudentAnalyticsOut:
    """Return recent attempts + mastery snapshot for one student (teacher-only).

    Pass ?unit_id=<id> to scope to a chapter; add ?lesson_index=<n> to further narrow to one lesson.
    Supports pagination via ?limit=20&offset=0.
    """
    await ensure_teacher_classroom(db, auth, classroom_id)
    await ensure_student_enrolled(db, student_id, classroom_id)

    filter_unit = unit_id if (unit_id and unit_id != "all") else None
    return await svc.get_student_analytics(
        student_id,
        unit_id=filter_unit,
        lesson_index=lesson_index,
        limit=limit,
        offset=offset,
    )


@router.get("/classes/{classroom_id}/live", response_model=list[LiveStudentEntry])
async def get_class_live(
    classroom_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
    db: AsyncSession = Depends(get_db),
    within_seconds: int = Query(default=60, ge=10, le=300),
) -> list[LiveStudentEntry]:
    require_teacher_or_admin(auth)
    await ensure_teacher_classroom(db, auth, classroom_id)
    teacher_id = auth.user_id if auth.role == "teacher" else None
    try:
        return await svc.get_live(classroom_id, teacher_id, within_seconds)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


_live_rows_adapter = TypeAdapter(list[LiveStudentEntry])


@router.get("/classes/{classroom_id}/live/stream")
async def stream_class_live(
    classroom_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context_from_query),
    db: AsyncSession = Depends(get_db),
    within_seconds: int = Query(default=60, ge=10, le=300),
) -> StreamingResponse:
    """SSE: push live presence rows when they change (replaces teacher polling)."""
    require_teacher_or_admin(auth)
    await ensure_teacher_classroom(db, auth, classroom_id)
    teacher_id = auth.user_id if auth.role == "teacher" else None
    async with sse_poll_session() as db:
        svc = _teacher_service_from_session(db)
        try:
            await svc.get_live(classroom_id, teacher_id, within_seconds)
        except LookupError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    async def event_stream():
        async def poll_json() -> str:
            async with sse_poll_session() as sdb:
                ssvc = _teacher_service_from_session(sdb)
                rows = await ssvc.get_live(classroom_id, teacher_id, within_seconds)
            return _live_rows_adapter.dump_json(rows).decode()

        async for chunk in sse_json_poll_events(
            poll_json=poll_json,
            log_event="teacher_live_sse_error",
        ):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=dict(SSE_STREAM_HEADERS),
    )


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


# ── Session history ────────────────────────────────────────────


@router.get("/classes/{classroom_id}/sessions", response_model=list[ClassroomSessionOut])
async def list_classroom_sessions(
    classroom_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> list[ClassroomSessionOut]:
    """Paginated list of persisted sessions (timed practice / exit ticket / both)."""
    await ensure_teacher_classroom(db, auth, classroom_id)

    result = await db.execute(
        select(ClassroomSession)
        .where(ClassroomSession.classroom_id == classroom_id)
        .order_by(ClassroomSession.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.scalars().all()
    return [
        ClassroomSessionOut(
            id=r.id,
            classroom_id=r.classroom_id,
            session_type=r.session_type,
            exit_ticket_id=r.exit_ticket_id,
            unit_id=r.unit_id,
            lesson_index=r.lesson_index,
            timed_practice_minutes=r.timed_practice_minutes,
            started_at=r.started_at,
            ended_at=r.ended_at,
        )
        for r in rows
    ]


@router.get(
    "/classes/{classroom_id}/sessions/{session_id}/practice-analytics",
    response_model=TimedPracticeAnalytics,
)
async def get_timed_practice_analytics(
    classroom_id: uuid.UUID,
    session_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
    svc: TeacherService = Depends(_teacher_service),
) -> TimedPracticeAnalytics:
    """Per-student, per-level problem attempt stats for a specific timed-practice session."""
    await ensure_teacher_classroom(db, auth, classroom_id)

    teacher_id: uuid.UUID | None = auth.user_id if auth.role == "teacher" else None
    out = await svc.get_timed_practice_analytics(classroom_id, session_id, teacher_id)
    if out is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return out


@router.get("/classes/{classroom_id}/sessions/{session_id}/practice-analytics/stream")
async def stream_timed_practice_analytics(
    classroom_id: uuid.UUID,
    session_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context_from_query),
) -> StreamingResponse:
    """SSE: push timed practice analytics when attempt counts change."""
    teacher_id: uuid.UUID | None = auth.user_id if auth.role == "teacher" else None
    async with sse_poll_session() as db:
        await ensure_teacher_classroom(db, auth, classroom_id)
        ssvc = _teacher_service_from_session(db)
        if await ssvc.get_timed_practice_analytics(classroom_id, session_id, teacher_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    async def event_stream():
        async def poll_json() -> str | None:
            async with sse_poll_session() as sdb:
                ssvc = _teacher_service_from_session(sdb)
                out = await ssvc.get_timed_practice_analytics(classroom_id, session_id, teacher_id)
            if out is None:
                return None
            return out.model_dump_json()

        async for chunk in sse_json_poll_events(
            poll_json=poll_json,
            log_event="teacher_practice_analytics_sse_error",
        ):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=dict(SSE_STREAM_HEADERS),
    )
