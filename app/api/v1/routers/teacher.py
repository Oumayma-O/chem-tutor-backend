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
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, get_auth_context_from_query, require_teacher, require_teacher_or_admin
from app.api.v1.classroom_access import ensure_teacher_classroom
from app.domain.schemas.live_session import LiveSessionOut, LiveSessionPublishRequest
from app.core.sse_stream import SSE_STREAM_HEADERS, sse_json_poll_events
from app.infrastructure.database.connection import get_db, sse_poll_session
from app.services.classroom import live_session as live_session_svc
from app.domain.schemas.classrooms import ClassroomOut
from app.domain.schemas.dashboards import (
    ClassroomSessionOut,
    LevelStats,
    LiveStudentEntry,
    RosterStudentEntry,
    StudentAnalyticsOut,
    StudentAttemptOut,
    StudentTimedPracticeRow,
    TeacherClassCreate,
    TeacherClassOut,
    TeacherClassPatch,
    TimedPracticeAnalytics,
)
from app.infrastructure.database.models import ClassroomSession, User
from app.infrastructure.database.models.learning import ProblemAttempt
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository
from app.services.mastery_service import MasteryService
from app.services.teacher.service import TeacherService

router = APIRouter(prefix="/teacher")


# ── Helpers for student attempt metrics ────────────────────────────────────

def _compute_time_spent(attempt: ProblemAttempt) -> int:
    """Seconds between started_at and completed_at. 0 if incomplete or missing."""
    if not attempt.completed_at or not attempt.started_at:
        return 0
    delta = attempt.completed_at - attempt.started_at
    return max(0, int(delta.total_seconds()))


def _count_hints(step_log: list | dict | None) -> int:
    """Sum hints_used across all steps in the step_log JSONB array."""
    if not isinstance(step_log, list):
        return 0
    return sum(
        int(step.get("hints_used", 0) or 0)
        for step in step_log
        if isinstance(step, dict)
    )


def _count_reveals(step_log: list | dict | None) -> int:
    """Count steps where the student used an answer reveal."""
    if not isinstance(step_log, list):
        return 0
    return sum(
        1 for step in step_log
        if isinstance(step, dict) and step.get("was_revealed") is True
    )


def _teacher_service(db: AsyncSession = Depends(get_db)) -> TeacherService:
    mastery = MasteryService(
        mastery_repo=MasteryRepository(db),
        attempt_repo=AttemptRepository(db),
        misconception_repo=MisconceptionRepository(db),
    )
    return TeacherService(db, mastery)


def _teacher_service_from_session(db: AsyncSession) -> TeacherService:
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
    db: AsyncSession = Depends(get_db),
) -> list[RosterStudentEntry]:
    require_teacher_or_admin(auth)
    await ensure_teacher_classroom(db, auth, classroom_id)
    teacher_id = auth.user_id if auth.role == "teacher" else None
    try:
        return await svc.get_roster(classroom_id, teacher_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


@router.get("/classes/{classroom_id}/students/{student_id}/analytics", response_model=StudentAnalyticsOut)
async def get_student_analytics(
    classroom_id: uuid.UUID,
    student_id: uuid.UUID,
    unit_id: str | None = Query(default=None, description="Filter by chapter/unit. Omit or 'all' for all chapters."),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
    db: AsyncSession = Depends(get_db),
) -> StudentAnalyticsOut:
    """Return recent attempts + mastery snapshot for one student (teacher-only).

    Pass ?unit_id=<id> to scope mastery and attempts to a specific chapter.
    Supports pagination via ?limit=20&offset=0.
    """
    await ensure_teacher_classroom(db, auth, classroom_id)

    filter_unit = unit_id if (unit_id and unit_id != "all") else None
    snap = await svc._mastery.get_student_mastery_snapshot(student_id, filter_unit)

    count_q = select(func.count()).select_from(ProblemAttempt).where(ProblemAttempt.user_id == student_id)
    if filter_unit:
        count_q = count_q.where(ProblemAttempt.unit_id == filter_unit)
    total_attempts = await db.scalar(count_q) or 0

    query = (
        select(ProblemAttempt)
        .where(ProblemAttempt.user_id == student_id)
        .order_by(ProblemAttempt.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if filter_unit:
        query = query.where(ProblemAttempt.unit_id == filter_unit)

    result = await db.execute(query)
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
                completed_at=r.completed_at,
                time_spent_s=_compute_time_spent(r),
                hints_used=_count_hints(r.step_log),
                reveals_used=_count_reveals(r.step_log),
            )
            for r in rows
        ],
        lessons_with_data=snap.lessons_with_data,
        total_attempts=total_attempts,
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


async def _fetch_timed_practice_analytics(
    db: AsyncSession,
    classroom_id: uuid.UUID,
    session_id: uuid.UUID,
) -> TimedPracticeAnalytics | None:
    sess = await db.scalar(
        select(ClassroomSession).where(
            ClassroomSession.id == session_id,
            ClassroomSession.classroom_id == classroom_id,
        )
    )
    if sess is None:
        return None

    end_bound = sess.ended_at or datetime.now(timezone.utc)
    result = await db.execute(
        select(ProblemAttempt).where(
            ProblemAttempt.class_id == classroom_id,
            ProblemAttempt.unit_id == sess.unit_id,
            ProblemAttempt.started_at >= sess.started_at,
            ProblemAttempt.started_at <= end_bound,
        )
    )
    attempts = result.scalars().all()

    user_ids = list({a.user_id for a in attempts})
    users: dict[uuid.UUID, User] = {}
    if user_ids:
        res_u = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = {u.id: u for u in res_u.scalars().all()}

    # {user_id: {level: [scores]}}
    grouped: dict[uuid.UUID, dict[int, list[float | None]]] = defaultdict(lambda: defaultdict(list))
    for a in attempts:
        grouped[a.user_id][a.level].append(a.score)

    rows: list[StudentTimedPracticeRow] = []
    for uid, levels in grouped.items():
        level_stats: dict[int, LevelStats] = {}
        total = 0
        for lvl, scores in levels.items():
            valid = [s for s in scores if s is not None]
            level_stats[lvl] = LevelStats(
                count=len(scores),
                avg_score=round(sum(valid) / len(valid), 1) if valid else 0.0,
            )
            total += len(scores)
        u = users.get(uid)
        rows.append(StudentTimedPracticeRow(
            student_id=uid,
            student_name=u.name if u else None,
            levels=level_stats,
            total_count=total,
        ))

    rows.sort(key=lambda r: r.total_count, reverse=True)

    return TimedPracticeAnalytics(
        session_id=sess.id,
        unit_id=sess.unit_id,
        lesson_index=sess.lesson_index,
        rows=rows,
    )


@router.get(
    "/classes/{classroom_id}/sessions/{session_id}/practice-analytics",
    response_model=TimedPracticeAnalytics,
)
async def get_timed_practice_analytics(
    classroom_id: uuid.UUID,
    session_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> TimedPracticeAnalytics:
    """Per-student, per-level problem attempt stats for a specific timed-practice session."""
    await ensure_teacher_classroom(db, auth, classroom_id)

    out = await _fetch_timed_practice_analytics(db, classroom_id, session_id)
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
    async with sse_poll_session() as db:
        await ensure_teacher_classroom(db, auth, classroom_id)
        if await _fetch_timed_practice_analytics(db, classroom_id, session_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    async def event_stream():
        async def poll_json() -> str | None:
            async with sse_poll_session() as sdb:
                out = await _fetch_timed_practice_analytics(sdb, classroom_id, session_id)
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
