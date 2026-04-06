"""
Teacher dashboard API — classes, roster, live presence, session history.

GET  /teacher/classes
POST /teacher/classes
GET  /teacher/classes/{classroom_id}/roster
GET  /teacher/classes/{classroom_id}/live
GET  /teacher/classes/{classroom_id}/sessions
GET  /teacher/classes/{classroom_id}/sessions/{session_id}/practice-analytics
"""

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_teacher
from app.domain.schemas.live_session import LiveSessionOut, LiveSessionPublishRequest
from app.infrastructure.database.connection import get_db
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
from app.infrastructure.database.repositories.classroom_repo import ClassroomRepository
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
    unit_id: str | None = Query(default=None, description="Filter by chapter/unit. Omit or 'all' for all chapters."),
    auth: AuthContext = Depends(get_auth_context),
    svc: TeacherService = Depends(_teacher_service),
    db: AsyncSession = Depends(get_db),
) -> StudentAnalyticsOut:
    """Return recent attempts + mastery snapshot for one student (teacher-only).

    Pass ?unit_id=<id> to scope mastery and attempts to a specific chapter.
    """
    require_teacher(auth)
    try:
        classroom = await svc._classrooms.get_by_id_with_students(classroom_id)
    except Exception:
        classroom = None
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    if classroom.teacher_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class.")

    filter_unit = unit_id if (unit_id and unit_id != "all") else None
    snap = await svc._mastery.get_student_mastery_snapshot(student_id, filter_unit)

    query = (
        select(ProblemAttempt)
        .where(ProblemAttempt.user_id == student_id)
        .order_by(ProblemAttempt.started_at.desc())
    )
    if filter_unit:
        query = query.where(ProblemAttempt.unit_id == filter_unit).limit(200)
    else:
        query = query.limit(120)

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


# ── Session history ────────────────────────────────────────────


async def _verify_classroom_owner(
    classroom_id: uuid.UUID,
    auth: AuthContext,
    db: AsyncSession,
) -> None:
    c_repo = ClassroomRepository(db)
    classroom = await c_repo.get_by_id_with_students(classroom_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    if classroom.teacher_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class.")


@router.get("/classes/{classroom_id}/sessions", response_model=list[ClassroomSessionOut])
async def list_classroom_sessions(
    classroom_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> list[ClassroomSessionOut]:
    """Paginated list of persisted sessions (timed practice / exit ticket / both)."""
    require_teacher(auth)
    await _verify_classroom_owner(classroom_id, auth, db)

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
) -> TimedPracticeAnalytics:
    """Per-student, per-level problem attempt stats for a specific timed-practice session."""
    require_teacher(auth)
    await _verify_classroom_owner(classroom_id, auth, db)

    sess = await db.scalar(
        select(ClassroomSession).where(
            ClassroomSession.id == session_id,
            ClassroomSession.classroom_id == classroom_id,
        )
    )
    if sess is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

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
