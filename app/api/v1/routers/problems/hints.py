"""Problems: hint generation."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import get_logger
from app.domain.schemas.tutor import GenerateHintRequest, HintOutput
from app.services.ai.hint_generation.service import (
    HintGenerationService,
    get_hint_generation_service,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/hint", response_model=HintOutput)
async def generate_hint(
    req: GenerateHintRequest,
    service: HintGenerationService = Depends(get_hint_generation_service),
) -> HintOutput:
    try:
        return await service.generate(
            step_label=req.step_label,
            step_instruction=req.step_instruction,
            student_input=req.student_input,
            correct_answer=req.correct_answer,
            attempt_count=req.attempt_count,
            problem_context=req.problem_context,
            interests=req.interests or None,
            grade_level=req.grade_level,
            lesson_context=req.lesson_context,
            error_category=req.error_category,
            misconception_tag=req.misconception_tag,
        )
    except Exception as exc:
        logger.error("hint_generation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hint service unavailable.",
        )
