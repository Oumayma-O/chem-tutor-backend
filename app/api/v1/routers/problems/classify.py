"""Problems: thinking tracker / error classification."""

from fastapi import APIRouter, Depends, status

from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.tutor import ClassifyErrorsRequest, ErrorClassificationOutput
from app.services.ai.thinking_analysis.service import (
    ThinkingAnalysisService,
    get_thinking_analysis_service,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/classify-thinking", response_model=ErrorClassificationOutput)
@map_unexpected_errors(
    logger=logger,
    event="thinking_classification_failed",
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="Thinking analysis service unavailable.",
)
async def classify_thinking(
    req: ClassifyErrorsRequest,
    service: ThinkingAnalysisService = Depends(get_thinking_analysis_service),
) -> ErrorClassificationOutput:
    """
    Classify errors and populate the Thinking Tracker panel.
    Called by the frontend after an attempt is completed.
    """
    return await service.classify_errors(
        incorrect_steps=req.steps,
        all_steps=req.all_steps,
        problem_context=req.problem_context,
    )
