"""SessionActivityRepository — heartbeat upserts and engagement analytics queries."""

import uuid
from datetime import date, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.classroom import Classroom
from app.infrastructure.database.models.teacher import ExitTicket
from app.infrastructure.database.models.user import User
from app.infrastructure.database.models.user_session import UserSessionActivity


class SessionActivityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Heartbeat ─────────────────────────────────────────────

    async def record_heartbeat(self, user_id: uuid.UUID, today: date) -> None:
        """Upsert daily activity for user.

        - INSERT on first heartbeat of the day (login_count=1, total_minutes_active=1).
        - UPDATE on subsequent heartbeats (increment total_minutes_active only; login_count unchanged).
        """
        stmt = (
            pg_insert(UserSessionActivity)
            .values(
                id=uuid.uuid4(),
                user_id=user_id,
                session_date=today,
                login_count=1,
                total_minutes_active=1,
            )
            .on_conflict_do_update(
                constraint="uq_user_session_date",
                set_={"total_minutes_active": UserSessionActivity.total_minutes_active + 1},
            )
        )
        await self._session.execute(stmt)

    # ── Analytics queries ──────────────────────────────────────

    async def get_teacher_ids_for_scope(
        self,
        scope: str,
        target: str,
        requesting_school: str | None,
    ) -> list[uuid.UUID]:
        """Return teacher UUIDs allowed by the requested scope.

        Args:
            scope: "teacher" | "school" | "district"
            target: UUID string for teacher scope; name string for school/district.
            requesting_school: set for school-admin callers; None for superadmin.
        """
        stmt = select(User.id).where(User.role == "teacher")

        if scope == "teacher":
            try:
                teacher_uuid = uuid.UUID(target)
            except ValueError:
                return []
            stmt = stmt.where(User.id == teacher_uuid)
            # School admins may only query teachers in their school
            if requesting_school:
                stmt = stmt.where(User.school == requesting_school)

        elif scope == "school":
            if requesting_school and requesting_school != target:
                return []  # school admin cannot query another school
            stmt = stmt.where(User.school == target)

        elif scope == "district":
            if requesting_school:
                return []  # school admins cannot query district-wide
            stmt = stmt.where(User.district == target)

        else:
            return []

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_daily_activity(
        self,
        teacher_ids: list[uuid.UUID],
        since: date,
    ) -> list[dict]:
        """Return rows: {user_id, teacher_name, email, school, district, session_date, logins, minutes}.

        One row per (teacher, day).  Days with no activity are absent (sparse).
        """
        if not teacher_ids:
            return []

        result = await self._session.execute(
            select(
                UserSessionActivity.user_id,
                User.name.label("teacher_name"),
                User.email,
                User.school,
                User.district,
                UserSessionActivity.session_date,
                func.sum(UserSessionActivity.login_count).label("logins"),
                func.sum(UserSessionActivity.total_minutes_active).label("minutes"),
            )
            .join(User, User.id == UserSessionActivity.user_id)
            .where(
                UserSessionActivity.user_id.in_(teacher_ids),
                UserSessionActivity.session_date >= since,
            )
            .group_by(
                UserSessionActivity.user_id,
                User.name,
                User.email,
                User.school,
                User.district,
                UserSessionActivity.session_date,
            )
            .order_by(UserSessionActivity.session_date)
        )
        return [row._asdict() for row in result]

    async def get_questions_by_class(
        self,
        teacher_ids: list[uuid.UUID],
        since: date,
    ) -> list[dict]:
        """Return rows: {classroom_id, class_name, teacher_id, teacher_name, question_count}.

        Counts questions in published exit tickets (published_at IS NOT NULL) using
        PostgreSQL's ``jsonb_array_length``.
        """
        if not teacher_ids:
            return []

        result = await self._session.execute(
            select(
                ExitTicket.class_id.label("classroom_id"),
                Classroom.name.label("class_name"),
                ExitTicket.teacher_id,
                User.name.label("teacher_name"),
                func.sum(
                    func.jsonb_array_length(ExitTicket.questions)
                ).label("question_count"),
            )
            .join(Classroom, Classroom.id == ExitTicket.class_id)
            .join(User, User.id == ExitTicket.teacher_id)
            .where(
                ExitTicket.teacher_id.in_(teacher_ids),
                ExitTicket.published_at.isnot(None),
                func.date(ExitTicket.published_at) >= since,
            )
            .group_by(
                ExitTicket.class_id,
                Classroom.name,
                ExitTicket.teacher_id,
                User.name,
            )
            .order_by(ExitTicket.teacher_id)
        )
        return [row._asdict() for row in result]
