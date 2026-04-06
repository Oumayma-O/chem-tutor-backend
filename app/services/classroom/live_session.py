"""Publish / stop classroom live session (exit ticket + timed practice)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.live_session import LiveSessionOut
from app.infrastructure.database.models import Classroom, ClassroomStudent, ExitTicket
from app.services.ai.exit_ticket.config_serialization import exit_ticket_row_to_config


def _coerce_optional_int(v: object) -> int | None:
    """JSONB may return int or float for whole numbers."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v) if v.is_integer() else None
    try:
        return int(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _empty_live_session() -> dict:
    return {
        "active_exit_ticket_id": None,
        "timed_mode_active": False,
        "timed_practice_minutes": None,
        "timed_started_at": None,
        "session_phase": "idle",
        "unit_id": None,
        "lesson_index": None,
    }


def _to_out(classroom_id: uuid.UUID, raw: dict | None) -> LiveSessionOut:
    d = raw if isinstance(raw, dict) else {}
    phase = d.get("session_phase") or "idle"
    if phase not in ("idle", "timed_practice", "exit_ticket"):
        phase = "idle"
    aid = d.get("active_exit_ticket_id")
    tpm = d.get("timed_practice_minutes")
    if isinstance(tpm, float) and tpm.is_integer():
        tpm = int(tpm)
    elif not isinstance(tpm, int):
        tpm = None

    return LiveSessionOut(
        classroom_id=classroom_id,
        timed_mode_active=bool(d.get("timed_mode_active")),
        timed_practice_minutes=tpm,
        timed_started_at=d.get("timed_started_at") if isinstance(d.get("timed_started_at"), str) else None,
        active_exit_ticket_id=str(aid) if aid else None,
        session_phase=phase,
        unit_id=d.get("unit_id") if isinstance(d.get("unit_id"), str) else None,
        lesson_index=_coerce_optional_int(d.get("lesson_index")),
    )


async def publish_live_session(
    session: AsyncSession,
    classroom_id: uuid.UUID,
    teacher_id: uuid.UUID,
    exit_ticket_id: uuid.UUID,
    timed_practice_enabled: bool,
    timed_practice_minutes: int | None,
    unit_id: str,
    lesson_index: int,
) -> LiveSessionOut:
    c_row = await session.scalar(select(Classroom).where(Classroom.id == classroom_id))
    if c_row is None:
        raise LookupError("Classroom not found.")
    if c_row.teacher_id != teacher_id:
        raise PermissionError("Not your class.")

    t_row = await session.scalar(select(ExitTicket).where(ExitTicket.id == exit_ticket_id))
    if t_row is None or t_row.class_id != classroom_id or t_row.teacher_id != teacher_id:
        raise LookupError("Exit ticket not found for this class.")

    # Mark ticket as published the first time it is pushed to students.
    if t_row.published_at is None:
        t_row.published_at = datetime.now(timezone.utc)

    now = datetime.now(timezone.utc).isoformat()
    if timed_practice_enabled:
        phase: str = "timed_practice"
        timed_started = now
        timed_mode = True
    else:
        phase = "exit_ticket"
        timed_started = None
        timed_mode = False

    c_row.live_session = {
        "active_exit_ticket_id": str(exit_ticket_id),
        "timed_mode_active": timed_mode,
        "timed_practice_minutes": timed_practice_minutes if timed_practice_enabled else None,
        "timed_started_at": timed_started,
        "session_phase": phase,
        "unit_id": unit_id,
        "lesson_index": lesson_index,
    }
    await session.flush()
    return _to_out(classroom_id, c_row.live_session)


async def stop_live_session(
    session: AsyncSession,
    classroom_id: uuid.UUID,
    teacher_id: uuid.UUID,
) -> LiveSessionOut:
    c_row = await session.scalar(select(Classroom).where(Classroom.id == classroom_id))
    if c_row is None:
        raise LookupError("Classroom not found.")
    if c_row.teacher_id != teacher_id:
        raise PermissionError("Not your class.")

    c_row.live_session = _empty_live_session()
    await session.flush()
    return _to_out(classroom_id, c_row.live_session)


async def get_live_session_for_student(
    session: AsyncSession,
    student_id: uuid.UUID,
) -> LiveSessionOut | None:
    """Return live session for the student's most recently joined classroom."""
    result = await session.execute(
        select(Classroom)
        .join(ClassroomStudent, ClassroomStudent.classroom_id == Classroom.id)
        .where(ClassroomStudent.student_id == student_id, Classroom.is_active.is_(True))
        .order_by(ClassroomStudent.joined_at.desc())
        .limit(1)
    )
    c_row = result.scalar_one_or_none()
    if c_row is None:
        return None
    raw = c_row.live_session if isinstance(c_row.live_session, dict) else {}
    base = _to_out(c_row.id, raw)
    exit_cfg = None
    aid = raw.get("active_exit_ticket_id") if isinstance(raw, dict) else None
    if aid:
        try:
            tid = uuid.UUID(str(aid))
        except ValueError:
            tid = None
        else:
            t_row = await session.scalar(
                select(ExitTicket).where(ExitTicket.id == tid, ExitTicket.class_id == c_row.id)
            )
            if t_row is not None:
                exit_cfg = exit_ticket_row_to_config(t_row)
    return base.model_copy(update={"exit_ticket": exit_cfg})
