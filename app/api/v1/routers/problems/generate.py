"""
Problems: cache-aware problem generation with playlist tracking.

Generation rules:
  - Level 1: max 3 worked examples per (user, chapter, topic, difficulty) slot.
  - Level 2/3: max 5 problems per slot.
  - Once the cap is reached, generation returns the current playlist position
    (frontend should navigate with /navigate instead of calling /generate again).
  - When user_id is absent, cap enforcement and playlist tracking are skipped
    (anonymous / preview mode).
"""

import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.tutor import GenerateProblemRequest, ProblemDeliveryResponse, ProblemOutput
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.chapter_repo import (
    CurriculumDocumentRepository,
    TopicRepository,
)
from app.infrastructure.database.repositories.playlist_repo import (
    MAX_PROBLEMS_PER_LEVEL,
    UserTopicPlaylistRepository,
)
from app.services.ai.problem_generation.service import (
    ProblemGenerationService,
    enforce_step_types,
    get_problem_generation_service,
)
from app.services.problem_cache_service import ProblemCacheService

logger = get_logger(__name__)
router = APIRouter()


@router.get("/reference", response_model=ProblemOutput)
async def get_reference_example(
    background_tasks: BackgroundTasks,
    chapter_id: str = Query(...),
    topic_index: int = Query(...),
    db: AsyncSession = Depends(get_db),
    gen_service: ProblemGenerationService = Depends(get_problem_generation_service),
) -> ProblemOutput:
    """
    Return a Level 1 worked example for the topic (reference problem for the panel).

    Cache-first: serves from problem cache when available; otherwise generates and caches.
    """
    cache = ProblemCacheService(db)
    problem = await cache.get_or_none(
        chapter_id=chapter_id,
        topic_index=topic_index,
        difficulty="medium",
        level=1,
        context_tag=None,
        exclude_ids=None,
    )
    if problem:
        enforce_step_types(problem, 1)
        return problem

    topic_repo = TopicRepository(db)
    topic = await topic_repo.get_by_index(chapter_id, topic_index)
    topic_name = topic.title if topic else ""

    doc_repo = CurriculumDocumentRepository(db)
    rag_context = await doc_repo.build_rag_context(chapter_id=chapter_id, topic_id=None)
    if topic and topic.key_equations:
        rag_context.setdefault("equations", []).extend(topic.key_equations)

    try:
        problem = await gen_service.generate(
            chapter_id=chapter_id,
            topic_index=topic_index,
            topic_name=topic_name,
            level=1,
            difficulty="medium",
            interests=None,
            grade_level=None,
            focus_areas=None,
            problem_style=None,
            rag_context=rag_context,
        )
    except Exception as exc:
        logger.error("reference_generation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate reference example. Please try again.",
        )

    enforce_step_types(problem, 1)
    req = GenerateProblemRequest(
        chapter_id=chapter_id,
        topic_index=topic_index,
        topic_name=topic_name,
        difficulty="medium",
        level=1,
    )
    background_tasks.add_task(_store_in_cache, problem, req, db)
    return problem


@router.post("/generate", response_model=ProblemDeliveryResponse)
async def generate_problem(
    req: GenerateProblemRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    gen_service: ProblemGenerationService = Depends(get_problem_generation_service),
) -> ProblemDeliveryResponse:
    """
    Deliver a problem at the requested level.

    When user_id is provided:
      1. Check if the playlist cap is reached → return current position if so.
      2. Otherwise generate / serve from cache and append to playlist.
      3. Return ProblemDeliveryResponse with navigation metadata.

    When user_id is absent (preview/anonymous):
      - Skip cap check and playlist tracking.
      - Serve from cache (L1) or generate fresh (L2/L3).
    """
    cache = ProblemCacheService(db)
    playlist_repo = UserTopicPlaylistRepository(db) if req.user_id else None
    context_tag = req.interests[0] if req.interests else None
    max_p = MAX_PROBLEMS_PER_LEVEL.get(req.level, 5)

    # ── Cap check: if user has hit the limit, return current playlist position ──
    if playlist_repo and req.user_id:
        playlist = await playlist_repo.get(
            req.user_id, req.chapter_id, req.topic_index, req.level, req.difficulty
        )
        if playlist and len(playlist.problems) >= max_p:
            ci = playlist.current_index
            problem = ProblemOutput.model_validate(playlist.problems[ci])
            enforce_step_types(problem, req.level)
            total = len(playlist.problems)
            return ProblemDeliveryResponse(
                problem=problem,
                current_index=ci,
                total=total,
                max_problems=max_p,
                has_prev=ci > 0,
                has_next=ci < total - 1,
                at_limit=True,
            )

    # ── Level 1: cache-first for worked examples ───────────────
    problem: ProblemOutput | None = None
    if req.level == 1:
        exclude = set(req.exclude_ids or [])
        problem = await cache.get_or_none(
            chapter_id=req.chapter_id,
            topic_index=req.topic_index,
            difficulty=req.difficulty,
            level=1,
            context_tag=context_tag,
            exclude_ids=exclude or None,
        )
        if problem:
            enforce_step_types(problem, 1)
            if await cache.needs_backfill(
                req.chapter_id, req.topic_index, req.difficulty, 1, context_tag
            ):
                background_tasks.add_task(
                    _backfill_cache, req, gen_service, db, context_tag
                )

    # ── Fresh generation (L2/L3 always, L1 on cache miss) ─────
    elapsed_s = 0.0
    if problem is None:
        try:
            rag_context = req.rag_context
            if rag_context is None:
                doc_repo = CurriculumDocumentRepository(db)
                topic_repo = TopicRepository(db)
                rag_context = await doc_repo.build_rag_context(
                    chapter_id=req.chapter_id,
                    topic_id=None,
                )
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

        background_tasks.add_task(_store_in_cache, problem, req, db)
        background_tasks.add_task(
            _log_generation,
            problem, req, elapsed_s,
            gen_service.provider_name,
            gen_service.model_name,
            gen_service.prompt_version,
        )

    # ── Append to user playlist and return with navigation metadata ─
    if playlist_repo and req.user_id:
        updated_playlist = await playlist_repo.append_and_advance(
            user_id=req.user_id,
            chapter_id=req.chapter_id,
            topic_index=req.topic_index,
            level=req.level,
            difficulty=req.difficulty,
            problem_data=problem.model_dump(by_alias=True),
        )
        await db.commit()
        total = len(updated_playlist.problems)
        ci = updated_playlist.current_index
        return ProblemDeliveryResponse(
            problem=problem,
            current_index=ci,
            total=total,
            max_problems=max_p,
            has_prev=ci > 0,
            has_next=ci < total - 1,
            at_limit=total >= max_p,
        )

    # Anonymous / no user_id: return minimal wrapper
    return ProblemDeliveryResponse(problem=problem)


# ── Background helpers ─────────────────────────────────────────

async def _store_in_cache(
    problem: ProblemOutput,
    req: GenerateProblemRequest,
    db: AsyncSession,
) -> None:
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
            provider=provider, model=model,
            prompt_version=prompt_version, execution_time_s=elapsed_s,
        )
    except Exception as exc:
        logger.warning("generation_log_failed", error=str(exc))


async def _backfill_cache(
    req: GenerateProblemRequest,
    gen_service: ProblemGenerationService,
    db: AsyncSession,
    context_tag: str | None,
) -> None:
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
