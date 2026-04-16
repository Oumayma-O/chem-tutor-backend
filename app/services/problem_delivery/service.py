"""Thin orchestrator for problem delivery flow."""

from __future__ import annotations

import re
import uuid as _uuid
from typing import Literal

from fastapi import BackgroundTasks
from app.services.ai.shared.timing import perf_now, since
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.tutor import (
    GenerateProblemRequest,
    ProblemDeliveryResponse,
    ProblemOutput,
)
from app.domain.schemas.tutor.problems import PlaylistHydrationResponse
from app.infrastructure.database.repositories.attempt_repo import AttemptRepository
from app.services.ai.problem_generation.service import ProblemGenerationService
from app.services.ai.shared.step_types import enforce_step_types
from app.infrastructure.database.repositories.playlist_repo import UserLessonPlaylistRepository
from app.services.problem_delivery.cache import ProblemCacheService
from app.services.problem_delivery.delivery_cache_adapter import backfill_cache, store_in_cache
from app.services.problem_delivery.delivery_telemetry import DeliveryTelemetry
from app.services.problem_delivery.difficulty_policy import DifficultyPolicy
from app.services.problem_delivery.generation_orchestrator import LessonContextLoader
from app.services.problem_delivery.limits import max_problems_for_level
from app.services.classroom.class_settings import (
    get_allow_answer_reveal,
    get_max_answer_reveals_per_lesson,
    get_min_level1_examples_for_level2,
)
from app.services.problem_delivery.playlist_coordinator import PlaylistCoordinator

logger = get_logger(__name__)


def _normalize_problem_step_ids(problem: ProblemOutput) -> tuple[dict[str, str], dict[int, str]]:
    mapping: dict[str, str] = {}
    by_step_number: dict[int, str] = {}
    for step in problem.steps:
        original_id = step.id or ""
        normalized_id = f"{problem.id}-step-{step.step_number}"
        step.id = normalized_id
        if original_id:
            mapping[original_id] = normalized_id
        mapping[normalized_id] = normalized_id
        by_step_number[step.step_number] = normalized_id
    return mapping, by_step_number


def _normalize_step_log(
    step_log: list[dict] | None,
    id_mapping: dict[str, str],
    id_by_step_number: dict[int, str],
) -> list[dict]:
    normalized: list[dict] = []
    for entry in step_log or []:
        if not isinstance(entry, dict):
            continue
        out = dict(entry)
        step_id = out.get("step_id")
        if isinstance(step_id, str):
            mapped = id_mapping.get(step_id)
            if mapped:
                out["step_id"] = mapped
            else:
                match = re.fullmatch(r"step-(\d+)", step_id.strip())
                if match:
                    step_number = int(match.group(1))
                    canonical = id_by_step_number.get(step_number)
                    if canonical:
                        out["step_id"] = canonical
        normalized.append(out)
    return normalized


def _attempt_payload(
    attempt: object,
    id_mapping: dict[str, str],
    id_by_step_number: dict[int, str],
) -> dict[str, object]:
    return {
        "attempt_id": str(attempt.id),
        "problem_id": attempt.problem_id,
        "level": attempt.level,
        "is_complete": bool(attempt.is_complete),
        "step_log": _normalize_step_log(
            list(getattr(attempt, "step_log", []) or []),
            id_mapping,
            id_by_step_number,
        ),
    }


class ProblemDeliveryService:
    def __init__(self, db: AsyncSession, gen_service: ProblemGenerationService) -> None:
        self._db = db
        self._gen = gen_service
        self._difficulty = DifficultyPolicy(db)
        self._cache = ProblemCacheService(db)
        self._lesson_loader = LessonContextLoader(db)
        self._playlist = PlaylistCoordinator(db)

    async def get_playlist(
        self,
        user_id: _uuid.UUID,
        unit_id: str,
        lesson_index: int,
        level: int,
        difficulty: Literal["easy", "medium", "hard"] | None = None,
    ) -> PlaylistHydrationResponse:
        # Keep arg for API compatibility; hydration is now level-scoped, not difficulty-scoped.
        _ = difficulty
        repo = UserLessonPlaylistRepository(self._db)
        playlist = await repo.get_most_recent_for_level(
            user_id=user_id,
            unit_id=unit_id,
            lesson_index=lesson_index,
            level=level,
            difficulty=None,
        )
        if not playlist or not playlist.problems:
            return PlaylistHydrationResponse()

        parsed: list[ProblemOutput] = []
        step_id_maps: list[tuple[dict[str, str], dict[int, str]]] = []
        for payload in playlist.problems:
            if not isinstance(payload, dict):
                continue
            try:
                problem = ProblemOutput.model_validate(payload)
                id_map, id_by_step_number = _normalize_problem_step_ids(problem)
                parsed.append(enforce_step_types(problem, level))
                step_id_maps.append((id_map, id_by_step_number))
            except Exception:
                logger.warning(
                    "playlist_problem_payload_invalid",
                    user_id=str(user_id),
                    unit_id=unit_id,
                    lesson_index=lesson_index,
                    level=level,
                )

        if not parsed:
            return PlaylistHydrationResponse()

        current_index = min(max(playlist.current_index, 0), len(parsed) - 1)
        total = len(parsed)
        attempts = AttemptRepository(self._db)
        current_problem_id = parsed[current_index].id
        latest_by_problem = await attempts.get_latest_for_problems(
            user_id=user_id,
            unit_id=unit_id,
            lesson_index=lesson_index,
            level=level,
            problem_ids=[p.id for p in parsed],
        )
        current_id_map, current_id_by_step_number = step_id_maps[current_index]
        active_attempt = latest_by_problem.get(current_problem_id)
        attempts_by_problem: dict[str, dict[str, object]] = {}
        for idx, problem in enumerate(parsed):
            attempt = latest_by_problem.get(problem.id)
            if attempt is None:
                continue
            id_map, id_by_step_number = step_id_maps[idx]
            attempts_by_problem[problem.id] = _attempt_payload(attempt, id_map, id_by_step_number)
        return PlaylistHydrationResponse(
            problems=parsed,
            current_index=current_index,
            total=total,
            has_prev=current_index > 0,
            has_next=current_index < total - 1,
            attempts_by_problem=attempts_by_problem,
            active_attempt=(
                _attempt_payload(active_attempt, current_id_map, current_id_by_step_number)
                if active_attempt is not None
                else None
            ),
        )

    async def deliver_worked_example(
        self,
        unit_id: str,
        lesson_index: int,
        background_tasks: BackgroundTasks,
    ) -> ProblemOutput:
        problem = await self._cache.get_or_none(
            unit_id,
            lesson_index,
            "medium",
            1,
            None,
        )
        if problem:
            return enforce_step_types(problem, 1)

        lesson, lesson_context = await self._lesson_loader.load_lesson_and_context(unit_id, lesson_index)
        lesson_name = lesson.title if lesson else ""
        lesson_blueprint = getattr(lesson, "blueprint", None) or "solver"

        problem = await self._gen.generate(
            unit_id=unit_id,
            lesson_index=lesson_index,
            lesson_name=lesson_name,
            level=1,
            difficulty="medium",
            lesson_context=lesson_context,
            blueprint=lesson_blueprint,
            db=self._db,
        )
        enforce_step_types(problem, 1)
        background_tasks.add_task(
            store_in_cache,
            problem,
            GenerateProblemRequest(
                unit_id=unit_id,
                lesson_index=lesson_index,
                lesson_name=lesson_name,
                difficulty="medium",
                level=1,
            ),
        )
        return problem

    async def deliver(
        self,
        req: GenerateProblemRequest,
        background_tasks: BackgroundTasks,
    ) -> ProblemDeliveryResponse:
        max_p = max_problems_for_level(req.level)
        context_tag = req.interests[0] if req.interests else None
        exclude = set(req.exclude_ids or [])
        effective_difficulty = await self._difficulty.resolve(req)
        reveal = await get_allow_answer_reveal(self._db, req.class_id)
        max_reveals = await get_max_answer_reveals_per_lesson(self._db, req.class_id)
        min_l1 = await get_min_level1_examples_for_level2(self._db, req.class_id)

        resumed = await self._playlist.try_resume(
            req,
            effective_difficulty,
            max_p,
            allow_answer_reveal=reveal,
            max_answer_reveals_per_lesson=max_reveals,
            min_level1_examples_for_level2=min_l1,
        )
        if resumed:
            return resumed

        problem = None
        if req.level == 1:
            problem = await self._cache.get_or_none(
                req.unit_id,
                req.lesson_index,
                effective_difficulty,
                1,
                context_tag,
                exclude or None,
            )
            if problem:
                enforce_step_types(problem, 1)
                if await self._cache.needs_backfill(
                    unit_id=req.unit_id,
                    lesson_index=req.lesson_index,
                    difficulty=effective_difficulty,
                    level=1,
                    context_tag=context_tag,
                ):
                    background_tasks.add_task(backfill_cache, req, self._gen, context_tag)

        elapsed_s = 0.0
        if problem is None:
            lesson_context = req.lesson_context.model_dump() if req.lesson_context else None
            lesson_obj = None
            if lesson_context is None:
                lesson_obj, lesson_context = await self._lesson_loader.load_lesson_and_context(
                    req.unit_id,
                    req.lesson_index,
                )
            blueprint = getattr(lesson_obj, "blueprint", None) or "solver"
            t0 = perf_now()
            # Collect titles/statements of problems the student already saw in this slot
            # so the LLM avoids repeating the same scenario.
            previous_problems = await self._playlist.get_previous_problem_summaries(
                user_id=req.user_id,
                unit_id=req.unit_id,
                lesson_index=req.lesson_index,
                level=req.level,
                difficulty=effective_difficulty,
            )
            problem = await self._gen.generate(
                unit_id=req.unit_id,
                lesson_index=req.lesson_index,
                lesson_name=req.lesson_name,
                level=req.level,
                difficulty=effective_difficulty,
                interests=req.interests or None,
                grade_level=req.grade_level,
                focus_areas=req.focus_areas or None,
                problem_style=req.problem_style,
                lesson_context=lesson_context,
                blueprint=blueprint,
                db=self._db,
                previous_problems=previous_problems,
            )
            # Fill step.category from canonical labels when the LLM omits it; must run before cache/playlist.
            enforce_step_types(problem, req.level)
            elapsed_s = since(t0, decimals=3)
            if exclude and problem.id in exclude:
                problem.id = f"{problem.id}-{_uuid.uuid4().hex[:8]}"
                _normalize_problem_step_ids(problem)
                logger.info("problem_id_deduplicated", new_id=problem.id)

            background_tasks.add_task(store_in_cache, problem, req)
            background_tasks.add_task(
                DeliveryTelemetry.log_generation,
                problem,
                req,
                elapsed_s,
                self._gen.provider_name,
                self._gen.model_name,
                self._gen.prompt_version,
            )

        if req.user_id:
            updated = await self._playlist.persist_playlist_entry(
                user_id=req.user_id,
                unit_id=req.unit_id,
                lesson_index=req.lesson_index,
                level=req.level,
                difficulty=effective_difficulty,
                problem_data=problem.model_dump(mode="json", by_alias=False),
            )
            total = len(updated.problems)
            ci = updated.current_index
            return ProblemDeliveryResponse(
                problem=problem,
                current_index=ci,
                total=total,
                max_problems=max_p,
                has_prev=ci > 0,
                has_next=ci < total - 1,
                at_limit=total >= max_p,
                allow_answer_reveal=reveal,
                max_answer_reveals_per_lesson=max_reveals,
                min_level1_examples_for_level2=min_l1,
            )

        return ProblemDeliveryResponse(
            problem=problem,
            allow_answer_reveal=reveal,
            max_answer_reveals_per_lesson=max_reveals,
            min_level1_examples_for_level2=min_l1,
        )

