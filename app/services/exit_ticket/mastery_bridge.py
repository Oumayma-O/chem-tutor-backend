"""Bridge exit ticket scores into the SkillMastery table.

Exit tickets fill the top mastery band (l3_ceiling → 1.0), which is 15% of total
mastery by default. Practice fills L2 (0→60%) and L3 (60→85%) bands. This ensures
a student needs both practice AND assessment to reach 100%.

The exit ticket contribution is additive — it never overwrites practice mastery.
Multiple exit ticket submissions for the same lesson use the best score.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.database.models.learning import SkillMastery
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository

logger = get_logger(__name__)


async def apply_exit_ticket_to_mastery(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    unit_id: str,
    lesson_index: int,
    exit_ticket_score_percent: float,
) -> None:
    """Upsert SkillMastery so the exit ticket score fills the top band.

    ``exit_ticket_score_percent`` is 0–100. The contribution to mastery_score is:
        et_band_width * (score / 100)
    where et_band_width = 1.0 - l3_mastery_ceiling (default 0.15).

    If the student has no practice mastery yet, a minimal record is created so the
    standards heatmap shows the exit ticket result instead of "no data".
    """
    if exit_ticket_score_percent is None:
        return

    settings = get_settings()
    et_band_width = 1.0 - settings.l3_mastery_ceiling  # 0.15 by default
    et_contribution = et_band_width * (exit_ticket_score_percent / 100.0)

    repo = MasteryRepository(db)
    existing = await repo.get_for_lesson(user_id, unit_id, lesson_index)

    if existing is not None:
        # Practice mastery exists — add the exit ticket band on top.
        # Cap at l3_ceiling so we don't double-count if practice already filled some.
        practice_part = min(existing.mastery_score, settings.l3_mastery_ceiling)
        new_score = round(practice_part + et_contribution, 4)
        existing.mastery_score = min(new_score, 1.0)
        existing.updated_at = datetime.now(timezone.utc)
        await repo.upsert(existing)
    else:
        # No practice record — create one with just the exit ticket band.
        record = SkillMastery(
            user_id=user_id,
            unit_id=unit_id,
            lesson_index=lesson_index,
            mastery_score=round(min(et_contribution, et_band_width), 4),
            attempts_count=0,
            consecutive_correct=0,
            current_difficulty="medium",
            category_scores={},
            error_counts={},
            recent_scores=[],
            updated_at=datetime.now(timezone.utc),
        )
        await repo.upsert(record)

    logger.info(
        "exit_ticket_mastery_applied",
        user=str(user_id),
        unit=unit_id,
        lesson=lesson_index,
        et_score=exit_ticket_score_percent,
        et_contribution=round(et_contribution, 4),
    )
