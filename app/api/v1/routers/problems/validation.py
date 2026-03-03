"""Problems: step answer validation."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import get_logger
from app.domain.schemas.tutor import ValidateAnswerRequest, ValidationOutput
from app.services.ai.step_validation.service import (
    StepValidationService,
    get_step_validation_service,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/validate-step", response_model=ValidationOutput)
async def validate_step(
    req: ValidateAnswerRequest,
    service: StepValidationService = Depends(get_step_validation_service),
) -> ValidationOutput:
    try:
        return await service.validate(
            student_answer=req.student_answer,
            correct_answer=req.correct_answer,
            step_label=req.step_label,
            step_type=req.step_type,
            problem_context=req.problem_context,
        )
    except Exception as exc:
        logger.error("step_validation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Validation service unavailable.",
        )
