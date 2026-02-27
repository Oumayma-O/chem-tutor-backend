"""
Mastery router — attempt lifecycle and mastery state endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.mastery import (
    CompleteAttemptRequest,
    MasteryState,
    ProgressionDecision,
    StartAttemptRequest,
    StartAttemptResponse,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository
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
    state = await service.get_mastery(user_id, chapter_id, topic_index)
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No mastery record found.",
        )
    return state
