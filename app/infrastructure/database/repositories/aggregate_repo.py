"""AggregateRepository — cross-scope performance queries for the Combined Analytics tab.

Join path for mastery/student metrics:
  User (teacher) → Classroom → ClassroomStudent → SkillMastery / UserSessionActivity

The grouping column changes based on `grouping`:
  "district" → User.district
  "school"   → User.school
  "class"    → Classroom.id (name returned separately for display)
"""

from sqlalchemy import String, case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.at_risk import (
    AT_RISK_THRESHOLD_L2,
    AT_RISK_THRESHOLD_L3,
    AT_RISK_MIN_ATTEMPTS,
    L1_MASTERY_CEIL,
    L2_MASTERY_CEIL,
    L3_MASTERY_CEIL,
)

_L2_W = 0.40   # L2 weight in the new 20/40/40 formula
_L3_W = 0.40   # L3 weight in the new 20/40/40 formula
from app.infrastructure.database.models import (
    Classroom,
    ClassroomStudent,
    ProblemAttempt,
    SkillMastery,
    User,
    UserSessionActivity,
)


class AggregateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _group_col(self, grouping: str):
        return {
            "district": User.district,
            "school": User.school,
            "class": Classroom.id,
        }[grouping]

    def _key_col(self, grouping: str):
        """Column used as the dict key in helper queries.

        For class-level we key by UUID string so lookups are unambiguous even
        when two classrooms share the same display name.
        """
        if grouping == "class":
            return func.cast(Classroom.id, String)
        return self._group_col(grouping)

    def _apply_scope(self, stmt, grouping: str, district: str | None, school: str | None):
        """Apply district/school WHERE filters and exclude NULL group keys."""
        # For district/school grouping, exclude rows where the text column is NULL.
        # For class grouping Classroom.id is never NULL so no filter needed.
        if grouping != "class":
            col = self._group_col(grouping)
            stmt = stmt.where(col.is_not(None))
        if district:
            stmt = stmt.where(User.district == district)
        if school:
            stmt = stmt.where(User.school == school)
        return stmt

    # ── Main groups query ──────────────────────────────────────────────────────

    async def get_groups(
        self,
        grouping: str,
        district: str | None,
        school: str | None,
    ) -> list:
        """Return one row per group with student count, class count, avg mastery,
        and at-risk count.

        Uses a DISTINCT CTE for student-level stats so that a student enrolled
        in multiple classrooms within the same district or school is counted once,
        not once per classroom. Class-level grouping is inherently deduplicated
        (one row per classroom per student in ClassroomStudent).
        """
        # For class-level, key by UUID string; for district/school, key by text value.
        if grouping == "class":
            gk_expr = func.cast(Classroom.id, String)
        else:
            gk_expr = self._group_col(grouping)

        # CTE: per-student global avg mastery, unlock status, attempt count, level fills,
        # adoption flag, and continuous risk score.
        _avg = func.avg(SkillMastery.mastery_score)
        _total_att = func.coalesce(func.sum(SkillMastery.attempts_count), 0)
        _mastery_risk = func.least(func.greatest(1.0 - _avg, 0.0), 1.0)
        _attempt_risk = func.least(_total_att / 10.0, 1.0)
        _risk_score = func.least(0.7 * _mastery_risk + 0.3 * _attempt_risk, 1.0)
        student_mastery_cte = (
            select(
                SkillMastery.user_id,
                _avg.label("avg_mastery"),
                func.bool_or(SkillMastery.level3_unlocked).label("any_l3_unlocked"),
                func.sum(SkillMastery.attempts_count).label("total_attempts"),
                func.least(_avg / L1_MASTERY_CEIL, 1.0).label("l1_fill"),
                func.greatest(
                    0.0,
                    func.least((_avg - L1_MASTERY_CEIL) / _L2_W, 1.0),
                ).label("l2_fill"),
                func.greatest(
                    0.0,
                    func.least((_avg - (L1_MASTERY_CEIL + _L2_W)) / _L3_W, 1.0),
                ).label("l3_fill"),
                func.bool_or(SkillMastery.attempts_count >= AT_RISK_MIN_ATTEMPTS).label("has_l2_attempt"),
                _risk_score.label("risk_score"),
            )
            .group_by(SkillMastery.user_id)
            .cte("student_mastery")
        )

        # CTE: distinct (group_key, student_id, avg_mastery).
        # DISTINCT prevents a student enrolled in multiple classrooms within the
        # same district/school from inflating group averages or at-risk counts.
        scoped_q = (
            select(
                gk_expr.label("gk"),
                ClassroomStudent.student_id,
                student_mastery_cte.c.avg_mastery,
                student_mastery_cte.c.any_l3_unlocked,
                student_mastery_cte.c.total_attempts,
                student_mastery_cte.c.l1_fill,
                student_mastery_cte.c.l2_fill,
                student_mastery_cte.c.l3_fill,
                student_mastery_cte.c.has_l2_attempt,
                student_mastery_cte.c.risk_score,
            )
            .select_from(User)
            .join(Classroom, Classroom.teacher_id == User.id)
            .join(
                ClassroomStudent,
                (ClassroomStudent.classroom_id == Classroom.id)
                & (ClassroomStudent.is_blocked == False),  # noqa: E712
                isouter=True,
            )
            .join(
                student_mastery_cte,
                student_mastery_cte.c.user_id == ClassroomStudent.student_id,
                isouter=True,
            )
            .where(
                User.role == "teacher",
                Classroom.is_active == True,  # noqa: E712
            )
        )
        scoped_q = self._apply_scope(scoped_q, grouping, district, school)
        scoped_cte = scoped_q.distinct().cte("scoped_students")

        # CTE: class count per group (separate from student dedup — counts classrooms,
        # not students, so no dedup needed here).
        cc_q = (
            select(
                gk_expr.label("gk"),
                func.count(func.distinct(Classroom.id)).label("class_count"),
            )
            .select_from(User)
            .join(Classroom, Classroom.teacher_id == User.id)
            .where(
                User.role == "teacher",
                Classroom.is_active == True,  # noqa: E712
            )
            .group_by(gk_expr)
        )
        cc_q = self._apply_scope(cc_q, grouping, district, school)
        cc_cte = cc_q.cte("class_count")

        # Aggregate per-group stats from the deduplicated student CTE.
        student_agg = (
            select(
                scoped_cte.c.gk,
                func.coalesce(func.max(cc_cte.c.class_count), 0).label("class_count"),
                func.count(scoped_cte.c.student_id).label("student_count"),
                func.coalesce(func.avg(scoped_cte.c.avg_mastery), 0.0).label("avg_mastery"),
                func.count(
                    case(
                        (
                            scoped_cte.c.any_l3_unlocked
                            & (scoped_cte.c.avg_mastery < AT_RISK_THRESHOLD_L3),
                            scoped_cte.c.student_id,
                        ),
                        (
                            (~scoped_cte.c.any_l3_unlocked)
                            & (scoped_cte.c.total_attempts >= AT_RISK_MIN_ATTEMPTS)
                            & (scoped_cte.c.avg_mastery < AT_RISK_THRESHOLD_L2),
                            scoped_cte.c.student_id,
                        ),
                        else_=None,
                    )
                ).label("at_risk_count"),
                func.coalesce(func.avg(scoped_cte.c.l1_fill), 0.0).label("avg_l1_score"),
                func.coalesce(func.avg(scoped_cte.c.l2_fill), 0.0).label("avg_l2_score"),
                func.coalesce(func.avg(scoped_cte.c.l3_fill), 0.0).label("avg_l3_score"),
                func.count(
                    case(
                        (
                            scoped_cte.c.any_l3_unlocked
                            & (scoped_cte.c.avg_mastery < AT_RISK_THRESHOLD_L3),
                            scoped_cte.c.student_id,
                        ),
                        else_=None,
                    )
                ).label("at_risk_l3_count"),
                func.count(
                    case(
                        (
                            (~scoped_cte.c.any_l3_unlocked)
                            & (scoped_cte.c.total_attempts >= AT_RISK_MIN_ATTEMPTS)
                            & (scoped_cte.c.avg_mastery < AT_RISK_THRESHOLD_L2),
                            scoped_cte.c.student_id,
                        ),
                        else_=None,
                    )
                ).label("at_risk_l2_count"),
                func.count(
                    case(
                        (scoped_cte.c.risk_score >= 0.7, scoped_cte.c.student_id),
                        else_=None,
                    )
                ).label("high_risk_count"),
                func.count(
                    case(
                        (
                            (scoped_cte.c.risk_score >= 0.4)
                            & (scoped_cte.c.risk_score < 0.7),
                            scoped_cte.c.student_id,
                        ),
                        else_=None,
                    )
                ).label("moderate_risk_count"),
                func.count(
                    case(
                        (scoped_cte.c.has_l2_attempt == True, scoped_cte.c.student_id),  # noqa: E712
                        else_=None,
                    )
                ).label("adopted_count"),
            )
            .select_from(scoped_cte)
            .join(cc_cte, cc_cte.c.gk == scoped_cte.c.gk, isouter=True)
            .group_by(scoped_cte.c.gk)
            .subquery("student_agg")
        )

        # Outer query: add display name and group_id columns.
        if grouping == "class":
            stmt = (
                select(
                    Classroom.name.label("name"),
                    student_agg.c.gk.label("group_id"),
                    student_agg.c.class_count,
                    student_agg.c.student_count,
                    student_agg.c.avg_mastery,
                    student_agg.c.at_risk_count,
                    student_agg.c.avg_l1_score,
                    student_agg.c.avg_l2_score,
                    student_agg.c.avg_l3_score,
                    student_agg.c.at_risk_l2_count,
                    student_agg.c.at_risk_l3_count,
                    student_agg.c.high_risk_count,
                    student_agg.c.moderate_risk_count,
                    student_agg.c.adopted_count,
                )
                .select_from(student_agg)
                .join(Classroom, func.cast(Classroom.id, String) == student_agg.c.gk)
                .order_by(Classroom.name)
            )
        else:
            stmt = (
                select(
                    student_agg.c.gk.label("name"),
                    literal(None).label("group_id"),
                    student_agg.c.class_count,
                    student_agg.c.student_count,
                    student_agg.c.avg_mastery,
                    student_agg.c.at_risk_count,
                    student_agg.c.avg_l1_score,
                    student_agg.c.avg_l2_score,
                    student_agg.c.avg_l3_score,
                    student_agg.c.at_risk_l2_count,
                    student_agg.c.at_risk_l3_count,
                    student_agg.c.high_risk_count,
                    student_agg.c.moderate_risk_count,
                    student_agg.c.adopted_count,
                )
                .select_from(student_agg)
                .order_by(student_agg.c.gk)
            )

        result = await self._session.execute(stmt)
        return result.all()

    # ── Problems solved ────────────────────────────────────────────────────────

    async def get_problems_solved(
        self,
        grouping: str,
        district: str | None,
        school: str | None,
    ) -> dict[str, int]:
        """Return {group_key: completed_attempt_count}.

        Key is UUID string for class-level, district/school name otherwise.
        """
        key_col = self._key_col(grouping)
        group_by_col = self._group_col(grouping)

        stmt = (
            select(
                key_col.label("key"),
                func.count(ProblemAttempt.id).label("problems_solved"),
            )
            .select_from(ProblemAttempt)
            .join(Classroom, Classroom.id == ProblemAttempt.class_id)
            .join(User, User.id == Classroom.teacher_id)
            .where(
                ProblemAttempt.is_complete == True,  # noqa: E712
                ProblemAttempt.class_id.is_not(None),
                User.role == "teacher",
                Classroom.is_active == True,  # noqa: E712
            )
            .group_by(group_by_col)
        )

        stmt = self._apply_scope(stmt, grouping, district, school)
        result = await self._session.execute(stmt)
        return {str(row.key): row.problems_solved for row in result.all()}

    # ── Student hours active ───────────────────────────────────────────────────

    async def get_hours_active(
        self,
        grouping: str,
        district: str | None,
        school: str | None,
    ) -> dict[str, int]:
        """Return {group_key: total_student_hours}.

        Uses a distinct (group_key, student_id) subquery so that a student enrolled
        in multiple classrooms within the same district or school has their session
        minutes counted once, not once per classroom.
        Key is UUID string for class-level, district/school name otherwise.
        """
        key_col = self._key_col(grouping)

        distinct_q = (
            select(key_col.label("key"), ClassroomStudent.student_id)
            .select_from(User)
            .join(Classroom, Classroom.teacher_id == User.id)
            .join(
                ClassroomStudent,
                (ClassroomStudent.classroom_id == Classroom.id)
                & (ClassroomStudent.is_blocked == False),  # noqa: E712
                isouter=True,
            )
            .where(
                User.role == "teacher",
                Classroom.is_active == True,  # noqa: E712
            )
            .distinct()
        )
        distinct_q = self._apply_scope(distinct_q, grouping, district, school)
        sq = distinct_q.subquery("distinct_students")

        stmt = (
            select(
                sq.c.key,
                func.coalesce(
                    func.sum(UserSessionActivity.total_minutes_active) / 60, 0
                ).label("hours_active"),
            )
            .select_from(sq)
            .join(UserSessionActivity, UserSessionActivity.user_id == sq.c.student_id, isouter=True)
            .group_by(sq.c.key)
        )

        result = await self._session.execute(stmt)
        return {str(row.key): int(row.hours_active or 0) for row in result.all()}

    # ── Weakest units ──────────────────────────────────────────────────────────

    async def get_weakest_units(
        self,
        district: str | None,
        school: str | None,
        limit: int = 8,
    ) -> list:
        """Return up to `limit` units with the lowest avg mastery across the scope,
        sorted ascending. Includes unit_id and student_count only; caller fetches titles."""
        stmt = (
            select(
                SkillMastery.unit_id,
                func.avg(SkillMastery.mastery_score).label("avg_mastery"),
                func.count(func.distinct(SkillMastery.user_id)).label("student_count"),
            )
            .select_from(SkillMastery)
            .join(ClassroomStudent, ClassroomStudent.student_id == SkillMastery.user_id)
            .join(Classroom, Classroom.id == ClassroomStudent.classroom_id)
            .join(User, User.id == Classroom.teacher_id)
            .where(
                User.role == "teacher",
                Classroom.is_active == True,  # noqa: E712
                ClassroomStudent.is_blocked == False,  # noqa: E712
            )
            .group_by(SkillMastery.unit_id)
            .order_by(func.avg(SkillMastery.mastery_score).asc())
            .limit(limit)
        )

        if district:
            stmt = stmt.where(User.district == district)
        if school:
            stmt = stmt.where(User.school == school)

        result = await self._session.execute(stmt)
        return result.all()

    # ── Mastery distribution ───────────────────────────────────────────────────

    async def get_mastery_distribution(
        self,
        district: str | None,
        school: str | None,
    ) -> dict[str, int]:
        """Return student counts bucketed into 4 mastery ranges.

        Aggregates SkillMastery per student first (via subquery) to avoid
        inflating counts when students are enrolled in multiple classrooms.
        """
        # Scoped student IDs (distinct — avoids duplication from multi-class enrolment)
        scoped_q = (
            select(func.distinct(ClassroomStudent.student_id))
            .join(Classroom, Classroom.id == ClassroomStudent.classroom_id)
            .join(User, User.id == Classroom.teacher_id)
            .where(
                User.role == "teacher",
                Classroom.is_active == True,  # noqa: E712
                ClassroomStudent.is_blocked == False,  # noqa: E712
            )
        )
        if district:
            scoped_q = scoped_q.where(User.district == district)
        if school:
            scoped_q = scoped_q.where(User.school == school)

        # CTE: one row per student, their overall avg mastery across all skills
        cte = (
            select(
                SkillMastery.user_id,
                func.avg(SkillMastery.mastery_score).label("avg_mastery"),
            )
            .where(SkillMastery.user_id.in_(scoped_q))
            .group_by(SkillMastery.user_id)
            .cte("dist_cte")
        )

        stmt = select(
            func.count(case((cte.c.avg_mastery < 0.50, 1), else_=None)).label("b0_50"),
            func.count(case(
                ((cte.c.avg_mastery >= 0.50) & (cte.c.avg_mastery < 0.70), 1), else_=None,
            )).label("b50_70"),
            func.count(case(
                ((cte.c.avg_mastery >= 0.70) & (cte.c.avg_mastery < 0.85), 1), else_=None,
            )).label("b70_85"),
            func.count(case((cte.c.avg_mastery >= 0.85, 1), else_=None)).label("b85_100"),
        ).select_from(cte)

        row = (await self._session.execute(stmt)).one()
        return {
            "0-50":   int(row.b0_50 or 0),
            "50-70":  int(row.b50_70 or 0),
            "70-85":  int(row.b70_85 or 0),
            "85-100": int(row.b85_100 or 0),
        }
