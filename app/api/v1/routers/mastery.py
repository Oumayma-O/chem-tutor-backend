"""
Mastery router — attempt lifecycle and mastery state endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_self
from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.mastery import (
    CompleteAttemptRequest,
    LessonProgressOut,
    MasteryState,
    ProgressionDecision,
    ResumeAttemptResponse,
    SaveStepRequest,
    SaveStepResponse,
    SetTopicStatusRequest,
    StartAttemptRequest,
    StartAttemptResponse,
    UnlockLevel3Response,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import (
    MasteryRepository,
    TopicProgressRepository,
)
from app.services.mastery_service import MasteryService

logger = get_logger(__name__)
router = APIRouter(prefix="/mastery")


def _get_topic_progress_repo(db: AsyncSession = Depends(get_db)) -> TopicProgressRepository:
    return TopicProgressRepository(db)


def _get_mastery_service(db: AsyncSession = Depends(get_db)) -> MasteryService:
    return MasteryService(
        mastery_repo=MasteryRepository(db),
        attempt_repo=AttemptRepository(db),
        misconception_repo=MisconceptionRepository(db),
    )


@router.post("/attempts/start", response_model=StartAttemptResponse)
@map_unexpected_errors(
    logger=logger,
    event="start_attempt_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to start attempt.",
)
async def start_attempt(
    req: StartAttemptRequest,
    service: MasteryService = Depends(_get_mastery_service),
    auth: AuthContext = Depends(get_auth_context),
) -> StartAttemptResponse:
    require_self(req.user_id, auth)
    attempt = await service.start_attempt(
        user_id=req.user_id,
        unit_id=req.unit_id,
        lesson_index=req.lesson_index,
        problem_id=req.problem_id,
        difficulty=req.difficulty,
        level=req.level,
        class_id=req.class_id,
    )
    return StartAttemptResponse(attempt_id=attempt.id)


@router.post("/attempts/complete", response_model=ProgressionDecision)
@map_unexpected_errors(
    logger=logger,
    event="complete_attempt_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to record attempt.",
)
async def complete_attempt(
    req: CompleteAttemptRequest,
    service: MasteryService = Depends(_get_mastery_service),
    auth: AuthContext = Depends(get_auth_context),
) -> ProgressionDecision:
    require_self(req.user_id, auth)
    return await service.complete_attempt(
        attempt_id=req.attempt_id,
        user_id=req.user_id,
        unit_id=req.unit_id,
        lesson_index=req.lesson_index,
        score=req.score,
        step_log=req.step_log,
        level=req.level,
    )


@router.post("/attempts/save-step", response_model=SaveStepResponse)
@map_unexpected_errors(
    logger=logger,
    event="save_step_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to save step progress.",
)
async def save_step(
    req: SaveStepRequest,
    service: MasteryService = Depends(_get_mastery_service),
) -> SaveStepResponse:
    """
    Checkpoint: persist the current step_log for an in-progress attempt.

    Call this after each step the student completes so their progress is saved
    and can be restored if they log out mid-problem.
    """
    try:
        mastery_state, attempt_score, attempted_steps = await service.preview_step_progress(
            req.attempt_id, req.step_log, was_revealed=req.was_revealed
        )
    except ValueError as exc:
        # Specific domain case: attempt not found or already complete → 404
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SaveStepResponse(
        mastery=mastery_state,
        attempt_score=attempt_score,
        attempted_steps=attempted_steps,
    )


@router.get(
    "/users/{user_id}/units/{unit_id}/lessons/{lesson_index}/resume",
    response_model=ResumeAttemptResponse,
)
async def resume_attempt(
    user_id: uuid.UUID,
    unit_id: str,
    lesson_index: int,
    level: int,
    service: MasteryService = Depends(_get_mastery_service),
    auth: AuthContext = Depends(get_auth_context),
) -> ResumeAttemptResponse:
    """
    Return the student's latest in-progress attempt for a lesson/level.

    The frontend calls this on load to restore UI state (completed steps, answers).
    Returns 404 if there is no in-progress attempt.
    """
    require_self(user_id, auth)
    attempt = await service.get_in_progress_attempt(user_id, unit_id, lesson_index, level)
    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No in-progress attempt found.",
        )
    return ResumeAttemptResponse(
        attempt_id=attempt.id,
        problem_id=attempt.problem_id,
        level=attempt.level,
        step_log=list(attempt.step_log or []),
    )


@router.get("/users/{user_id}/units/{unit_id}/lessons/{lesson_index}", response_model=MasteryState)
async def get_mastery(
    user_id: uuid.UUID,
    unit_id: str,
    lesson_index: int,
    service: MasteryService = Depends(_get_mastery_service),
    auth: AuthContext = Depends(get_auth_context),
) -> MasteryState:
    """Return mastery state for user/unit/lesson.

    Returns baseline defaults when no record exists.
    """
    require_self(user_id, auth)
    return await service.get_mastery_or_default(user_id, unit_id, lesson_index)


# ── Lesson Progress endpoints ───────────────────────────────────

@router.get(
    "/users/{user_id}/progress",
    response_model=list[LessonProgressOut],
)
async def get_all_progress(
    user_id: uuid.UUID,
    repo: TopicProgressRepository = Depends(_get_topic_progress_repo),
    auth: AuthContext = Depends(get_auth_context),
) -> list[LessonProgressOut]:
    """Return all lesson progress for a user across every unit."""
    require_self(user_id, auth)
    records = await repo.get_all_for_user(user_id)
    return [LessonProgressOut(lesson_index=r.lesson_index, status=r.status) for r in records]


@router.get(
    "/users/{user_id}/units/{unit_id}/progress",
    response_model=list[LessonProgressOut],
)
async def get_unit_progress(
    user_id: uuid.UUID,
    unit_id: str,
    repo: TopicProgressRepository = Depends(_get_topic_progress_repo),
    auth: AuthContext = Depends(get_auth_context),
) -> list[LessonProgressOut]:
    """Return lesson completion statuses for all lessons in a unit, sorted by lesson_index."""
    require_self(user_id, auth)
    records = await repo.get_unit_progress(user_id, unit_id)
    return [
        LessonProgressOut(lesson_index=r.lesson_index, status=r.status)
        for r in sorted(records, key=lambda x: x.lesson_index)
    ]


@router.patch(
    "/users/{user_id}/units/{unit_id}/lessons/{lesson_index}/status",
    response_model=LessonProgressOut,
)
async def set_lesson_status(
    user_id: uuid.UUID,
    unit_id: str,
    lesson_index: int,
    req: SetTopicStatusRequest,
    repo: TopicProgressRepository = Depends(_get_topic_progress_repo),
    auth: AuthContext = Depends(get_auth_context),
) -> LessonProgressOut:
    """Upsert a lesson's completion status (not-started / in-progress / completed)."""
    require_self(user_id, auth)
    record = await repo.upsert_status(user_id, unit_id, lesson_index, req.status)
    return LessonProgressOut(lesson_index=record.lesson_index, status=record.status)


@router.post(
    "/users/{user_id}/units/{unit_id}/lessons/{lesson_index}/unlock-level3",
    response_model=UnlockLevel3Response,
)
async def unlock_level3(
    user_id: uuid.UUID,
    unit_id: str,
    lesson_index: int,
    service: MasteryService = Depends(_get_mastery_service),
    auth: AuthContext = Depends(get_auth_context),
) -> UnlockLevel3Response:
    """Permanently mark Level 3 as unlocked. One-way latch — cannot be reversed."""
    require_self(user_id, auth)
    await service.unlock_level3(user_id, unit_id, lesson_index)
    return UnlockLevel3Response(level3_unlocked=True)
