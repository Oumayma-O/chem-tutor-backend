"""
GET /problems/reference-card

Returns a conceptual "fiche de cours" for a topic.

Cache strategy:
  1. Look up the topic row — if reference_card_json is populated, return it immediately.
  2. Otherwise call the LLM chain, persist the result, and return it.

The card is generated ONCE per topic and never regenerated automatically.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.tutor.problems import ReferenceCardOutput
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.unit_repo import LessonRepository
from app.services.ai.reference_card.service import generate_reference_card

router = APIRouter()


@router.get("/reference-card", response_model=ReferenceCardOutput)
async def get_reference_card(
    unit_id: str,
    lesson_index: int,
    topic_name: str,
    db: AsyncSession = Depends(get_db),
) -> ReferenceCardOutput:
    """
    Return the study reference card for a lesson.

    - If the card is already cached in the DB it is returned instantly (< 5 ms).
    - On first call for a lesson the LLM generates it (~2 s) and it is persisted.

    Query params:
      unit_id      — unit slug, e.g. `unit-gas-laws`
      lesson_index — 0-based lesson index within the unit
      topic_name   — human-readable name used only when generating (e.g. `Boyle's Law`)
    """
    repo = LessonRepository(db)
    lesson = await repo.get_by_index(unit_id, lesson_index)

    # ── Cache hit ──────────────────────────────────────────────
    if lesson is not None and lesson.reference_card_json:
        return ReferenceCardOutput.model_validate(lesson.reference_card_json)

    # ── LLM generation ────────────────────────────────────────
    key_equations: list[str] = (lesson.key_equations or []) if lesson else []

    card = await generate_reference_card(
        topic_name=topic_name,
        unit_id=unit_id,
        lesson_index=lesson_index,
        key_equations=key_equations if key_equations else None,
    )

    # Persist if the lesson row exists in the DB
    if lesson is not None:
        await repo.save_reference_card(unit_id, lesson_index, card.model_dump())

    return card
