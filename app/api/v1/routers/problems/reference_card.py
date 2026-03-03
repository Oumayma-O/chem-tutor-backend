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
from app.infrastructure.database.repositories.chapter_repo import TopicRepository
from app.services.ai.reference_card.service import generate_reference_card

router = APIRouter()


@router.get("/reference-card", response_model=ReferenceCardOutput)
async def get_reference_card(
    chapter_id: str,
    topic_index: int,
    topic_name: str,
    db: AsyncSession = Depends(get_db),
) -> ReferenceCardOutput:
    """
    Return the study reference card for a topic.

    - If the card is already cached in the DB it is returned instantly (< 5 ms).
    - On first call for a topic the LLM generates it (~2 s) and it is persisted.

    Query params:
      chapter_id  — chapter slug, e.g. `chemical-kinetics`
      topic_index — 0-based topic index within the chapter
      topic_name  — human-readable name used only when generating (e.g. `Zero-Order Kinetics`)
    """
    repo = TopicRepository(db)
    topic = await repo.get_by_index(chapter_id, topic_index)

    # ── Cache hit ──────────────────────────────────────────────
    if topic is not None and topic.reference_card_json:
        return ReferenceCardOutput.model_validate(topic.reference_card_json)

    # ── LLM generation ────────────────────────────────────────
    key_equations: list[str] = (topic.key_equations or []) if topic else []

    card = await generate_reference_card(
        topic_name=topic_name,
        chapter_id=chapter_id,
        topic_index=topic_index,
        key_equations=key_equations if key_equations else None,
    )

    # Persist if the topic row exists in the DB
    if topic is not None:
        await repo.save_reference_card(chapter_id, topic_index, card.model_dump())

    return card
