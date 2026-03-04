"""
Analytics router — teacher-facing class analytics.

All endpoints are read-only aggregations. The AI insights endpoint
optionally calls TutorService.generate_class_insights.
"""

import uuid
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.analytics import (
    ClassAnalyticsRequest,
    ClassAnalyticsResponse,
    LessonBreakdown,
    StudentMasterySummary,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository
from app.services.ai.thinking_analysis.service import ThinkingAnalysisService, get_thinking_analysis_service

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics")
settings = get_settings()


@router.post("/classes", response_model=ClassAnalyticsResponse)
async def get_class_analytics(
    req: ClassAnalyticsRequest,
    db: AsyncSession = Depends(get_db),
    thinking_service: ThinkingAnalysisService = Depends(get_thinking_analysis_service),
) -> ClassAnalyticsResponse:
    mastery_repo = MasteryRepository(db)
    attempt_repo = AttemptRepository(db)
    misconception_repo = MisconceptionRepository(db)

    # 1. Pull class-level misconceptions
    misconceptions = await misconception_repo.get_class_misconceptions(
        class_id=req.class_id,
        unit_id=req.unit_id,
        lesson_index=req.lesson_index,
    )

    # 2. Pull class attempts
    attempts = await attempt_repo.get_class_attempts(
        class_id=req.class_id,
        unit_id=req.unit_id,
        lesson_index=req.lesson_index,
    )

    # 3. Collect student IDs from attempts
    student_ids = list({a.user_id for a in attempts})

    # 4. Pull mastery records for all students
    mastery_records = await mastery_repo.get_class_mastery(
        user_ids=student_ids,
        unit_id=req.unit_id,
    )

    # 5. Aggregate error frequencies
    error_freq: dict[str, int] = Counter(m.error_category for m in misconceptions)  # type: ignore[arg-type]

    # 6. Top misconception tags
    tag_counts: Counter = Counter(
        m.misconception_tag for m in misconceptions if m.misconception_tag
    )
    top_misconceptions = [tag for tag, _ in tag_counts.most_common(5)]

    # 7. Per-student summaries
    mastery_by_student = {r.user_id: r for r in mastery_records}
    at_risk_threshold = settings.mastery_threshold - 0.35  # e.g. < 0.40

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
                    and record.attempts_count >= 3
                ),
            )
        )

    # 8. Lesson breakdown
    lesson_groups: dict[int, list] = {}
    for r in mastery_records:
        lesson_groups.setdefault(r.lesson_index, []).append(r.mastery_score)

    topic_breakdowns = [
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

    # 9. AI insights (optional, adds ~1s latency)
    ai_insights: list[str] = []
    if req.include_ai_insights and student_summaries:
        try:
            insights_out = await thinking_service.generate_class_insights(
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
        topic_breakdown=topic_breakdowns,
        students=student_summaries,
        ai_insights=ai_insights,
    )
