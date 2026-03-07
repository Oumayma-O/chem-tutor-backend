"""
ProblemDeliveryService — orchestrates the full problem delivery pipeline.

Encapsulates:
  - Cap check (playlist limit)
  - Cache lookup (Level 1)
  - Lesson context fetch (key_equations, objectives, key_rules, misconceptions)
  - Problem generation (via ProblemGenerationService)
  - Dedup guard
  - Playlist append + navigation metadata
  - Background tasks: cache store, generation log, cache backfill
"""

from __future__ import annotations

import time
import uuid as _uuid

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.tutor import GenerateProblemRequest, ProblemDeliveryResponse, ProblemOutput
from app.infrastructure.database.repositories.unit_repo import LessonRepository
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository
from app.infrastructure.database.repositories.playlist_repo import UserLessonPlaylistRepository
from app.services.ai.problem_generation.service import (
    ProblemGenerationService,
    enforce_step_types,
)
from app.services.problem_cache_service import ProblemCacheService

logger = get_logger(__name__)


class ProblemDeliveryService:
    def __init__(self, db: AsyncSession, gen_service: ProblemGenerationService) -> None:
        self._db = db
        self._gen = gen_service
        self._cache = ProblemCacheService(db)
        self._lessons = LessonRepository(db)

    @staticmethod
    def _build_lesson_context(lesson: object | None) -> dict | None:
        """Normalize lesson metadata used by generation prompts."""
        if lesson is None:
            return None
        return {
            "equations": getattr(lesson, "key_equations", None) or [],
            "objectives": getattr(lesson, "objectives", None) or [],
            "key_rules": getattr(lesson, "key_rules", None) or [],
            "misconceptions": getattr(lesson, "misconceptions", None) or [],
        }

    async def _load_lesson_and_context(self, unit_id: str, lesson_index: int) -> tuple[object | None, dict | None]:
        """Fetch lesson once and derive standardized generation context."""
        lesson = await self._lessons.get_by_index(unit_id, lesson_index)
        return lesson, self._build_lesson_context(lesson)

    async def _generate_problem(
        self,
        *,
        unit_id: str,
        lesson_index: int,
        topic_name: str,
        level: int,
        difficulty: str,
        lesson_context: dict | None,
        interests: list[str] | None = None,
        grade_level: str | None = None,
        focus_areas: list[str] | None = None,
        problem_style: str | None = None,
        blueprint: str | None = None,
    ) -> ProblemOutput:
        """Shared wrapper around AI generation call."""
        return await self._gen.generate(
            unit_id=unit_id,
            lesson_index=lesson_index,
            topic_name=topic_name,
            level=level,  # type: ignore[arg-type]
            difficulty=difficulty,  # type: ignore[arg-type]
            interests=interests,
            grade_level=grade_level,
            focus_areas=focus_areas,
            problem_style=problem_style,
            lesson_context=lesson_context,
            db=self._db,
            blueprint=blueprint,
        )

    async def deliver_worked_example(
        self,
        unit_id: str,
        lesson_index: int,
        background_tasks: BackgroundTasks,
    ) -> ProblemOutput:
        """Cache-first Level 1 worked example for the lesson side panel."""
        problem = await self._cache.get_or_none(
            unit_id=unit_id,
            lesson_index=lesson_index,
            difficulty="medium",
            level=1,
            context_tag=None,
            exclude_ids=None,
        )
        if problem:
            return enforce_step_types(problem, 1)

        lesson, lesson_context = await self._load_lesson_and_context(unit_id, lesson_index)
        topic_name = lesson.title if lesson else ""
        lesson_blueprint = getattr(lesson, "blueprint", None) or "solver"

        problem = await self._generate_problem(
            unit_id=unit_id,
            lesson_index=lesson_index,
            topic_name=topic_name,
            level=1,
            difficulty="medium",
            lesson_context=lesson_context,
            blueprint=lesson_blueprint,
        )
        enforce_step_types(problem, 1)

        stub_req = GenerateProblemRequest(
            unit_id=unit_id,
            lesson_index=lesson_index,
            topic_name=topic_name,
            difficulty="medium",
            level=1,
        )
        background_tasks.add_task(_store_in_cache, problem, stub_req, self._db)
        return problem

    async def deliver(
        self,
        req: GenerateProblemRequest,
        background_tasks: BackgroundTasks,
    ) -> ProblemDeliveryResponse:
        """Full delivery pipeline: cap check → cache → generate → playlist append."""
        playlist_repo = UserLessonPlaylistRepository(self._db) if req.user_id else None
        context_tag = req.interests[0] if req.interests else None
        _settings = get_settings()
        max_p = {1: _settings.l1_max_problems, 2: _settings.l2_max_problems, 3: _settings.l3_max_problems}.get(req.level, _settings.l2_max_problems)
        exclude = set(req.exclude_ids or [])

        # Derive difficulty from mastery for L2/L3 — backend is the source of truth.
        # L1 (worked examples) always uses "medium"; no mastery tracking there.
        effective_difficulty = req.difficulty
        if req.user_id and req.level >= 2:
            mastery_record = await MasteryRepository(self._db).get_for_topic(
                req.user_id, req.unit_id, req.lesson_index
            )
            if mastery_record:
                effective_difficulty = mastery_record.current_difficulty

        # ── Cap check ──────────────────────────────────────────
        if playlist_repo and req.user_id:
            playlist = await playlist_repo.get(
                req.user_id, req.unit_id, req.lesson_index, req.level, effective_difficulty
            )
            if playlist and len(playlist.problems) >= max_p:
                ci = playlist.current_index
                problem = ProblemOutput.model_validate(playlist.problems[ci])
                enforce_step_types(problem, req.level)
                total = len(playlist.problems)
                return ProblemDeliveryResponse(
                    problem=problem,
                    current_index=ci, total=total, max_problems=max_p,
                    has_prev=ci > 0, has_next=ci < total - 1, at_limit=True,
                )

        # ── Cache (Level 1 only) ───────────────────────────────
        problem: ProblemOutput | None = None
        if req.level == 1:
            problem = await self._cache.get_or_none(
                unit_id=req.unit_id,
                lesson_index=req.lesson_index,
                difficulty=effective_difficulty,
                level=1,
                context_tag=context_tag,
                exclude_ids=exclude or None,
            )
            if problem:
                enforce_step_types(problem, 1)
                if await self._cache.needs_backfill(
                    req.unit_id, req.lesson_index, effective_difficulty, 1, context_tag
                ):
                    background_tasks.add_task(
                        _backfill_cache, req, self._gen, self._db, context_tag
                    )

        # ── Generate ───────────────────────────────────────────
        elapsed_s = 0.0
        if problem is None:
            lesson_context = req.lesson_context.model_dump() if req.lesson_context else None
            lesson_obj = None
            if lesson_context is None:
                lesson_obj, lesson_context = await self._load_lesson_and_context(req.unit_id, req.lesson_index)

            blueprint = getattr(lesson_obj, "blueprint", None) or "solver"

            t0 = time.perf_counter()
            problem = await self._generate_problem(
                unit_id=req.unit_id,
                lesson_index=req.lesson_index,
                topic_name=req.topic_name,
                level=req.level,
                difficulty=effective_difficulty,
                interests=req.interests or None,
                grade_level=req.grade_level,
                focus_areas=req.focus_areas or None,
                problem_style=req.problem_style,
                lesson_context=lesson_context,
                blueprint=blueprint,
            )
            elapsed_s = round(time.perf_counter() - t0, 3)

            # Dedup guard
            if exclude and problem.id in exclude:
                problem.id = f"{problem.id}-{_uuid.uuid4().hex[:8]}"
                logger.info("problem_id_deduplicated", new_id=problem.id)

            background_tasks.add_task(_store_in_cache, problem, req, self._db)
            background_tasks.add_task(
                _log_generation, problem, req, elapsed_s,
                self._gen.provider_name, self._gen.model_name, self._gen.prompt_version,
            )

        # ── Playlist append ────────────────────────────────────
        if playlist_repo and req.user_id:
            updated = await playlist_repo.append_and_advance(
                user_id=req.user_id,
                unit_id=req.unit_id,
                lesson_index=req.lesson_index,
                level=req.level,
                difficulty=effective_difficulty,
                problem_data=problem.model_dump(by_alias=True),
            )
            await self._db.commit()
            total = len(updated.problems)
            ci = updated.current_index
            return ProblemDeliveryResponse(
                problem=problem,
                current_index=ci, total=total, max_problems=max_p,
                has_prev=ci > 0, has_next=ci < total - 1, at_limit=total >= max_p,
            )

        return ProblemDeliveryResponse(problem=problem)


# ── Background helpers ─────────────────────────────────────────────────────────

async def _store_in_cache(
    problem: ProblemOutput,
    req: GenerateProblemRequest,
    db: AsyncSession,
) -> None:
    try:
        await ProblemCacheService(db).store(problem, req.unit_id, req.lesson_index)
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
            session.add(GenerationLog(
                problem_id=problem.id,
                unit_id=req.unit_id,
                lesson_index=req.lesson_index,
                level=req.level,
                difficulty=req.difficulty,
                provider=provider,
                model_name=model,
                prompt_version=prompt_version,
                execution_time_s=elapsed_s,
                problem_json=problem.model_dump(by_alias=True),
            ))
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
            unit_id=req.unit_id,
            lesson_index=req.lesson_index,
            topic_name=req.topic_name,
            level=1,
            difficulty=req.difficulty,
            interests=[context_tag] if context_tag else None,
            grade_level=req.grade_level,
        )
        await ProblemCacheService(db).store(problem, req.unit_id, req.lesson_index)
        logger.info("cache_backfilled", unit=req.unit_id, lesson=req.lesson_index)
    except Exception as exc:
        logger.warning("cache_backfill_failed", error=str(exc))
