"""
GET /problems/reference-card

Returns a conceptual "fiche de cours" for a lesson.

Cache strategy (fetch-or-generate):
  1. 404 immediately if (unit_id, lesson_index) has no corresponding Lesson row.
     Reference cards must not be generated for ghost/non-existent lessons.
  2. If Lesson.reference_card_json is populated, return it instantly (< 5 ms).
  3. Otherwise call the LLM, persist the card on the Lesson row, and return it.

The card lives directly on the Lesson row (1-to-1 relationship). Cascade delete
is handled automatically — deleting a Lesson removes its reference card too.
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.tutor.problems import ReferenceCardOutput
from app.infrastructure.database.connection import get_db, AsyncSessionFactory
from app.infrastructure.database.repositories.unit_repo import LessonRepository
from app.services.ai.reference_card.service import generate_reference_card

logger = get_logger(__name__)

router = APIRouter()


@router.get("/reference-card", response_model=ReferenceCardOutput)
async def get_reference_card(
    unit_id: str = Query(..., description="Unit slug, e.g. ap-unit-1"),
    lesson_index: int = Query(..., description="0-based lesson index within the unit"),
    lesson_name: str = Query(..., description="Human-readable lesson name for first-time generation"),
    db: AsyncSession = Depends(get_db),
) -> ReferenceCardOutput:
    """
    Return the study reference card for a lesson.

    - 404 if lesson does not exist (no ghost generation).
    - Cache hit  → returned instantly from Lesson.reference_card_json (< 5 ms).
    - Cache miss → LLM generates it (~2 s), persisted on the Lesson row, then returned.

    Query params:
      unit_id      — unit slug, e.g. `unit-gas-laws`
      lesson_index — 0-based lesson index within the unit
      lesson_name  — human-readable name used only on first generation (e.g. `Boyle's Law`)
    """
    repo = LessonRepository(db)
    lesson = await repo.get_by_index(unit_id, lesson_index)

    # ── 1. Guard: no lesson → no card ─────────────────────────
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson not found for unit '{unit_id}', index {lesson_index}.",
        )

    # ── 2. Cache hit: card already stored on the lesson row ───
    if lesson.reference_card_json:
        return ReferenceCardOutput.model_validate(lesson.reference_card_json)

    # ── 3. LLM generation — shielded from client disconnect ──────────────────
    # asyncio.shield() wraps only the LLM call so it keeps running even if the
    # browser drops the connection mid-flight (hard refresh, fast nav).  The
    # generated card is returned to the client as soon as the LLM finishes —
    # DB persistence is fire-and-forget (asyncio.create_task) so it never adds
    # latency to the HTTP response.
    key_equations: list[str] = lesson.key_equations or []
    lesson_blueprint: str = getattr(lesson, "blueprint", None) or "solver"

    card: ReferenceCardOutput = await asyncio.shield(
        generate_reference_card(
            lesson_name=lesson_name,
            unit_id=unit_id,
            lesson_index=lesson_index,
            key_equations=key_equations if key_equations else None,
            blueprint=lesson_blueprint,
        )
    )

    # Persist in the background — do NOT block the response on DB writes.
    # Uses a fresh AsyncSessionFactory session so it survives client disconnect.
    card_dict = card.model_dump()

    async def _persist() -> None:
        try:
            async with AsyncSessionFactory() as fresh_db:
                fresh_repo = LessonRepository(fresh_db)
                fresh_lesson = await fresh_repo.get_by_index(unit_id, lesson_index)
                if fresh_lesson:
                    await fresh_repo.save_reference_card(fresh_lesson, card_dict)
                    await fresh_db.commit()
            logger.info(
                "reference_card_saved",
                unit_id=unit_id,
                lesson_index=lesson_index,
                lesson=lesson_name,
            )
        except Exception as exc:
            logger.error(
                "reference_card_save_failed",
                unit_id=unit_id,
                lesson_index=lesson_index,
                lesson=lesson_name,
                error=str(exc),
            )

    asyncio.create_task(_persist())

    return card
