"""
Mastery router — attempt lifecycle and mastery state endpoints.
"""

from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.mastery import (
    CategoryScores,
    CompleteAttemptRequest,
    LessonProgressOut,
    MasteryState,
    ProgressionDecision,
    ResumeAttemptResponse,
    SaveStepRequest,
    SetTopicStatusRequest,
    StartAttemptRequest,
    StartAttemptResponse,
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
        unit_id=req.unit_id,
        lesson_index=req.lesson_index,
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
            unit_id=req.unit_id,
            lesson_index=req.lesson_index,
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


@router.post("/attempts/save-step", status_code=204)
async def save_step(
    req: SaveStepRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Checkpoint: persist the current step_log for an in-progress attempt.

    Call this after each step the student completes so their progress is saved
    and can be restored if they log out mid-problem.
    """
    repo = AttemptRepository(db)
    await repo.update_step_log(req.attempt_id, req.step_log)
    await db.commit()


@router.get(
    "/users/{user_id}/units/{unit_id}/lessons/{lesson_index}/resume",
    response_model=ResumeAttemptResponse,
)
async def resume_attempt(
    user_id: uuid.UUID,
    unit_id: str,
    lesson_index: int,
    level: int,
    db: AsyncSession = Depends(get_db),
) -> ResumeAttemptResponse:
    """
    Return the student's latest in-progress attempt for a lesson/level.

    The frontend calls this on load to restore UI state (completed steps, answers).
    Returns 404 if there is no in-progress attempt.
    """
    repo = AttemptRepository(db)
    attempt = await repo.get_in_progress(user_id, unit_id, lesson_index, level)
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
) -> MasteryState:
    """Return mastery state for user/unit/lesson. Returns default (0 attempts, 0% baseline) when no record exists."""
    state = await service.get_mastery(user_id, unit_id, lesson_index)
    if state is None:
        from datetime import datetime
        return MasteryState(
            user_id=user_id,
            unit_id=unit_id,
            lesson_index=lesson_index,
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


# ── Lesson Progress endpoints ───────────────────────────────────

@router.get(
    "/users/{user_id}/progress",
    response_model=list[LessonProgressOut],
)
async def get_all_progress(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[LessonProgressOut]:
    """Return all lesson progress for a user across every unit."""
    try:
        repo = TopicProgressRepository(db)
        records = await repo.get_all_for_user(user_id)
        return [LessonProgressOut(lesson_index=r.lesson_index, status=r.status) for r in records]
    except Exception as e:
        logger.warning("get_all_progress_failed", user_id=str(user_id), error=str(e))
        return []


@router.get(
    "/users/{user_id}/units/{unit_id}/progress",
    response_model=list[LessonProgressOut],
)
async def get_unit_progress(
    user_id: uuid.UUID,
    unit_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[LessonProgressOut]:
    """Return lesson completion statuses for all lessons in a unit, sorted by lesson_index."""
    repo = TopicProgressRepository(db)
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
    db: AsyncSession = Depends(get_db),
) -> LessonProgressOut:
    """Upsert a lesson's completion status (not-started / in-progress / completed)."""
    repo = TopicProgressRepository(db)
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
    db: AsyncSession = Depends(get_db),
) -> UnlockLevel3Response:
    """
    Permanently mark Level 3 as unlocked for a student/lesson.
    One-way latch — cannot be reversed.
    """
    from datetime import datetime
    now = datetime.utcnow()
    repo = MasteryRepository(db)
    existing = await repo.get_for_topic(user_id, unit_id, lesson_index)
    if existing is None:
        new_mastery = SkillMastery(
            user_id=user_id,
            unit_id=unit_id,
            lesson_index=lesson_index,
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
