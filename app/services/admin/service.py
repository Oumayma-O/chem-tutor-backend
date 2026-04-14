"""Admin service — curriculum, unit management, logs, stats, curated problems."""

import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.schemas.dashboards import (
    AdminStats,
    AdminTeacherClassSummary,
    AdminTeacherOut,
    ClassQuestionsMetric,
    CuratedProblem,
    DailyEngagementMetric,
    EngagementAnalyticsOut,
    GenerationLogEntry,
    SuperadminStats,
    SystemStats,
    TeacherEngagementRow,
)
from app.domain.schemas.phases import CurriculumResponse

from app.infrastructure.database.models import Classroom, ClassroomStudent, ClassroomSession, Unit, User
from app.infrastructure.database.repositories.exit_ticket_repo import FewShotCuratedRepository
from app.infrastructure.database.repositories.session_activity_repo import SessionActivityRepository
from app.infrastructure.database.repositories.generation_log_repo import (
    GenerationLogRepository,
    UserStatsRepository,
)
from app.infrastructure.database.repositories.phase_repo import ClassroomCurriculumRepository
from app.infrastructure.database.repositories.unit_repo import UnitRepository


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_curriculum(self, course_id: int | None) -> CurriculumResponse:
        repo = ClassroomCurriculumRepository(self._session)
        data = await repo.fetch_curriculum(course_id=course_id, classroom_id=None)
        return CurriculumResponse(**data)

    async def patch_unit(
        self,
        unit_id: str,
        title: str | None,
        description: str | None,
        is_active: bool | None,
    ) -> None:
        """Raises LookupError if unit not found."""
        repo = UnitRepository(self._session)
        unit = await repo.get_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found.")
        if title is not None:
            unit.title = title
        if description is not None:
            unit.description = description
        if is_active is not None:
            unit.is_active = is_active
        await self._session.flush()

    async def delete_unit(self, unit_id: str) -> None:
        """Soft-delete: marks the unit inactive. Raises LookupError if not found."""
        repo = UnitRepository(self._session)
        unit = await repo.get_by_id(unit_id)
        if unit is None:
            raise LookupError("Unit not found.")
        unit.is_active = False
        await self._session.flush()

    async def get_generation_logs(
        self,
        limit: int,
        offset: int,
        unit_id: str | None,
    ) -> list[GenerationLogEntry]:
        repo = GenerationLogRepository(self._session)
        rows = await repo.list_recent(limit=limit, offset=offset, unit_id=unit_id)
        return [
            GenerationLogEntry(
                id=r.id,
                problem_id=r.problem_id,
                unit_id=r.unit_id,
                lesson_index=r.lesson_index,
                level=r.level,
                difficulty=r.difficulty,
                provider=r.provider,
                model_name=r.model_name,
                prompt_version=r.prompt_version,
                execution_time_s=r.execution_time_s,
                created_at=r.created_at,
            )
            for r in rows
        ]

    async def get_system_stats(self) -> SystemStats:
        u_repo = UserStatsRepository(self._session)
        g_repo = GenerationLogRepository(self._session)
        roles = await u_repo.count_by_roles()
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        gen_24h = await g_repo.count_since(since)
        total_logs = await g_repo.count_total()
        n_classrooms = await self._session.execute(select(func.count()).select_from(Classroom))
        total_classrooms = int(n_classrooms.scalar_one())
        return SystemStats(
            total_users=roles.get("total", 0),
            students=roles.get("student", 0),
            teachers=roles.get("teacher", 0),
            admins=roles.get("admin", 0),
            total_generation_logs=total_logs,
            generations_last_24h=gen_24h,
            total_classrooms=total_classrooms,
        )

    async def list_teachers(self, school: str | None = None) -> list[AdminTeacherOut]:
        """All teachers, optionally filtered by school. Includes dynamic student/class counts + is_online."""
        stmt = select(User).where(User.role == "teacher").order_by(User.created_at.desc())
        if school:
            stmt = stmt.where(User.school == school)
        t_result = await self._session.execute(stmt)
        teachers = list(t_result.scalars().all())
        if not teachers:
            return []

        ids: list[uuid.UUID] = [t.id for t in teachers]

        # Active classrooms only — exclude soft-deleted classes
        cls_result = await self._session.execute(
            select(Classroom).where(
                Classroom.teacher_id.in_(ids),
                Classroom.is_active == True,
            )
        )
        all_classes = list(cls_result.scalars().all())
        by_teacher: dict[uuid.UUID, list[Classroom]] = {}
        for c in all_classes:
            by_teacher.setdefault(c.teacher_id, []).append(c)

        # COUNT(DISTINCT student_id) per teacher in one query to avoid double-counting
        # students who are enrolled in multiple classes under the same teacher.
        total_students_by_teacher: dict[uuid.UUID, int] = {}
        if all_classes:
            ds_result = await self._session.execute(
                select(
                    Classroom.teacher_id,
                    func.count(ClassroomStudent.student_id.distinct()).label("n"),
                )
                .join(ClassroomStudent, ClassroomStudent.classroom_id == Classroom.id)
                .where(
                    Classroom.teacher_id.in_(ids),
                    Classroom.is_active == True,
                )
                .group_by(Classroom.teacher_id)
            )
            total_students_by_teacher = {row.teacher_id: row.n for row in ds_result}

        # Online teachers: any classroom session with ended_at IS NULL
        classroom_ids = [c.id for c in all_classes]
        online_teacher_ids: set[uuid.UUID] = set()
        if classroom_ids:
            active_result = await self._session.execute(
                select(Classroom.teacher_id)
                .join(ClassroomSession, ClassroomSession.classroom_id == Classroom.id)
                .where(Classroom.teacher_id.in_(ids), ClassroomSession.ended_at.is_(None))
                .distinct()
            )
            online_teacher_ids = set(active_result.scalars())

        out: list[AdminTeacherOut] = []
        for u in teachers:
            classes = [
                AdminTeacherClassSummary(id=c.id, name=c.name, class_code=c.code)
                for c in sorted(by_teacher.get(u.id, []), key=lambda x: x.created_at)
            ]
            out.append(
                AdminTeacherOut(
                    user_id=u.id,
                    display_name=u.name,
                    email=u.email,
                    district=u.district,
                    school=u.school,
                    total_students=total_students_by_teacher.get(u.id, 0),
                    total_classes=len(classes),
                    is_online=u.id in online_teacher_ids,
                    is_active=u.is_active,
                    created_at=u.created_at,
                    classes=classes,
                )
            )
        return out

    async def get_superadmin_stats(self) -> SuperadminStats:
        """Global platform counts: admins, teachers, active classes, enrolled students,
        and distinct districts/schools derived from admin accounts."""
        admin_count = await self._session.scalar(
            select(func.count()).select_from(User).where(User.role == "admin")
        )
        teacher_count = await self._session.scalar(
            select(func.count()).select_from(User).where(User.role == "teacher")
        )
        class_count = await self._session.scalar(
            select(func.count()).select_from(Classroom).where(Classroom.is_active == True)
        )
        student_count = await self._session.scalar(
            select(func.count(ClassroomStudent.student_id.distinct()))
            .select_from(ClassroomStudent)
            .join(Classroom, Classroom.id == ClassroomStudent.classroom_id)
            .where(Classroom.is_active == True)
        )
        district_count = await self._session.scalar(
            select(func.count(User.district.distinct()))
            .select_from(User)
            .where(User.role == "admin", User.district.isnot(None))
        )
        school_count = await self._session.scalar(
            select(func.count(User.school.distinct()))
            .select_from(User)
            .where(User.role == "admin", User.school.isnot(None))
        )
        return SuperadminStats(
            total_admins=int(admin_count or 0),
            total_teachers=int(teacher_count or 0),
            total_classes=int(class_count or 0),
            total_students=int(student_count or 0),
            total_districts=int(district_count or 0),
            total_schools=int(school_count or 0),
        )

    async def get_admin_stats(self, school: str | None) -> AdminStats:
        """School-scoped counts for an admin dashboard card. When school is None, returns platform-wide stats."""
        teacher_q = select(func.count()).select_from(User).where(User.role == "teacher")
        class_q = (
            select(func.count())
            .select_from(Classroom)
            .join(User, User.id == Classroom.teacher_id)
            .where(Classroom.is_active == True)
        )
        student_q = (
            select(func.count(ClassroomStudent.student_id.distinct()))
            .select_from(ClassroomStudent)
            .join(Classroom, Classroom.id == ClassroomStudent.classroom_id)
            .join(User, User.id == Classroom.teacher_id)
            .where(Classroom.is_active == True)
        )
        if school:
            teacher_q = teacher_q.where(User.school == school)
            class_q = class_q.where(User.school == school)
            student_q = student_q.where(User.school == school)

        teacher_count = await self._session.scalar(teacher_q)
        class_count = await self._session.scalar(class_q)
        student_count = await self._session.scalar(student_q)
        return AdminStats(
            total_teachers=int(teacher_count or 0),
            total_classes=int(class_count or 0),
            total_students=int(student_count or 0),
        )

    async def delete_teacher(self, teacher_id: uuid.UUID, school: str | None) -> None:
        """Delete a teacher account. school=None means superadmin (no scope restriction)."""
        user = await self._session.scalar(
            select(User).where(User.id == teacher_id, User.role == "teacher")
        )
        if user is None:
            raise LookupError("Teacher not found.")
        if school and user.school != school:
            raise PermissionError("Not in your school.")
        await self._session.delete(user)
        await self._session.commit()

    async def patch_teacher(self, teacher_id: uuid.UUID, school: str | None, **fields) -> None:
        """Update teacher profile fields. school=None means superadmin (no scope restriction)."""
        user = await self._session.scalar(
            select(User).where(User.id == teacher_id, User.role == "teacher")
        )
        if user is None:
            raise LookupError("Teacher not found.")
        if school and user.school != school:
            raise PermissionError("Not in your school.")
        for k, v in fields.items():
            if v is not None and hasattr(user, k):
                setattr(user, k, v)
        await self._session.commit()

    async def get_engagement_analytics(
        self,
        scope: Literal["teacher", "school", "district"],
        target: str,
        timeframe: Literal["last_7_days", "last_30_days", "last_90_days"],
        requesting_school: str | None,
    ) -> EngagementAnalyticsOut:
        """Aggregate teacher engagement metrics for admin/superadmin dashboards."""
        days = {"last_7_days": 7, "last_30_days": 30, "last_90_days": 90}[timeframe]
        since: date = (datetime.now(timezone.utc) - timedelta(days=days)).date()

        repo = SessionActivityRepository(self._session)

        teacher_ids = await repo.get_teacher_ids_for_scope(scope, target, requesting_school)
        if not teacher_ids:
            return EngagementAnalyticsOut(
                scope=scope, target=target, timeframe=timeframe, since=since
            )

        # Seed one row per teacher so users with zero session activity still appear (frontend expects a row).
        users_for_teachers = await self._session.execute(select(User).where(User.id.in_(teacher_ids)))
        by_teacher: dict[uuid.UUID, dict] = {}
        daily_by_teacher: dict[uuid.UUID, list[DailyEngagementMetric]] = defaultdict(list)
        for u in users_for_teachers.scalars().all():
            by_teacher[u.id] = {
                "teacher_id": u.id,
                "teacher_name": u.name,
                "email": u.email,
                "school": u.school,
                "district": u.district,
                "total_logins": 0,
                "total_minutes": 0,
            }

        activity_rows = await repo.get_daily_activity(teacher_ids, since)
        question_rows = await repo.get_questions_by_class(teacher_ids, since)

        for row in activity_rows:
            tid = row["user_id"]
            if tid not in by_teacher:
                by_teacher[tid] = {
                    "teacher_id": tid,
                    "teacher_name": row["teacher_name"],
                    "email": row["email"],
                    "school": row["school"],
                    "district": row["district"],
                    "total_logins": 0,
                    "total_minutes": 0,
                }
            logins = int(row["logins"] or 0)
            minutes = int(row["minutes"] or 0)
            by_teacher[tid]["total_logins"] += logins
            by_teacher[tid]["total_minutes"] += minutes
            daily_by_teacher[tid].append(
                DailyEngagementMetric(
                    date=row["session_date"],
                    logins=logins,
                    minutes=minutes,
                )
            )

        teachers = [
            TeacherEngagementRow(
                **meta,
                daily=sorted(daily_by_teacher.get(tid, []), key=lambda d: d.date),
            )
            for tid, meta in by_teacher.items()
        ]

        questions_by_class = [
            ClassQuestionsMetric(
                classroom_id=r["classroom_id"],
                class_name=r["class_name"],
                teacher_id=r["teacher_id"],
                teacher_name=r["teacher_name"],
                question_count=int(r["question_count"] or 0),
            )
            for r in question_rows
        ]

        return EngagementAnalyticsOut(
            scope=scope,
            target=target,
            timeframe=timeframe,
            since=since,
            teachers=teachers,
            questions_by_class=questions_by_class,
            total_logins=sum(t.total_logins for t in teachers),
            total_minutes=sum(t.total_minutes for t in teachers),
            total_questions_assigned=sum(q.question_count for q in questions_by_class),
        )

    async def get_curated_problems(self, limit: int, offset: int) -> list[CuratedProblem]:
        repo = FewShotCuratedRepository(self._session)
        rows = await repo.list_page(limit=limit, offset=offset)
        unit_ids = list({r.unit_id for r in rows})
        unit_meta: dict[str, tuple[str | None, str | None]] = {}
        if unit_ids:
            u_result = await self._session.execute(
                select(Unit).where(Unit.id.in_(unit_ids)).options(selectinload(Unit.course)),
            )
            for u in u_result.scalars().all():
                course_nm = u.course.name if u.course else None
                unit_meta[u.id] = (course_nm, u.title)

        out: list[CuratedProblem] = []
        for r in rows:
            ej = r.example_json or {}
            raw_steps = ej.get("steps")
            steps = raw_steps if isinstance(raw_steps, list) else []
            title = ej.get("title") if isinstance(ej.get("title"), str) else None
            statement = ej.get("statement") if isinstance(ej.get("statement"), str) else None
            cn, ch = unit_meta.get(r.unit_id, (None, None))
            out.append(
                CuratedProblem(
                    id=r.id,
                    unit_id=r.unit_id,
                    lesson_index=r.lesson_index,
                    difficulty=r.difficulty,
                    level=r.level,
                    strategy=r.strategy,
                    variant_index=r.variant_index,
                    is_active=r.is_active,
                    promoted=r.promoted,
                    created_at=r.created_at,
                    title=title,
                    statement=statement,
                    steps=[s for s in steps if isinstance(s, dict)],
                    course_name=cn,
                    chapter_name=ch,
                )
            )
        return out
