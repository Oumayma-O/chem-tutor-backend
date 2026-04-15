"""
Classrooms router — classroom management and student enrollment.

POST   /classrooms                             → teacher creates classroom
DELETE /classrooms/{id}                        → teacher soft-deletes classroom
GET    /classrooms/{id}                        → get classroom detail (teacher)
GET    /classrooms/teacher/{id}               → list teacher's classrooms
POST   /classrooms/join                        → student joins by code
GET    /classrooms/student/{id}               → list student's classrooms
GET    /classrooms/{id}/students              → list enrolled students
DELETE /classrooms/{id}/students/{sid}        → remove student
GET    /classrooms/me/live-session            → poll live session (student)
GET    /classrooms/me/live-session/stream     → SSE stream live session (student)
POST   /classrooms/me/live-session/dismiss    → dismiss overlay (student)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.connection import get_db, sse_poll_session
from app.api.v1.authz import AuthContext, get_auth_context, get_auth_context_from_query, require_role, require_self
from app.domain.schemas.live_session import LiveSessionDismissIn, LiveSessionOut
from app.services.classroom.live_session import get_live_session_for_student
from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.core.sse_stream import SSE_STREAM_HEADERS, sse_json_poll_events
from app.domain.schemas.classrooms import (
    ClassroomCreate,
    ClassroomListItem,
    ClassroomOut,
    ClassroomStudentOut,
    JoinClassroomRequest,
    JoinClassroomResponse,
)
from app.services.classroom.service import ClassroomService

logger = get_logger(__name__)
router = APIRouter(prefix="/classrooms")


# ── Student: current live session (must be before /{classroom_id}) ──

@router.get("/me/live-session", response_model=LiveSessionOut)
async def get_my_classroom_live_session(
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
) -> LiveSessionOut:
    """Poll published exit ticket / timed practice for the student's primary class."""
    require_role(auth, "student")
    out = await get_live_session_for_student(db, auth.user_id)
    if out is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in any active classroom.",
        )
    return out


@router.post("/me/live-session/dismiss", status_code=status.HTTP_204_NO_CONTENT)
async def dismiss_my_live_session_overlay(
    body: LiveSessionDismissIn,
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    """Student closed timed practice / exit ticket overlays; logs anchor for analytics (no DB write)."""
    require_role(auth, "student")
    logger.info(
        "student_live_session_overlay_dismissed",
        user_id=str(auth.user_id),
        anchor_key=body.anchor_key[:200],
    )
    return None


@router.get("/me/live-session/stream")
async def stream_my_classroom_live_session(
    auth: AuthContext = Depends(get_auth_context_from_query),
) -> StreamingResponse:
    """
    SSE stream that pushes live session state to a student in real time.

    Sends a `data:` event whenever the session changes, and a comment heartbeat
    every ~25 s to keep the connection alive through proxies.
    The client should reconnect (EventSource does this automatically) on error.
    """
    require_role(auth, "student")
    user_id = auth.user_id

    async def event_stream():
        async def poll_json() -> str | None:
            async with sse_poll_session() as db:
                out = await get_live_session_for_student(db, user_id)
            if out is None:
                return None
            return out.model_dump_json()

        async for chunk in sse_json_poll_events(
            poll_json=poll_json,
            log_event="live_session_sse_error",
        ):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=dict(SSE_STREAM_HEADERS),
    )


# ── Teacher: create / manage classrooms ───────────────────────

@router.post("", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
@map_unexpected_errors(
    logger=logger,
    event="create_classroom_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to create classroom.",
)
async def create_classroom(
    req: ClassroomCreate,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ClassroomOut:
    require_role(auth, "teacher")
    require_self(req.teacher_id, auth)
    try:
        return await ClassroomService(db).create(req.name, req.teacher_id, req.unit_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/teacher/{teacher_id}", response_model=list[ClassroomListItem])
async def list_teacher_classrooms(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[ClassroomListItem]:
    require_role(auth, "teacher")
    require_self(teacher_id, auth)
    return await ClassroomService(db).list_for_teacher(teacher_id)


@router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_classroom(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> Response:
    """Soft-delete a classroom (sets is_active=False). Only the owning teacher may do this."""
    require_role(auth, "teacher")
    try:
        await ClassroomService(db).delete(classroom_id, auth.user_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{classroom_id}", response_model=ClassroomOut)
async def get_classroom(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ClassroomOut:
    require_role(auth, "teacher")
    svc = ClassroomService(db)
    classroom = await svc.get(classroom_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    require_self(classroom.teacher_id, auth)
    return classroom


# ── Student: join / list classrooms ───────────────────────────

@router.post("/join", response_model=JoinClassroomResponse)
@map_unexpected_errors(
    logger=logger,
    event="join_classroom_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to join classroom.",
)
async def join_classroom(
    req: JoinClassroomRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> JoinClassroomResponse:
    require_self(req.student_id, auth)
    try:
        return await ClassroomService(db).join(req.code, req.student_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/student/{student_id}", response_model=list[ClassroomListItem])
async def list_student_classrooms(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[ClassroomListItem]:
    require_self(student_id, auth)
    return await ClassroomService(db).list_for_student(student_id)


@router.delete(
    "/{classroom_id}/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_classroom_student(
    classroom_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> Response:
    """Student leaves the class, or the class teacher removes a student."""
    svc = ClassroomService(db)
    classroom = await svc.get_raw(classroom_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")

    if auth.user_id == student_id:
        require_role(auth, "student")
        require_self(student_id, auth)
        if not await svc.is_enrolled(classroom_id, student_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not enrolled in this classroom.",
            )
    else:
        require_role(auth, "teacher")
        require_self(classroom.teacher_id, auth)

    try:
        await svc.remove_student(classroom_id, student_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{classroom_id}/students", response_model=list[ClassroomStudentOut])
async def list_classroom_students(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> list[ClassroomStudentOut]:
    require_role(auth, "teacher")
    svc = ClassroomService(db)
    classroom = await svc.get_raw(classroom_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    require_self(classroom.teacher_id, auth)
    return await svc.list_students(classroom_id)
