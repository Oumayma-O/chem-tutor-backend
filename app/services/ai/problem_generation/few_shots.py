"""
In-memory cache for few-shot examples loaded from the DB.

Usage
-----
  # At startup (inside lifespan):
  from app.services.ai.problem_generation.few_shots import load_few_shots
  await load_few_shots(db_session)

  # At generation time (inside prompts.py):
  from app.services.ai.problem_generation.few_shots import get_few_shot
  example = get_few_shot(unit_id, lesson_index, difficulty, level)

Design
------
- All active rows are loaded once at startup into a dict keyed by
  (unit_id, lesson_index, difficulty, level).
- If no exact match, the lookup falls back through:
    1. same unit_id + lesson_index + difficulty (any level)
    2. same unit_id + difficulty (any lesson, any level)
    3. any example with the same difficulty
- Returns None when no example exists at all.
- `reload_few_shots()` can be called without restart (admin endpoint).
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger

logger = get_logger(__name__)

# key → list of example_json dicts
_store: dict[tuple[str, int, str, int], list[dict[str, Any]]] = defaultdict(list)
_loaded = False


async def load_few_shots(session: AsyncSession) -> None:
    """Load all active few-shot examples from DB into memory."""
    global _loaded
    from app.infrastructure.database.models import FewShotExample  # avoid circular import

    result = await session.execute(
        select(FewShotExample).where(FewShotExample.is_active.is_(True))
    )
    rows = result.scalars().all()

    new_store: dict[tuple[str, int, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row.unit_id, row.lesson_index, row.difficulty, row.level)
        new_store[key].append(row.example_json)

    _store.clear()
    _store.update(new_store)
    _loaded = True
    logger.info("few_shots_loaded", count=len(rows), keys=len(_store))


def get_few_shot(
    unit_id: str,
    lesson_index: int,
    difficulty: str,
    level: int,
) -> dict[str, Any] | None:
    """
    Return one random example for the given key, falling back through
    progressively looser matches.  Returns None if store is empty.
    """
    if not _loaded:
        return None

    # Exact match
    key = (unit_id, lesson_index, difficulty, level)
    if _store.get(key):
        return random.choice(_store[key])

    # Same unit + lesson + difficulty, any level
    candidates = [
        ex
        for (u, l, d, _), exs in _store.items()
        if u == unit_id and l == lesson_index and d == difficulty
        for ex in exs
    ]
    if candidates:
        return random.choice(candidates)

    # Same unit + difficulty, any lesson/level
    candidates = [
        ex
        for (u, _, d, _), exs in _store.items()
        if u == unit_id and d == difficulty
        for ex in exs
    ]
    if candidates:
        return random.choice(candidates)

    # Any example with matching difficulty (global fallback)
    candidates = [
        ex
        for (_, _, d, _), exs in _store.items()
        if d == difficulty
        for ex in exs
    ]
    if candidates:
        return random.choice(candidates)

    return None


def is_loaded() -> bool:
    return _loaded
