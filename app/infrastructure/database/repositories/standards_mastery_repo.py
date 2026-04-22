"""StandardsMasteryRepository — aggregated mastery queries across standards.

Class view join paths:
  ProblemAttempt (class_id, unit_id, lesson_index)
    -> UnitLesson.(unit_id, lesson_order) -> UnitLesson.lesson_id
    -> LessonStandard.lesson_id           -> LessonStandard.standard_id
    -> Standard.(id, code, framework, title, description, is_core)

  ExitTicketResponse -> ExitTicket (class_id, unit_id, lesson_index)
    -> UnitLesson.(unit_id, lesson_order) -> UnitLesson.lesson_id
    -> LessonStandard.lesson_id           -> LessonStandard.standard_id
    -> Standard.(id, code, framework, title, description, is_core)

Both sources are merged in Python and averaged per (standard, student).

For student view: gated by SkillMastery records (lessons the student attempted).
"""

import uuid
from typing import NamedTuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    ExitTicket,
    ExitTicketResponse,
    LessonStandard,
    ProblemAttempt,
    SkillMastery,
    Standard,
    UnitLesson,
)

class _StdRow(NamedTuple):
    code: str
    framework: str
    title: str | None
    description: str | None
    user_id: uuid.UUID
    avg_mastery: float


class _StdAggRow(NamedTuple):
    code: str
    framework: str
    title: str | None
    description: str | None
    user_id: uuid.UUID
    score_sum: float
    score_count: int


class _StudentStdRow(NamedTuple):
    code: str
    framework: str
    title: str | None
    avg_mastery: float
    lesson_count: int


class StandardsMasteryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- Class view -----------------------------------------------------------

    async def get_class_standards_mastery(
        self,
        class_id: uuid.UUID,
    ) -> list[_StdRow]:
        """
        Return per-student mastery for every core standard naturally practiced
        in the class -- derived from ProblemAttempts (where class_id matches)
        and ExitTicketResponses (via the parent ExitTicket's class_id).

        No unit_id gate: surfaces whatever students have actually worked on.
        """
        # -- Source 1: ProblemAttempt -----------------------------------------
        pa_stmt = (
            select(
                Standard.code,
                Standard.framework,
                Standard.title,
                Standard.description,
                ProblemAttempt.user_id,
                func.sum(ProblemAttempt.score).label("score_sum"),
                func.count(ProblemAttempt.score).label("score_count"),
            )
            .join(UnitLesson, and_(
                UnitLesson.unit_id == ProblemAttempt.unit_id,
                UnitLesson.lesson_order == ProblemAttempt.lesson_index,
            ))
            .join(LessonStandard, LessonStandard.lesson_id == UnitLesson.lesson_id)
            .join(Standard, Standard.id == LessonStandard.standard_id)
            .where(
                ProblemAttempt.class_id == class_id,
                ProblemAttempt.is_complete == True,
                ProblemAttempt.score.is_not(None),
                Standard.is_core == True,
            )
            .group_by(
                Standard.code,
                Standard.framework,
                Standard.title,
                Standard.description,
                ProblemAttempt.user_id,
            )
        )

        # -- Source 2: ExitTicketResponse -------------------------------------
        et_stmt = (
            select(
                Standard.code,
                Standard.framework,
                Standard.title,
                Standard.description,
                ExitTicketResponse.student_id.label("user_id"),
                func.sum(ExitTicketResponse.score / 100.0).label("score_sum"),
                func.count(ExitTicketResponse.score).label("score_count"),
            )
            .join(ExitTicket, ExitTicket.id == ExitTicketResponse.exit_ticket_id)
            .join(UnitLesson, and_(
                UnitLesson.unit_id == ExitTicket.unit_id,
                UnitLesson.lesson_order == ExitTicket.lesson_index,
            ))
            .join(LessonStandard, LessonStandard.lesson_id == UnitLesson.lesson_id)
            .join(Standard, Standard.id == LessonStandard.standard_id)
            .where(
                ExitTicket.class_id == class_id,
                ExitTicketResponse.score.is_not(None),
                Standard.is_core == True,
            )
            .group_by(
                Standard.code,
                Standard.framework,
                Standard.title,
                Standard.description,
                ExitTicketResponse.student_id,
            )
        )

        pa_result = await self._session.execute(pa_stmt)
        et_result = await self._session.execute(et_stmt)
        return self._merge_standard_samples(
            list(pa_result.all()) + list(et_result.all())
        )

    async def get_student_standards_mastery_for_class(
        self,
        user_id: uuid.UUID,
        class_id: uuid.UUID,
    ) -> list[_StdRow]:
        """
        Return per-standard mastery for one student within a single class only.
        """
        pa_stmt = (
            select(
                Standard.code,
                Standard.framework,
                Standard.title,
                Standard.description,
                ProblemAttempt.user_id,
                # ProblemAttempt.score is stored as 0.0–1.0 (no division needed).
                func.sum(ProblemAttempt.score).label("score_sum"),
                func.count(ProblemAttempt.score).label("score_count"),
            )
            .join(UnitLesson, and_(
                UnitLesson.unit_id == ProblemAttempt.unit_id,
                UnitLesson.lesson_order == ProblemAttempt.lesson_index,
            ))
            .join(LessonStandard, LessonStandard.lesson_id == UnitLesson.lesson_id)
            .join(Standard, Standard.id == LessonStandard.standard_id)
            .where(
                ProblemAttempt.class_id == class_id,
                ProblemAttempt.user_id == user_id,
                ProblemAttempt.is_complete == True,
                ProblemAttempt.score.is_not(None),
                Standard.is_core == True,
            )
            .group_by(
                Standard.code,
                Standard.framework,
                Standard.title,
                Standard.description,
                ProblemAttempt.user_id,
            )
        )

        et_stmt = (
            select(
                Standard.code,
                Standard.framework,
                Standard.title,
                Standard.description,
                ExitTicketResponse.student_id.label("user_id"),
                func.sum(ExitTicketResponse.score / 100.0).label("score_sum"),
                func.count(ExitTicketResponse.score).label("score_count"),
            )
            .join(ExitTicket, ExitTicket.id == ExitTicketResponse.exit_ticket_id)
            .join(UnitLesson, and_(
                UnitLesson.unit_id == ExitTicket.unit_id,
                UnitLesson.lesson_order == ExitTicket.lesson_index,
            ))
            .join(LessonStandard, LessonStandard.lesson_id == UnitLesson.lesson_id)
            .join(Standard, Standard.id == LessonStandard.standard_id)
            .where(
                ExitTicket.class_id == class_id,
                ExitTicketResponse.student_id == user_id,
                ExitTicketResponse.score.is_not(None),
                Standard.is_core == True,
            )
            .group_by(
                Standard.code,
                Standard.framework,
                Standard.title,
                Standard.description,
                ExitTicketResponse.student_id,
            )
        )

        pa_result = await self._session.execute(pa_stmt)
        et_result = await self._session.execute(et_stmt)
        return self._merge_standard_samples(
            list(pa_result.all()) + list(et_result.all())
        )

    @staticmethod
    def _merge_standard_samples(rows: list[_StdAggRow]) -> list[_StdRow]:
        """Merge aggregated score samples from multiple sources with weighted mean."""
        combined: dict[tuple[str, uuid.UUID], dict] = {}
        for row in rows:
            user_uuid = uuid.UUID(str(row.user_id))
            key = (row.code, user_uuid)
            if key not in combined:
                combined[key] = {
                    "code": row.code,
                    "framework": row.framework,
                    "title": row.title or None,
                    "description": row.description or None,
                    "user_id": user_uuid,
                    "score_sum": 0.0,
                    "score_count": 0,
                }
            combined[key]["score_sum"] += float(row.score_sum or 0.0)
            combined[key]["score_count"] += int(row.score_count or 0)

        return [
            _StdRow(
                code=entry["code"],
                framework=entry["framework"],
                title=entry["title"],
                description=entry["description"],
                user_id=entry["user_id"],
                avg_mastery=(
                    entry["score_sum"] / entry["score_count"]
                    if entry["score_count"] > 0 else 0.0
                ),
            )
            for entry in sorted(combined.values(), key=lambda e: e["code"])
        ]

    # -- Student view ---------------------------------------------------------

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
            .where(Standard.is_core == True)
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
