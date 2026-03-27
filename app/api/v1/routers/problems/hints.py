"""Problems: hint generation."""

from fastapi import APIRouter, Depends, status

from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.tutor import GenerateHintRequest, HintOutput
from app.services.ai.hint_generation.service import (
    HintGenerationService,
    get_hint_generation_service,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/hint", response_model=HintOutput)
@map_unexpected_errors(
    logger=logger,
    event="hint_generation_failed",
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="Hint service unavailable.",
)
async def generate_hint(
    req: GenerateHintRequest,
    service: HintGenerationService = Depends(get_hint_generation_service),
) -> HintOutput:
    return await service.generate(
        step_label=req.step_label,
        step_instruction=req.step_instruction,
        step_explanation=req.step_explanation,
        student_input=req.student_input,
        correct_answer=req.correct_answer,
        attempt_count=req.attempt_count,
        problem_context=req.problem_context,
        interests=req.interests or None,
        grade_level=req.grade_level,
        key_rule=req.key_rule,
        error_category=req.error_category,
        misconception_tag=req.misconception_tag,
        validation_feedback=req.validation_feedback,
        step_number=req.step_number,
        total_steps=req.total_steps,
        step_type=req.step_type,
        prior_steps_summary=req.prior_steps_summary,
    )
