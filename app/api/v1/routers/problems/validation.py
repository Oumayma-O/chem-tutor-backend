"""Problems: step answer validation."""

from fastapi import APIRouter, Depends, status

from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.tutor import ValidateAnswerRequest, ValidationOutput
from app.services.ai.step_validation.service import (
    StepValidationService,
    get_step_validation_service,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/validate-step", response_model=ValidationOutput)
@map_unexpected_errors(
    logger=logger,
    event="step_validation_failed",
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="Validation service unavailable.",
)
async def validate_step(
    req: ValidateAnswerRequest,
    service: StepValidationService = Depends(get_step_validation_service),
) -> ValidationOutput:
    return await service.validate(
        student_answer=req.student_answer,
        correct_answer=req.correct_answer,
        step_label=req.step_label,
        step_type=req.step_type,
        problem_context=req.problem_context,
        step_instruction=req.step_instruction,
    )
