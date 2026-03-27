"""Background-task helpers for cache writes.

DeliveryCacheAdapter (the zero-value pass-through wrapper) has been removed.
ProblemDeliveryService now holds ProblemCacheService directly.

These module-level coroutines remain here because they open their own DB
session (background tasks cannot reuse the request-scoped session).
"""

from app.domain.schemas.tutor import GenerateProblemRequest, ProblemOutput
from app.infrastructure.database.connection import fresh_session
from app.services.ai.problem_generation.service import ProblemGenerationService
from app.services.problem_delivery.cache import ProblemCacheService


async def store_in_cache(problem: ProblemOutput, req: GenerateProblemRequest) -> None:
    async with fresh_session() as session:
        await ProblemCacheService(session).store(problem, req.unit_id, req.lesson_index)


async def backfill_cache(
    req: GenerateProblemRequest,
    gen_service: ProblemGenerationService,
    context_tag: str | None,
) -> None:
    problem = await gen_service.generate(
        unit_id=req.unit_id,
        lesson_index=req.lesson_index,
        lesson_name=req.lesson_name,
        level=1,
        difficulty=req.difficulty,
        interests=[context_tag] if context_tag else None,
        grade_level=req.grade_level,
    )
    async with fresh_session() as session:
        await ProblemCacheService(session).store(problem, req.unit_id, req.lesson_index)
