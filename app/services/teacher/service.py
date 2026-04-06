"""Teacher dashboard service — class overview, roster, live presence."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.classrooms import ClassroomOut
from app.domain.schemas.dashboards import (
    LiveStudentEntry,
    RosterStudentEntry,
    TeacherClassCreate,
    TeacherClassOut,
    TeacherClassPatch,
)
from app.infrastructure.database.models import Classroom, User
from app.services.classroom.service import _to_classroom_out
from app.infrastructure.database.repositories.classroom_repo import (
    ClassroomRepository,
    ClassroomStudentRepository,
)
from app.infrastructure.database.repositories.presence_repo import PresenceRepository
from app.services.mastery_service import MasteryService


def _live_session_teacher_snapshot(raw: object) -> dict:
    """Extract teacher-dashboard fields from `classrooms.live_session` JSON."""
    d = raw if isinstance(raw, dict) else {}
    phase = d.get("session_phase")
    if phase not in ("idle", "timed_practice", "exit_ticket", None):
        phase = None
    aid = d.get("active_exit_ticket_id")
    tpm = d.get("timed_practice_minutes")
    if isinstance(tpm, float) and tpm.is_integer():
        tpm = int(tpm)
    elif not isinstance(tpm, int):
        tpm = None
    et_lim = d.get("exit_ticket_time_limit_minutes")
    if isinstance(et_lim, float) and et_lim.is_integer():
        et_lim = int(et_lim)
    elif not isinstance(et_lim, int):
        et_lim = None
    sp = phase if isinstance(phase, str) else None
    return {
        "timed_mode_active": bool(d.get("timed_mode_active")),
        "timed_practice_minutes": tpm,
        "timed_started_at": d.get("timed_started_at") if isinstance(d.get("timed_started_at"), str) else None,
        "active_exit_ticket_id": str(aid) if aid else None,
        "session_phase": sp,
        "exit_ticket_time_limit_minutes": et_lim,
        "exit_ticket_window_started_at": d.get("exit_ticket_window_started_at")
        if isinstance(d.get("exit_ticket_window_started_at"), str)
        else None,
    }


class TeacherService:
    def __init__(self, session: AsyncSession, mastery: MasteryService) -> None:
        self._session = session
        self._mastery = mastery
        self._classrooms = ClassroomRepository(session)
        self._students = ClassroomStudentRepository(session)

    async def create_class(self, name: str, teacher_id: uuid.UUID, unit_id: str | None) -> ClassroomOut:
        classroom = Classroom(name=name, teacher_id=teacher_id, unit_id=unit_id, code="")
        created = await self._classrooms.create_with_code(classroom)
        return _to_classroom_out(created, student_count=0)

    async def list_classes(self, teacher_id: uuid.UUID) -> list[TeacherClassOut]:
        classrooms = await self._classrooms.get_by_teacher(teacher_id)
        out: list[TeacherClassOut] = []
        for c in classrooms:
            members = await self._students.get_class_students(c.id)
            student_ids = [m.student_id for m in members]
            stats = await self._mastery.get_class_summary_stats(c.id, student_ids, c.unit_id)
            snap = _live_session_teacher_snapshot(c.live_session)
            out.append(
                TeacherClassOut(
                    id=c.id,
                    name=c.name,
                    code=c.code,
                    unit_id=c.unit_id,
                    student_count=len(student_ids),
                    is_active=c.is_active,
                    calculator_enabled=c.calculator_enabled,
                    created_at=c.created_at,
                    stats=stats,
                    **snap,
                )
            )
        return out

    async def _fetch_users_by_ids(self, ids: list[uuid.UUID]) -> dict[uuid.UUID, User]:
        result = await self._session.execute(select(User).where(User.id.in_(ids)))
        return {u.id: u for u in result.scalars().all()}

    async def get_roster(
        self,
        classroom_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> list[RosterStudentEntry]:
        """Raises LookupError if classroom not found, PermissionError if not owner."""
        classroom = await self._classrooms.get_by_id_with_students(classroom_id)
        if classroom is None:
            raise LookupError("Classroom not found.")
        if classroom.teacher_id != teacher_id:
            raise PermissionError("Not your class.")

        members = await self._students.get_class_students(classroom_id)
        if not members:
            return []

        users = await self._fetch_users_by_ids([m.student_id for m in members])

        roster: list[RosterStudentEntry] = []
        for m in members:
            u = users.get(m.student_id)
            snap = await self._mastery.get_student_mastery_snapshot(m.student_id, classroom.unit_id)
            at_risk = (
                bool(classroom.unit_id)
                and await self._mastery.is_at_risk(m.student_id, classroom.unit_id)  # type: ignore[arg-type]
            )
            roster.append(
                RosterStudentEntry(
                    student_id=m.student_id,
                    name=u.name if u else "Unknown",
                    email=u.email if u else None,
                    joined_at=m.joined_at,
                    mastery=snap,
                    at_risk=at_risk,
                )
            )
        return roster

    async def patch_class(
        self,
        classroom_id: uuid.UUID,
        teacher_id: uuid.UUID,
        patch: TeacherClassPatch,
    ) -> None:
        """Raises LookupError if not found, PermissionError if not owner."""
        classroom = await self._classrooms.get_by_id_with_students(classroom_id)
        if classroom is None:
            raise LookupError("Classroom not found.")
        if classroom.teacher_id != teacher_id:
            raise PermissionError("Not your class.")
        if patch.calculator_enabled is not None:
            classroom.calculator_enabled = patch.calculator_enabled
        await self._session.commit()

    async def get_live(
        self,
        classroom_id: uuid.UUID,
        teacher_id: uuid.UUID,
        within_seconds: int,
    ) -> list[LiveStudentEntry]:
        """Raises LookupError if classroom not found, PermissionError if not owner."""
        classroom = await self._classrooms.get_by_id_with_students(classroom_id)
        if classroom is None:
            raise LookupError("Classroom not found.")
        if classroom.teacher_id != teacher_id:
            raise PermissionError("Not your class.")

        p_repo = PresenceRepository(self._session)
        rows = await p_repo.list_active_in_classroom(classroom_id, within_seconds=within_seconds)
        if not rows:
            return []

        users = await self._fetch_users_by_ids([r.user_id for r in rows])
        return [
            LiveStudentEntry(
                student_id=r.user_id,
                name=users[r.user_id].name if r.user_id in users else "Unknown",
                email=users[r.user_id].email if r.user_id in users else None,
                step_id=r.step_id,
                last_seen_at=r.last_seen_at,
            )
            for r in rows
        ]
