"""
Mastery router — attempt lifecycle and mastery state endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.mastery import (
    CategoryScores,
    CompleteAttemptRequest,
    MasteryState,
    ProgressionDecision,
    SetTopicStatusRequest,
    StartAttemptRequest,
    StartAttemptResponse,
    TopicProgressOut,
    UnlockLevel3Response,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import SkillMastery
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository, TopicProgressRepository
from app.services.mastery_service import MasteryService

logger = get_logger(__name__)
router = APIRouter(prefix="/mastery")


def _get_mastery_service(db: AsyncSession = Depends(get_db)) -> MasteryService:
    return MasteryService(
        mastery_repo=MasteryRepository(db),
        attempt_repo=AttemptRepository(db),
        misconception_repo=MisconceptionRepository(db),
    )


@router.post("/attempts/start", response_model=StartAttemptResponse)
async def start_attempt(
    req: StartAttemptRequest,
    service: MasteryService = Depends(_get_mastery_service),
) -> StartAttemptResponse:
    attempt = await service.start_attempt(
        user_id=req.user_id,
        chapter_id=req.chapter_id,
        topic_index=req.topic_index,
        problem_id=req.problem_id,
        difficulty=req.difficulty,
        level=req.level,
        class_id=req.class_id,
    )
    return StartAttemptResponse(attempt_id=attempt.id)


@router.post("/attempts/complete", response_model=ProgressionDecision)
async def complete_attempt(
    req: CompleteAttemptRequest,
    service: MasteryService = Depends(_get_mastery_service),
) -> ProgressionDecision:
    try:
        return await service.complete_attempt(
            attempt_id=req.attempt_id,
            user_id=req.user_id,
            chapter_id=req.chapter_id,
            topic_index=req.topic_index,
            score=req.score,
            step_log=req.step_log,
            level=req.level,
        )
    except Exception as exc:
        logger.error("complete_attempt_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record attempt.",
        )


@router.get("/users/{user_id}/chapters/{chapter_id}/topics/{topic_index}", response_model=MasteryState)
async def get_mastery(
    user_id: uuid.UUID,
    chapter_id: str,
    topic_index: int,
    service: MasteryService = Depends(_get_mastery_service),
) -> MasteryState:
    """Return mastery state for user/chapter/topic. Returns default (0 attempts, 0% baseline) when no record exists."""
    state = await service.get_mastery(user_id, chapter_id, topic_index)
    if state is None:
        from datetime import datetime
        return MasteryState(
            user_id=user_id,
            chapter_id=chapter_id,
            topic_index=topic_index,
            mastery_score=0.0,
            attempts_count=0,
            consecutive_correct=0,
            current_difficulty="medium",
            error_counts={},
            recent_scores=[],
            category_scores=CategoryScores(),
            updated_at=datetime.utcnow(),
            has_mastered=False,
            level3_unlocked=False,
            level3_unlocked_at=None,
            should_advance=False,
            recommended_difficulty="medium",
        )
    return state


# ── Topic Progress endpoints ───────────────────────────────────

@router.get(
    "/users/{user_id}/progress",
    response_model=list[TopicProgressOut],
)
async def get_all_progress(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[TopicProgressOut]:
    """Return all topic progress for a user across every chapter."""
    repo = TopicProgressRepository(db)
    records = await repo.get_all_for_user(user_id)
    return [TopicProgressOut(topic_index=r.topic_index, status=r.status) for r in records]


@router.get(
    "/users/{user_id}/chapters/{chapter_id}/progress",
    response_model=list[TopicProgressOut],
)
async def get_chapter_progress(
    user_id: uuid.UUID,
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[TopicProgressOut]:
    """Return topic completion statuses for all topics in a chapter."""
    repo = TopicProgressRepository(db)
    records = await repo.get_chapter_progress(user_id, chapter_id)
    return [TopicProgressOut(topic_index=r.topic_index, status=r.status) for r in records]


@router.patch(
    "/users/{user_id}/chapters/{chapter_id}/topics/{topic_index}/status",
    response_model=TopicProgressOut,
)
async def set_topic_status(
    user_id: uuid.UUID,
    chapter_id: str,
    topic_index: int,
    req: SetTopicStatusRequest,
    db: AsyncSession = Depends(get_db),
) -> TopicProgressOut:
    """Upsert a topic's completion status (not-started / in-progress / completed)."""
    repo = TopicProgressRepository(db)
    record = await repo.upsert_status(user_id, chapter_id, topic_index, req.status)
    return TopicProgressOut(topic_index=record.topic_index, status=record.status)


@router.post(
    "/users/{user_id}/chapters/{chapter_id}/topics/{topic_index}/unlock-level3",
    response_model=UnlockLevel3Response,
)
async def unlock_level3(
    user_id: uuid.UUID,
    chapter_id: str,
    topic_index: int,
    db: AsyncSession = Depends(get_db),
) -> UnlockLevel3Response:
    """
    Permanently mark Level 3 as unlocked for a student/topic.
    One-way latch — cannot be reversed.
    """
    from datetime import datetime
    now = datetime.utcnow()
    repo = MasteryRepository(db)
    existing = await repo.get_for_topic(user_id, chapter_id, topic_index)
    if existing is None:
        new_mastery = SkillMastery(
            user_id=user_id,
            chapter_id=chapter_id,
            topic_index=topic_index,
            mastery_score=0.0,
            attempts_count=0,
            consecutive_correct=0,
            current_difficulty="medium",
            level3_unlocked=True,
            level3_unlocked_at=now,
            category_scores={},
            error_counts={},
            recent_scores=[],
            updated_at=now,
        )
        await repo.upsert(new_mastery)
    elif not existing.level3_unlocked:
        existing.level3_unlocked = True
        existing.level3_unlocked_at = now
        await repo.upsert(existing)
    return UnlockLevel3Response(level3_unlocked=True)
