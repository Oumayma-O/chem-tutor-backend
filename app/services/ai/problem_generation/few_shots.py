"""
Direct DB query for few-shot examples — no in-memory cache.

A single async helper called from service.generate() at request time.
One extra DB query per generation is negligible vs. the LLM call latency.

Fallback chain:
  1. Exact (unit_id, lesson_index, difficulty, level)
  2. Same unit + lesson + difficulty (any level)
  3. Same unit + difficulty (any lesson / level)
  4. Any active row with matching difficulty (global fallback)
"""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def get_few_shot(
    db: AsyncSession,
    unit_id: str,
    lesson_index: int,
    difficulty: str,
    level: int,
) -> dict[str, Any] | None:
    """Return one random example_json dict, or None if no rows exist."""
    from app.infrastructure.database.models import FewShotExample  # avoid circular import

    base = select(FewShotExample).where(FewShotExample.is_active.is_(True))

    for where_clause in [
        # 1. Exact match
        (FewShotExample.unit_id == unit_id,
         FewShotExample.lesson_index == lesson_index,
         FewShotExample.difficulty == difficulty,
         FewShotExample.level == level),
        # 2. Same unit + lesson + difficulty, any level
        (FewShotExample.unit_id == unit_id,
         FewShotExample.lesson_index == lesson_index,
         FewShotExample.difficulty == difficulty),
        # 3. Same unit + difficulty, any lesson/level
        (FewShotExample.unit_id == unit_id,
         FewShotExample.difficulty == difficulty),
        # 4. Global: any active row matching difficulty
        (FewShotExample.difficulty == difficulty,),
    ]:
        result = await db.execute(base.where(*where_clause))
        rows = result.scalars().all()
        if rows:
            return random.choice(rows).example_json

    return None
