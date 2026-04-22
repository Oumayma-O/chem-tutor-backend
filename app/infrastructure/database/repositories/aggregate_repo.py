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

from app.infrastructure.database.models import (
    Classroom,
    ClassroomStudent,
    ProblemAttempt,
    SkillMastery,
    User,
    UserSessionActivity,
)

# Students below this per-student average mastery are flagged at-risk.
_AT_RISK_THRESHOLD = 0.50


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
        and at-risk count. At-risk uses a CTE to compute per-student averages first,
        then counts distinct at-risk students per group.

        For class-level grouping, groups by Classroom.id (unique) and returns
        group_id (UUID string) alongside the display name.
        """
        # For class-level: group by id (unique), expose both name and id.
        # For district/school: group by the text column; group_id is NULL.
        if grouping == "class":
            name_col = Classroom.name.label("name")
            group_id_col = func.cast(Classroom.id, String).label("group_id")
            group_by_col = Classroom.id
        else:
            group_col = self._group_col(grouping)
            name_col = group_col.label("name")
            group_id_col = literal(None).label("group_id")
            group_by_col = group_col

        # CTE: per-student average mastery (independent of classroom grouping)
        student_avg_cte = (
            select(
                SkillMastery.user_id,
                func.avg(SkillMastery.mastery_score).label("avg_mastery"),
            )
            .group_by(SkillMastery.user_id)
            .cte("student_avg_cte")
        )

        stmt = (
            select(
                name_col,
                group_id_col,
                func.count(func.distinct(Classroom.id)).label("class_count"),
                func.count(func.distinct(ClassroomStudent.student_id)).label("student_count"),
                func.coalesce(func.avg(SkillMastery.mastery_score), 0.0).label("avg_mastery"),
                # COUNT(DISTINCT student_id) where that student's overall avg < threshold
                func.count(
                    func.distinct(
                        case(
                            (student_avg_cte.c.avg_mastery < _AT_RISK_THRESHOLD,
                             ClassroomStudent.student_id),
                            else_=None,
                        )
                    )
                ).label("at_risk_count"),
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
                SkillMastery,
                SkillMastery.user_id == ClassroomStudent.student_id,
                isouter=True,
            )
            .join(
                student_avg_cte,
                student_avg_cte.c.user_id == ClassroomStudent.student_id,
                isouter=True,
            )
            .where(
                User.role == "teacher",
                Classroom.is_active == True,  # noqa: E712
            )
            .group_by(group_by_col)
            .order_by(group_by_col)
        )

        stmt = self._apply_scope(stmt, grouping, district, school)
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

        Joins through ClassroomStudent so only student session activity is summed —
        teacher heartbeats are excluded because teachers are not in ClassroomStudent.
        Integer division /60 produces whole hours (PostgreSQL behaviour).
        Key is UUID string for class-level, district/school name otherwise.
        """
        key_col = self._key_col(grouping)
        group_by_col = self._group_col(grouping)

        stmt = (
            select(
                key_col.label("key"),
                func.coalesce(
                    func.sum(UserSessionActivity.total_minutes_active) / 60, 0
                ).label("hours_active"),
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
                UserSessionActivity,
                UserSessionActivity.user_id == ClassroomStudent.student_id,
                isouter=True,
            )
            .where(
                User.role == "teacher",
                Classroom.is_active == True,  # noqa: E712
            )
            .group_by(group_by_col)
        )

        stmt = self._apply_scope(stmt, grouping, district, school)
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
