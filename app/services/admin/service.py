"""Admin service — curriculum, unit management, logs, stats, curated problems."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.schemas.dashboards import (
    AdminTeacherClassSummary,
    AdminTeacherOut,
    CuratedProblem,
    GenerationLogEntry,
    SystemStats,
)
from app.domain.schemas.phases import CurriculumResponse

from app.infrastructure.database.models import Classroom, Course, Grade, Unit, User, UserProfile
from app.infrastructure.database.repositories.exit_ticket_repo import FewShotCuratedRepository
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

    async def list_teachers(self) -> list[AdminTeacherOut]:
        """All users with role teacher, with profile grade/course label and owned classrooms."""
        t_result = await self._session.execute(
            select(User).where(User.role == "teacher").order_by(User.created_at.desc())
        )
        teachers = list(t_result.scalars().all())
        if not teachers:
            return []

        ids: list[uuid.UUID] = [t.id for t in teachers]
        cls_result = await self._session.execute(select(Classroom).where(Classroom.teacher_id.in_(ids)))
        all_classes = list(cls_result.scalars().all())
        by_teacher: dict[uuid.UUID, list[Classroom]] = {}
        for c in all_classes:
            by_teacher.setdefault(c.teacher_id, []).append(c)

        prof_result = await self._session.execute(select(UserProfile).where(UserProfile.user_id.in_(ids)))
        profiles = {p.user_id: p for p in prof_result.scalars().all()}

        grade_ids = {p.grade_id for p in profiles.values() if p.grade_id}
        course_ids = {p.course_id for p in profiles.values() if p.course_id}
        grade_map: dict[int, str] = {}
        course_map: dict[int, str] = {}
        if grade_ids:
            gr = await self._session.execute(select(Grade).where(Grade.id.in_(grade_ids)))
            grade_map = {g.id: g.name for g in gr.scalars().all()}
        if course_ids:
            cr = await self._session.execute(select(Course).where(Course.id.in_(course_ids)))
            course_map = {c.id: c.name for c in cr.scalars().all()}

        out: list[AdminTeacherOut] = []
        for u in teachers:
            prof = profiles.get(u.id)
            grade_level: str | None = None
            if prof:
                parts = [grade_map.get(prof.grade_id), course_map.get(prof.course_id)]
                parts = [p for p in parts if p]
                grade_level = " · ".join(parts) if parts else None
            classes = [
                AdminTeacherClassSummary(id=c.id, name=c.name, class_code=c.code)
                for c in sorted(by_teacher.get(u.id, []), key=lambda x: x.created_at)
            ]
            out.append(
                AdminTeacherOut(
                    user_id=u.id,
                    display_name=u.name,
                    email=u.email,
                    grade_level=grade_level,
                    created_at=u.created_at,
                    classes=classes,
                )
            )
        return out

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
