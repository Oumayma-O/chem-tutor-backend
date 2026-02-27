"""
Problems router — smart problem delivery with caching.

POST /problems/generate         → generate/serve problem (cache-aware)
POST /problems/validate-step    → validate one step answer
POST /problems/hint             → get a hint for a step
POST /problems/classify-thinking → classify errors + populate Thinking Tracker

Design:
  - Level 1 problems are served from cache; fresh generation is a fallback.
  - Level 2/3 problems are generated fresh (may be cached in background).
  - Student context (interests, grade) is fetched if user_id is provided.
  - Every fresh generation is logged to generation_logs for benchmarking.
"""

import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.tutor import (
    ClassifyErrorsRequest,
    ErrorClassificationOutput,
    GenerateHintRequest,
    GenerateProblemRequest,
    HintOutput,
    ProblemOutput,
    ValidateAnswerRequest,
    ValidationOutput,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.chapter_repo import (
    CurriculumDocumentRepository,
    TopicRepository,
)
from app.infrastructure.database.repositories.student_repo import UserProfileRepository
from app.services.ai.hint_generation_service import HintGenerationService, get_hint_generation_service
from app.services.ai.problem_generation_service import ProblemGenerationService, get_problem_generation_service
from app.services.ai.step_validation_service import StepValidationService, get_step_validation_service
from app.services.ai.thinking_analysis_service import ThinkingAnalysisService, get_thinking_analysis_service
from app.services.problem_cache_service import ProblemCacheService

logger = get_logger(__name__)
router = APIRouter(prefix="/problems")


# ── Problem Generation (cache-aware) ──────────────────────────

@router.post("/generate", response_model=ProblemOutput)
async def generate_problem(
    req: GenerateProblemRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    gen_service: ProblemGenerationService = Depends(get_problem_generation_service),
) -> ProblemOutput:
    """
    Deliver a problem at the requested level.

    1. Enriches request with student interests/grade from DB (if needed).
    2. For Level 1: tries cache first; generates fresh on miss.
    3. For Level 2/3: generates fresh (may cache in background).
    4. For Level 1: schedules cache backfill in background if below min.
    5. Logs generation metadata (provider, model, prompt version, time) in background.
    """
    cache = ProblemCacheService(db)

    # Determine context_tag from interests
    context_tag = req.interests[0] if req.interests else None

    # ── Level 1: cache-first ───────────────────────────────────
    if req.level == 1:
        cached = await cache.get_or_none(
            chapter_id=req.chapter_id,
            topic_index=req.topic_index,
            difficulty=req.difficulty,
            level=1,
            context_tag=context_tag,
        )
        if cached:
            # Schedule backfill if below minimum
            if await cache.needs_backfill(
                req.chapter_id, req.topic_index, req.difficulty, 1, context_tag
            ):
                background_tasks.add_task(
                    _backfill_cache, req, gen_service, db, context_tag
                )
            return cached

    # ── Fresh generation ───────────────────────────────────────
    try:
        rag_context = req.rag_context
        if rag_context is None:
            # Auto-fetch RAG context from curriculum documents
            doc_repo = CurriculumDocumentRepository(db)
            topic_repo = TopicRepository(db)
            rag_context = await doc_repo.build_rag_context(
                chapter_id=req.chapter_id,
                topic_id=None,
            )
            # Add key_equations from topic
            topic = await topic_repo.get_by_index(req.chapter_id, req.topic_index)
            if topic and topic.key_equations:
                rag_context.setdefault("equations", []).extend(topic.key_equations)

        t0 = time.perf_counter()
        problem = await gen_service.generate(
            chapter_id=req.chapter_id,
            topic_index=req.topic_index,
            topic_name=req.topic_name,
            level=req.level,
            difficulty=req.difficulty,
            interests=req.interests or None,
            grade_level=req.grade_level,
            focus_areas=req.focus_areas or None,
            problem_style=req.problem_style,
            rag_context=rag_context,
        )
        elapsed_s = round(time.perf_counter() - t0, 3)

    except Exception as exc:
        logger.error("problem_generation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate problem. Please try again.",
        )

    # ── Background tasks ───────────────────────────────────────
    background_tasks.add_task(_store_in_cache, problem, req, db)
    background_tasks.add_task(
        _log_generation,
        problem, req, elapsed_s,
        gen_service.provider_name,
        gen_service.model_name,
        gen_service.prompt_version,
    )

    return problem


# ── Step Validation ────────────────────────────────────────────

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


# ── Hint Generation ────────────────────────────────────────────

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
            rag_context=req.rag_context,
            error_category=req.error_category,
            misconception_tag=req.misconception_tag,
        )
    except Exception as exc:
        logger.error("hint_generation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hint service unavailable.",
        )


# ── Thinking Tracker / Error Classification ────────────────────

@router.post("/classify-thinking", response_model=ErrorClassificationOutput)
async def classify_thinking(
    req: ClassifyErrorsRequest,
    service: ThinkingAnalysisService = Depends(get_thinking_analysis_service),
) -> ErrorClassificationOutput:
    """
    Classify errors and populate the Thinking Tracker panel.
    Called by the frontend after an attempt is completed.
    """
    try:
        return await service.classify_errors(
            incorrect_steps=req.steps,
            all_steps=req.all_steps,
            problem_context=req.problem_context,
        )
    except Exception as exc:
        logger.error("thinking_classification_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Thinking analysis service unavailable.",
        )


# ── Background task helpers ────────────────────────────────────

async def _store_in_cache(
    problem: ProblemOutput,
    req: GenerateProblemRequest,
    db: AsyncSession,
) -> None:
    """Store a generated problem in the cache (runs in background)."""
    try:
        cache = ProblemCacheService(db)
        await cache.store(problem, req.chapter_id, req.topic_index)
    except Exception as exc:
        logger.warning("cache_store_failed", error=str(exc))


async def _log_generation(
    problem: ProblemOutput,
    req: GenerateProblemRequest,
    elapsed_s: float,
    provider: str,
    model: str,
    prompt_version: str,
) -> None:
    """
    Persist a generation log row for benchmarking.
    Opens its own session so it's independent of the request's session lifecycle.
    Captures provider, model, prompt version, and wall-clock time so different
    configurations can be compared offline.
    """
    from app.infrastructure.database.connection import AsyncSessionFactory
    from app.infrastructure.database.models import GenerationLog
    try:
        async with AsyncSessionFactory() as session:
            log = GenerationLog(
                problem_id=problem.id,
                chapter_id=req.chapter_id,
                topic_index=req.topic_index,
                level=req.level,
                difficulty=req.difficulty,
                provider=provider,
                model_name=model,
                prompt_version=prompt_version,
                execution_time_s=elapsed_s,
                problem_json=problem.model_dump(by_alias=True),
            )
            session.add(log)
            await session.commit()
        logger.info(
            "generation_logged",
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            execution_time_s=elapsed_s,
        )
    except Exception as exc:
        logger.warning("generation_log_failed", error=str(exc))


async def _backfill_cache(
    req: GenerateProblemRequest,
    gen_service: ProblemGenerationService,
    db: AsyncSession,
    context_tag: str | None,
) -> None:
    """Generate one additional Level 1 problem to backfill the cache."""
    try:
        problem = await gen_service.generate(
            chapter_id=req.chapter_id,
            topic_index=req.topic_index,
            topic_name=req.topic_name,
            level=1,
            difficulty=req.difficulty,
            interests=[context_tag] if context_tag else None,
            grade_level=req.grade_level,
        )
        cache = ProblemCacheService(db)
        await cache.store(problem, req.chapter_id, req.topic_index)
        logger.info("cache_backfilled", chapter=req.chapter_id, topic=req.topic_index)
    except Exception as exc:
        logger.warning("cache_backfill_failed", error=str(exc))
