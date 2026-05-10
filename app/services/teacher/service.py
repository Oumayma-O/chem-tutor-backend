"""Teacher dashboard service — class overview, roster, live presence."""

import uuid
from collections import defaultdict
from datetime import datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.teacher import ExitTicket, ExitTicketResponse

from app.domain.schemas.classrooms import ClassroomOut
from app.domain.schemas.dashboards import (
    LevelStats,
    LiveStudentEntry,
    RosterStudentEntry,
    StudentAnalyticsOut,
    StudentAttemptOut,
    StudentTimedPracticeRow,
    TeacherClassOut,
    TeacherClassPatch,
    TimedPracticeAnalytics,
)
from app.domain.schemas.teacher.attempt_detail import AttemptDetailOut, AttemptStepDetail
from app.infrastructure.database.models import Classroom, ClassroomSession, User
from app.infrastructure.database.models.learning import ProblemAttempt, ProblemCache, UserLessonPlaylist
from app.infrastructure.database.models.user_session import UserSessionActivity
from app.services.classroom.service import _to_classroom_out
from app.infrastructure.database.repositories.classroom_repo import (
    ClassroomRepository,
    ClassroomStudentRepository,
)
from app.infrastructure.database.repositories.playlist_repo import UserLessonPlaylistRepository
from app.infrastructure.database.repositories.presence_repo import PresenceRepository
from app.services.mastery_service import MasteryService


async def compute_exit_ticket_avg(
    session: AsyncSession,
    student_id: uuid.UUID,
    class_id: uuid.UUID,
    unit_id: str | None = None,
) -> float | None:
    """Compute average exit ticket score for a student in a class.

    Returns None if no exit ticket responses exist for the scope.
    Returns a float 0.0–100.0 representing the percentage score.
    """
    stmt = (
        select(func.avg(ExitTicketResponse.score))
        .join(ExitTicket, ExitTicketResponse.exit_ticket_id == ExitTicket.id)
        .where(
            ExitTicket.class_id == class_id,
            ExitTicketResponse.student_id == student_id,
            ExitTicketResponse.score.is_not(None),
        )
    )
    if unit_id is not None:
        stmt = stmt.where(ExitTicket.unit_id == unit_id)
    result = await session.scalar(stmt)
    return float(result) if result is not None else None


async def compute_class_exit_ticket_avg(
    session: AsyncSession,
    class_id: uuid.UUID,
    unit_id: str | None = None,
) -> float | None:
    """Compute class-wide average exit ticket score.

    Mean of per-student averages, excluding students with no submissions.
    Returns None if no exit ticket responses exist for the scope.
    """
    # Subquery: per-student average
    student_avg_subq = (
        select(
            ExitTicketResponse.student_id,
            func.avg(ExitTicketResponse.score).label("student_avg"),
        )
        .join(ExitTicket, ExitTicketResponse.exit_ticket_id == ExitTicket.id)
        .where(
            ExitTicket.class_id == class_id,
            ExitTicketResponse.score.is_not(None),
        )
    )
    if unit_id is not None:
        student_avg_subq = student_avg_subq.where(ExitTicket.unit_id == unit_id)
    student_avg_subq = student_avg_subq.group_by(ExitTicketResponse.student_id).subquery()

    # Outer query: mean of per-student averages
    stmt = select(func.avg(student_avg_subq.c.student_avg))
    result = await session.scalar(stmt)
    return float(result) if result is not None else None


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

    async def _last_activity_times(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, datetime | None]:
        """Best-effort last activity: max(problem attempt time, last session day from heartbeats)."""
        if not user_ids:
            return {}
        att = await self._session.execute(
            select(ProblemAttempt.user_id, func.max(ProblemAttempt.started_at))
            .where(ProblemAttempt.user_id.in_(user_ids))
            .group_by(ProblemAttempt.user_id)
        )
        attempt_max: dict[uuid.UUID, datetime] = {row[0]: row[1] for row in att.all() if row[1] is not None}

        sess = await self._session.execute(
            select(UserSessionActivity.user_id, func.max(UserSessionActivity.session_date))
            .where(UserSessionActivity.user_id.in_(user_ids))
            .group_by(UserSessionActivity.user_id)
        )
        session_max: dict[uuid.UUID, datetime] = {}
        for uid, d in sess.all():
            if d is None:
                continue
            session_max[uid] = datetime.combine(d, time.min, tzinfo=timezone.utc)

        out: dict[uuid.UUID, datetime | None] = {}
        for uid in user_ids:
            a_t = attempt_max.get(uid)
            s_t = session_max.get(uid)
            candidates = [x for x in (a_t, s_t) if x is not None]
            out[uid] = max(candidates) if candidates else None
        return out

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
            # Compute class-level exit ticket average
            et_avg = await compute_class_exit_ticket_avg(self._session, c.id, unit_id=c.unit_id)
            stats.exit_ticket_avg = et_avg
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
                    allow_answer_reveal=c.allow_answer_reveal,
                    max_answer_reveals_per_lesson=c.max_answer_reveals_per_lesson,
                    min_level1_examples_for_level2=c.min_level1_examples_for_level2,
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
        teacher_id: uuid.UUID | None,
        *,
        unit_id: str | None = None,
        lesson_index: int | None = None,
    ) -> list[RosterStudentEntry]:
        """Raises LookupError if classroom not found, PermissionError if not owner.
        Pass teacher_id=None to bypass ownership check (admin path).
        Optional unit_id/lesson_index scope the mastery calculation to match dashboard filters."""
        classroom = await self._classrooms.get_by_id_with_students(classroom_id)
        if classroom is None:
            raise LookupError("Classroom not found.")
        if teacher_id is not None and classroom.teacher_id != teacher_id:
            raise PermissionError("Not your class.")

        members = await self._students.get_class_students(classroom_id)
        if not members:
            return []

        # When no unit filter is provided, default to the classroom's active unit
        # so the roster mastery matches the class overview context.
        effective_unit = unit_id or classroom.unit_id

        users = await self._fetch_users_by_ids([m.student_id for m in members])
        last_by = await self._last_activity_times([m.student_id for m in members])

        roster: list[RosterStudentEntry] = []
        for m in members:
            u = users.get(m.student_id)
            snap = await self._mastery.get_student_mastery_snapshot(
                m.student_id, effective_unit, lesson_index=lesson_index,
            )
            at_risk = (
                bool(effective_unit)
                and await self._mastery.is_at_risk(m.student_id, effective_unit)
            )
            et_avg = await compute_exit_ticket_avg(
                self._session, m.student_id, classroom_id, unit_id=effective_unit,
            )
            roster.append(
                RosterStudentEntry(
                    student_id=m.student_id,
                    name=u.name if u else "Unknown",
                    email=u.email if u else None,
                    joined_at=m.joined_at,
                    mastery=snap,
                    at_risk=at_risk,
                    is_blocked=m.is_blocked,
                    last_activity_at=last_by.get(m.student_id),
                    exit_ticket_avg=et_avg,
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
        if patch.allow_answer_reveal is not None:
            classroom.allow_answer_reveal = patch.allow_answer_reveal
        if patch.max_answer_reveals_per_lesson is not None:
            classroom.max_answer_reveals_per_lesson = patch.max_answer_reveals_per_lesson
        if patch.min_level1_examples_for_level2 is not None:
            classroom.min_level1_examples_for_level2 = patch.min_level1_examples_for_level2
        await self._session.commit()

    async def get_live(
        self,
        classroom_id: uuid.UUID,
        teacher_id: uuid.UUID | None,
        within_seconds: int,
    ) -> list[LiveStudentEntry]:
        """Raises LookupError if classroom not found, PermissionError if not owner.
        Pass teacher_id=None to bypass ownership check (admin path)."""
        classroom = await self._classrooms.get_by_id_with_students(classroom_id)
        if classroom is None:
            raise LookupError("Classroom not found.")
        if teacher_id is not None and classroom.teacher_id != teacher_id:
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

    async def get_timed_practice_analytics(
        self,
        classroom_id: uuid.UUID,
        session_id: uuid.UUID,
        teacher_id: uuid.UUID | None,
    ) -> TimedPracticeAnalytics | None:
        """Return per-student/per-level timed-practice stats for one session."""
        classroom = await self._classrooms.get_by_id_with_students(classroom_id)
        if classroom is None:
            raise LookupError("Classroom not found.")
        if teacher_id is not None and classroom.teacher_id != teacher_id:
            raise PermissionError("Not your class.")

        sess = await self._session.scalar(
            select(ClassroomSession).where(
                ClassroomSession.id == session_id,
                ClassroomSession.classroom_id == classroom_id,
            )
        )
        if sess is None:
            return None

        end_bound = sess.ended_at or datetime.now(timezone.utc)
        result = await self._session.execute(
            select(ProblemAttempt).where(
                ProblemAttempt.class_id == classroom_id,
                ProblemAttempt.unit_id == sess.unit_id,
                ProblemAttempt.started_at >= sess.started_at,
                ProblemAttempt.started_at <= end_bound,
            )
        )
        attempts = result.scalars().all()

        user_ids = list({a.user_id for a in attempts})
        users = await self._fetch_users_by_ids(user_ids) if user_ids else {}

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

    async def get_student_analytics(
        self,
        student_id: uuid.UUID,
        *,
        unit_id: str | None,
        lesson_index: int | None,
        limit: int,
        offset: int,
        class_id: uuid.UUID | None = None,
    ) -> StudentAnalyticsOut:
        """Return mastery snapshot + paginated attempt rows for one student."""
        snap = await self._mastery.get_student_mastery_snapshot(
            student_id, unit_id, lesson_index=lesson_index,
        )

        # Compute exit ticket average if class context is available
        et_avg: float | None = None
        if class_id is not None:
            et_avg = await compute_exit_ticket_avg(
                self._session, student_id, class_id, unit_id=unit_id,
            )

        base_filter = [ProblemAttempt.user_id == student_id]
        if unit_id:
            base_filter.append(ProblemAttempt.unit_id == unit_id)
        if lesson_index is not None:
            base_filter.append(ProblemAttempt.lesson_index == lesson_index)

        count_q = select(func.count()).select_from(ProblemAttempt).where(*base_filter)
        total_attempts = await self._session.scalar(count_q) or 0

        query = (
            select(ProblemAttempt)
            .where(*base_filter)
            .order_by(ProblemAttempt.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        rows = result.scalars().all()

        return StudentAnalyticsOut(
            student_id=student_id,
            overall_mastery=snap.overall_mastery,
            category_scores=(
                snap.category_scores.model_dump()
                if hasattr(snap.category_scores, "model_dump")
                else dict(snap.category_scores)
            ),
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
                    time_spent_s=self._compute_time_spent(r),
                    hints_used=self._count_hints(r.step_log),
                    reveals_used=self._count_reveals(r.step_log),
                )
                for r in rows
            ],
            lessons_with_data=snap.lessons_with_data,
            total_attempts=total_attempts,
            exit_ticket_avg=et_avg,
        )

    @staticmethod
    def _compute_time_spent(attempt: ProblemAttempt) -> int:
        if not attempt.completed_at or not attempt.started_at:
            return 0
        delta = attempt.completed_at - attempt.started_at
        return max(0, int(delta.total_seconds()))

    @staticmethod
    def _count_hints(step_log: list | dict | None) -> int:
        if not isinstance(step_log, list):
            return 0
        return sum(
            int(step.get("hints_used", 0) or 0)
            for step in step_log
            if isinstance(step, dict)
        )

    @staticmethod
    def _count_reveals(step_log: list | dict | None) -> int:
        if not isinstance(step_log, list):
            return 0
        return sum(
            1 for step in step_log
            if isinstance(step, dict) and step.get("was_revealed") is True
        )

    # ── Attempt detail ─────────────────────────────────────────────

    @staticmethod
    def _find_problem_in_playlist(playlist_problems: list[dict], problem_id: str) -> dict | None:
        """Search the problems JSONB array for an entry matching problem_id."""
        for p in playlist_problems:
            if isinstance(p, dict) and p.get("id") == problem_id:
                return p
        return None

    async def get_attempt_detail(
        self, attempt_id: uuid.UUID, teacher_id: uuid.UUID
    ) -> AttemptDetailOut:
        """Load full attempt detail for the teacher drill-down panel.

        Raises LookupError if attempt not found, PermissionError if unauthorized.
        """
        # 1. Load ProblemAttempt
        attempt = await self._session.scalar(
            select(ProblemAttempt).where(ProblemAttempt.id == attempt_id)
        )
        if attempt is None:
            raise LookupError("Attempt not found")

        # 2. Authorization: verify teacher owns the classroom
        if attempt.class_id is not None:
            classroom = await self._classrooms.get_by_id_with_students(attempt.class_id)
            if classroom is None or classroom.teacher_id != teacher_id:
                raise PermissionError("Not authorized")
        else:
            # class_id is null — check if student is in any of the teacher's classrooms
            teacher_classrooms = await self._classrooms.get_by_teacher(teacher_id)
            student_in_teacher_class = False
            for c in teacher_classrooms:
                members = await self._students.get_class_students(c.id)
                if any(m.student_id == attempt.user_id for m in members):
                    student_in_teacher_class = True
                    break
            if not student_in_teacher_class:
                raise PermissionError("Not authorized")

        # 3. Load playlist to find problem definition
        playlist_repo = UserLessonPlaylistRepository(self._session)
        playlist = await playlist_repo.get(
            user_id=attempt.user_id,
            unit_id=attempt.unit_id,
            lesson_index=attempt.lesson_index,
            level=attempt.level,
            difficulty=attempt.difficulty,
        )

        problem_def: dict | None = None
        if playlist and isinstance(playlist.problems, list):
            problem_def = self._find_problem_in_playlist(playlist.problems, attempt.problem_id)

        # 4. Fallback to ProblemCache if not found in playlist
        if problem_def is None:
            cache_result = await self._session.execute(
                select(ProblemCache).where(
                    ProblemCache.unit_id == attempt.unit_id,
                    ProblemCache.lesson_index == attempt.lesson_index,
                    ProblemCache.difficulty == attempt.difficulty,
                    ProblemCache.level == attempt.level,
                )
            )
            for cache_entry in cache_result.scalars().all():
                pd = cache_entry.problem_data
                if isinstance(pd, dict) and pd.get("id") == attempt.problem_id:
                    problem_def = pd
                    break
                # Some cache entries store a list of problems
                if isinstance(pd, list):
                    for p in pd:
                        if isinstance(p, dict) and p.get("id") == attempt.problem_id:
                            problem_def = p
                            break
                    if problem_def:
                        break

        # 5. Extract problem statement and steps definition
        problem_statement: str | None = None
        title: str | None = None
        problem_steps: list[dict] = []
        if problem_def is not None:
            problem_statement = problem_def.get("statement")
            title = problem_def.get("title")
            raw_steps = problem_def.get("steps")
            if isinstance(raw_steps, list):
                problem_steps = [s for s in raw_steps if isinstance(s, dict)]

        # 6. Assemble AttemptStepDetail list from step_log + problem steps
        step_log: list[dict] = []
        if isinstance(attempt.step_log, list):
            step_log = [s for s in attempt.step_log if isinstance(s, dict)]

        steps: list[AttemptStepDetail] = []
        for i, log_entry in enumerate(step_log):
            # Match by index
            prob_step = problem_steps[i] if i < len(problem_steps) else None

            step_label = log_entry.get("step_label", "")
            if not step_label and prob_step:
                step_label = prob_step.get("label", f"Step {i + 1}")

            instruction = ""
            correct_answer: str | None = None
            if prob_step:
                instruction = prob_step.get("instruction", "")
                correct_answer = prob_step.get("correct_answer")

            is_correct = bool(log_entry.get("is_correct", False))
            attempts_count = int(log_entry.get("attempts", 1))
            hints_used = int(log_entry.get("hints_used", 0))
            was_revealed = bool(log_entry.get("was_revealed", False))
            time_spent = log_entry.get("time_spent_seconds")
            if time_spent is not None:
                try:
                    time_spent = float(time_spent)
                except (TypeError, ValueError):
                    time_spent = None

            first_attempt_correct = is_correct and attempts_count == 1

            steps.append(
                AttemptStepDetail(
                    step_label=step_label,
                    instruction=instruction,
                    correct_answer=correct_answer,
                    attempts=attempts_count,
                    hints_used=hints_used,
                    was_revealed=was_revealed,
                    is_correct=is_correct,
                    first_attempt_correct=first_attempt_correct,
                    time_spent_seconds=time_spent,
                )
            )

        # 7. Return AttemptDetailOut
        return AttemptDetailOut(
            attempt_id=attempt.id,
            problem_statement=problem_statement,
            title=title,
            steps=steps,
            overall_score=attempt.score,
            level=attempt.level,
            difficulty=attempt.difficulty,
        )
