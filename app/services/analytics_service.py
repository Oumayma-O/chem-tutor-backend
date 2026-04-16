"""AnalyticsService — class-level analytics aggregation.

Business logic extracted from the analytics router so it is independently
testable and reusable without spinning up FastAPI.
"""

import uuid
from collections import Counter, defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.analytics import (
    ClassAnalyticsRequest,
    ClassAnalyticsResponse,
    ClassStandardsMasteryResponse,
    LessonBreakdown,
    StandardMasteryItem,
    StudentMasterySummary,
    StudentStandardMasteryItem,
    StudentStandardScore,
    StudentStandardsMasteryResponse,
)
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository
from app.infrastructure.database.repositories.standards_mastery_repo import StandardsMasteryRepository
from app.services.ai.thinking_analysis.service import ThinkingAnalysisService

logger = get_logger(__name__)
settings = get_settings()

# A student is "at-risk" when their mastery is this far below the ceiling
# AND they have made at least _AT_RISK_MIN_ATTEMPTS attempts.
_AT_RISK_GAP = 0.40
_AT_RISK_MIN_ATTEMPTS = 3
_STANDARD_AT_RISK_THRESHOLD = 0.55


class AnalyticsService:
    def __init__(self, db: AsyncSession, thinking_service: ThinkingAnalysisService) -> None:
        self._db = db
        self._thinking = thinking_service

    async def aggregate_class(self, req: ClassAnalyticsRequest) -> ClassAnalyticsResponse:
        mastery_repo = MasteryRepository(self._db)
        attempt_repo = AttemptRepository(self._db)
        misconception_repo = MisconceptionRepository(self._db)

        # ── Fetch raw data ────────────────────────────────────────────────
        misconceptions = await misconception_repo.get_class_misconceptions(
            class_id=req.class_id,
            unit_id=req.unit_id,
            lesson_index=req.lesson_index,
        )
        attempts = await attempt_repo.get_class_attempts(
            class_id=req.class_id,
            unit_id=req.unit_id,
            lesson_index=req.lesson_index,
        )
        student_ids = list({a.user_id for a in attempts})
        mastery_records = await mastery_repo.get_class_mastery(
            user_ids=student_ids,
            unit_id=req.unit_id,
        )

        # ── Aggregate error + misconception frequencies ───────────────────
        error_freq: dict[str, int] = Counter(m.error_category for m in misconceptions)  # type: ignore[arg-type]
        tag_counts: Counter = Counter(
            m.misconception_tag for m in misconceptions if m.misconception_tag
        )
        top_misconceptions = [tag for tag, _ in tag_counts.most_common(5)]

        # ── Per-student summaries ─────────────────────────────────────────
        mastery_by_student = {r.user_id: r for r in mastery_records}
        at_risk_threshold = settings.l3_mastery_ceiling - _AT_RISK_GAP

        student_summaries: list[StudentMasterySummary] = []
        for sid in student_ids:
            record = mastery_by_student.get(sid)
            if record is None:
                continue
            student_tags = [
                m.misconception_tag
                for m in misconceptions
                if m.user_id == sid and m.misconception_tag
            ]
            student_summaries.append(
                StudentMasterySummary(
                    student_id=sid,
                    mastery_score=record.mastery_score,
                    attempts_count=record.attempts_count,
                    error_counts=record.error_counts or {},
                    top_misconceptions=student_tags[:3],
                    is_at_risk=(
                        record.mastery_score < at_risk_threshold
                        and record.attempts_count >= _AT_RISK_MIN_ATTEMPTS
                    ),
                )
            )

        # ── Lesson breakdown ──────────────────────────────────────────────
        lesson_groups: dict[int, list] = {}
        for r in mastery_records:
            lesson_groups.setdefault(r.lesson_index, []).append(r.mastery_score)

        lesson_breakdowns = [
            LessonBreakdown(
                lesson_index=li,
                avg_mastery=sum(scores) / len(scores),
                student_count=len(scores),
                completion_rate=len(scores) / max(len(student_ids), 1),
            )
            for li, scores in sorted(lesson_groups.items())
        ]

        avg_mastery = (
            sum(r.mastery_score for r in mastery_records) / len(mastery_records)
            if mastery_records else 0.0
        )
        at_risk_count = sum(1 for s in student_summaries if s.is_at_risk)

        # ── Optional AI insights ──────────────────────────────────────────
        ai_insights: list[str] = []
        if req.include_ai_insights and student_summaries:
            try:
                insights_out = await self._thinking.generate_class_insights(
                    student_count=len(student_ids),
                    class_mastery=avg_mastery,
                    error_frequencies=dict(error_freq),
                    misconception_data=[
                        {"tag": t, "count": c} for t, c in tag_counts.most_common(5)
                    ],
                )
                ai_insights = insights_out.insights
            except Exception as exc:
                logger.warning("ai_insights_failed", error=str(exc))

        return ClassAnalyticsResponse(
            class_id=req.class_id,
            unit_id=req.unit_id,
            student_count=len(student_ids),
            avg_mastery=avg_mastery,
            at_risk_count=at_risk_count,
            error_frequency=dict(error_freq),
            top_misconceptions=top_misconceptions,
            lesson_breakdown=lesson_breakdowns,
            students=student_summaries,
            ai_insights=ai_insights,
        )

    async def aggregate_class_standards(
        self,
        class_id: uuid.UUID,
    ) -> ClassStandardsMasteryResponse:
        """
        Return per-standard mastery for every student in a class, derived from
        whatever ProblemAttempts and ExitTicketResponses exist for that class.
        No unit assignment required.
        """
        repo = StandardsMasteryRepository(self._db)
        rows = await repo.get_class_standards_mastery(class_id=class_id)

        # Group rows by standard code
        by_std: dict[str, list] = defaultdict(list)
        std_meta: dict[str, tuple] = {}  # code → (framework, title, description)
        for row in rows:
            by_std[row.code].append(row)
            std_meta[row.code] = (row.framework, row.title, row.description)

        standards: list[StandardMasteryItem] = []
        for code, std_rows in sorted(by_std.items()):
            scores = [row.avg_mastery for row in std_rows]
            class_avg = sum(scores) / len(scores) if scores else 0.0
            at_risk = sum(1 for s in scores if s < _STANDARD_AT_RISK_THRESHOLD)
            framework, title, description = std_meta[code]
            standards.append(
                StandardMasteryItem(
                    standard_code=code,
                    standard_title=title,
                    standard_description=description,
                    framework=framework,
                    class_avg=class_avg,
                    at_risk_count=at_risk,
                    student_scores=[
                        StudentStandardScore(
                            student_id=r.user_id,
                            mastery_score=r.avg_mastery,
                        )
                        for r in std_rows
                    ],
                )
            )

        return ClassStandardsMasteryResponse(
            class_id=class_id,
            standards=standards,
        )

    async def aggregate_student_standards(
        self,
        student_id: uuid.UUID,
        class_id: uuid.UUID | None = None,
    ) -> StudentStandardsMasteryResponse:
        """
        Return per-standard mastery for a single student, derived from all
        lessons the student has a SkillMastery record for.
        """
        repo = StandardsMasteryRepository(self._db)
        if class_id is None:
            rows = await repo.get_student_standards_mastery(user_id=student_id)
        else:
            rows = await repo.get_student_standards_mastery_for_class(
                user_id=student_id,
                class_id=class_id,
            )

        standards = [
            StudentStandardMasteryItem(
                standard_code=row.code,
                standard_title=row.title,
                framework=row.framework,
                mastery_score=row.avg_mastery,
                # Class-scoped rows don't have lesson_count; keep 0 as "not computed".
                lesson_count=getattr(row, "lesson_count", 0),
                is_mastered=row.avg_mastery >= 0.75,
            )
            for row in rows
        ]

        return StudentStandardsMasteryResponse(
            student_id=student_id,
            standards=standards,
        )
