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


async def get_few_shots(
    db: AsyncSession,
    unit_id: str,
    lesson_index: int,
    difficulty: str,
    level: int,
    n: int = 2,
) -> list[dict[str, Any]]:
    """Return up to n distinct random example_json dicts (empty list if none exist).

    Fallback chain per tier — stops at the first tier that has rows.
    Picks up to n without replacement so the LLM sees varied examples.
    """
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
            sample = random.sample(rows, min(n, len(rows)))
            return [r.example_json for r in sample]

    return []
