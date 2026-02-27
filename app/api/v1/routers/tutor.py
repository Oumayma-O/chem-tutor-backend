"""
Tutor router — AI-powered tutor endpoints.

Routers contain ZERO business logic. They:
  - Validate input (via Pydantic)
  - Call services
  - Return responses

No DB calls, no prompt strings, no LLM code here.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.logging import get_logger
from app.domain.schemas.tutor import (
    ClassInsightsOutput,
    ClassifyErrorsRequest,
    ErrorClassificationOutput,
    ExitTicketOutput,
    GenerateExitTicketRequest,
    GenerateHintRequest,
    GenerateProblemRequest,
    GenerateInsightsRequest,
    HintOutput,
    ProblemOutput,
    ValidateAnswerRequest,
    ValidationOutput,
)
from app.services.ai.tutor_service import TutorService, get_tutor_service

logger = get_logger(__name__)
router = APIRouter(prefix="/tutor")


@router.post("/generate-problem", response_model=ProblemOutput)
async def generate_problem(
    req: GenerateProblemRequest,
    service: TutorService = Depends(get_tutor_service),
) -> ProblemOutput:
    try:
        return await service.generate_problem(
            chapter_id=req.chapter_id,
            topic_index=req.topic_index,
            topic_name=req.topic_name,
            level=req.level,
            difficulty=req.difficulty,
            interests=req.interests or None,
            grade_level=req.grade_level,
            focus_areas=req.focus_areas or None,
            problem_style=req.problem_style,
            rag_context=req.rag_context,
        )
    except Exception as exc:
        logger.error("generate_problem_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate problem. Please try again.",
        )


@router.post("/validate-answer", response_model=ValidationOutput)
async def validate_answer(
    req: ValidateAnswerRequest,
    service: TutorService = Depends(get_tutor_service),
) -> ValidationOutput:
    try:
        return await service.validate_answer(
            student_answer=req.student_answer,
            correct_answer=req.correct_answer,
            step_label=req.step_label,
            step_type=req.step_type,
            problem_context=req.problem_context,
        )
    except Exception as exc:
        logger.error("validate_answer_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Validation service unavailable.",
        )


@router.post("/generate-hint", response_model=HintOutput)
async def generate_hint(
    req: GenerateHintRequest,
    service: TutorService = Depends(get_tutor_service),
) -> HintOutput:
    try:
        return await service.generate_hint(
            step_label=req.step_label,
            step_instruction=req.step_instruction,
            student_input=req.student_input,
            correct_answer=req.correct_answer,
            attempt_count=req.attempt_count,
            problem_context=req.problem_context,
            interests=req.interests,
            grade_level=req.grade_level,
            rag_context=req.rag_context,
            error_category=req.error_category,
            misconception_tag=req.misconception_tag,
        )
    except Exception as exc:
        logger.error("generate_hint_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hint service unavailable.",
        )


@router.post("/classify-errors", response_model=ErrorClassificationOutput)
async def classify_errors(
    req: ClassifyErrorsRequest,
    service: TutorService = Depends(get_tutor_service),
) -> ErrorClassificationOutput:
    try:
        return await service.classify_errors(
            incorrect_steps=req.steps,
            all_steps=req.all_steps,
            problem_context=req.problem_context,
        )
    except Exception as exc:
        logger.error("classify_errors_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error classification service unavailable.",
        )


@router.post("/generate-exit-ticket", response_model=ExitTicketOutput)
async def generate_exit_ticket(
    req: GenerateExitTicketRequest,
    service: TutorService = Depends(get_tutor_service),
) -> ExitTicketOutput:
    try:
        return await service.generate_exit_ticket(
            chapter_id=req.chapter_id,
            topic_name=req.topic_name,
            difficulty=req.difficulty,
            question_count=req.question_count,
            format=req.format,
        )
    except Exception as exc:
        logger.error("generate_exit_ticket_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Exit ticket generation failed.",
        )


@router.post("/generate-class-insights", response_model=ClassInsightsOutput)
async def generate_class_insights(
    req: GenerateInsightsRequest,
    service: TutorService = Depends(get_tutor_service),
) -> ClassInsightsOutput:
    try:
        return await service.generate_class_insights(
            student_count=req.student_count,
            class_mastery=req.class_mastery,
            error_frequencies=req.error_frequencies,
            misconception_data=req.misconception_data,
        )
    except Exception as exc:
        logger.error("generate_class_insights_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Insight generation failed.",
        )
