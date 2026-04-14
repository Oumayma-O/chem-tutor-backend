"""StandardsMasteryRepository — aggregated mastery queries across standards.

Join path:
  SkillMastery.(unit_id, lesson_index)
  → UnitLesson.(unit_id, lesson_order)  →  UnitLesson.lesson_id
  → LessonStandard.lesson_id            →  LessonStandard.standard_id
  → Standard.(id, code, framework, title, is_core)

For class view:   gated by ClassroomSession (taught lessons).
For student view: gated by SkillMastery records (lessons the student attempted).
"""

import uuid
from collections import defaultdict
from typing import NamedTuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    ClassroomStudent,
    ClassroomSession,
    LessonStandard,
    SkillMastery,
    Standard,
    UnitLesson,
)

# A student is "at risk" on a standard when mastery is below this threshold.
_AT_RISK_THRESHOLD = 0.55


class _StdRow(NamedTuple):
    code: str
    framework: str
    title: str | None
    user_id: uuid.UUID
    avg_mastery: float


class _StudentStdRow(NamedTuple):
    code: str
    framework: str
    title: str | None
    avg_mastery: float
    lesson_count: int


class StandardsMasteryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Class view ────────────────────────────────────────────────────────────

    async def get_class_standards_mastery(
        self,
        class_id: uuid.UUID,
        unit_id: str | None = None,
    ) -> list[_StdRow]:
        """
        Return per-student mastery for every core standard that has been
        *engaged* in the class — either through a teacher session (exit ticket /
        timed practice) OR through independent student practice (SkillMastery
        records for enrolled students).
        """
        # Students enrolled in the classroom
        student_subq = (
            select(ClassroomStudent.student_id)
            .where(ClassroomStudent.classroom_id == class_id)
            .subquery()
        )

        # Taught (unit_id, lesson_index) combos from teacher sessions
        taught_q = (
            select(
                ClassroomSession.unit_id.label("unit_id"),
                ClassroomSession.lesson_index.label("lesson_index"),
            )
            .where(
                ClassroomSession.classroom_id == class_id,
                ClassroomSession.session_type.in_(["exit_ticket", "timed_practice"]),
            )
        )
        if unit_id:
            taught_q = taught_q.where(ClassroomSession.unit_id == unit_id)

        # Practiced (unit_id, lesson_index) combos from student mastery records
        practiced_q = (
            select(
                SkillMastery.unit_id.label("unit_id"),
                SkillMastery.lesson_index.label("lesson_index"),
            )
            .where(SkillMastery.user_id.in_(select(student_subq.c.student_id)))
        )
        if unit_id:
            practiced_q = practiced_q.where(SkillMastery.unit_id == unit_id)

        # Union: all lessons that have been either taught or practiced
        engaged_subq = taught_q.union(practiced_q).subquery()

        stmt = (
            select(
                Standard.code,
                Standard.framework,
                Standard.title,
                SkillMastery.user_id,
                func.avg(SkillMastery.mastery_score).label("avg_mastery"),
            )
            .join(LessonStandard, LessonStandard.standard_id == Standard.id)
            .join(UnitLesson, UnitLesson.lesson_id == LessonStandard.lesson_id)
            .join(
                engaged_subq,
                and_(
                    engaged_subq.c.unit_id == UnitLesson.unit_id,
                    engaged_subq.c.lesson_index == UnitLesson.lesson_order,
                ),
            )
            .join(
                SkillMastery,
                and_(
                    SkillMastery.unit_id == UnitLesson.unit_id,
                    SkillMastery.lesson_index == UnitLesson.lesson_order,
                ),
            )
            .join(student_subq, student_subq.c.student_id == SkillMastery.user_id)
            .where(Standard.is_core == True)  # noqa: E712
            .group_by(Standard.code, Standard.framework, Standard.title, SkillMastery.user_id)
            .order_by(Standard.code)
        )

        result = await self._session.execute(stmt)
        return [
            _StdRow(
                code=row.code,
                framework=row.framework,
                title=row.title or None,
                user_id=row.user_id,
                avg_mastery=float(row.avg_mastery),
            )
            for row in result.all()
        ]

    # ── Student view ──────────────────────────────────────────────────────────

    async def get_student_standards_mastery(
        self,
        user_id: uuid.UUID,
    ) -> list[_StudentStdRow]:
        """
        Return per-standard mastery for a student, derived from all lessons
        the student has a SkillMastery record for.
        """
        stmt = (
            select(
                Standard.code,
                Standard.framework,
                Standard.title,
                func.avg(SkillMastery.mastery_score).label("avg_mastery"),
                func.count(func.distinct(UnitLesson.lesson_id)).label("lesson_count"),
            )
            .join(LessonStandard, LessonStandard.standard_id == Standard.id)
            .join(UnitLesson, UnitLesson.lesson_id == LessonStandard.lesson_id)
            .join(
                SkillMastery,
                and_(
                    SkillMastery.unit_id == UnitLesson.unit_id,
                    SkillMastery.lesson_index == UnitLesson.lesson_order,
                    SkillMastery.user_id == user_id,
                ),
            )
            .where(Standard.is_core == True)  # noqa: E712
            .group_by(Standard.code, Standard.framework, Standard.title)
            .order_by(Standard.code)
        )

        result = await self._session.execute(stmt)
        return [
            _StudentStdRow(
                code=row.code,
                framework=row.framework,
                title=row.title or None,
                avg_mastery=float(row.avg_mastery),
                lesson_count=int(row.lesson_count),
            )
            for row in result.all()
        ]
