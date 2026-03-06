"""
Seed few_shot_examples table from the hardcoded FEW_SHOT_EXAMPLES dict in prompts.py.

Idempotent: skips rows where (unit_id, lesson_index, difficulty, level) already exists.

Usage:
  python -m scripts.seed_few_shots
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.infrastructure.database.connection import AsyncSessionFactory, Base, engine
from app.infrastructure.database.models import FewShotExample
from app.services.ai.problem_generation.prompts import (
    FEW_SHOT_EXAMPLES,
    DEFAULT_FEW_SHOT_EXAMPLES,
    UNIT_STRATEGIES,
)


def _get_strategy(unit_id: str) -> str | None:
    for strategy, ids in UNIT_STRATEGIES.items():
        if unit_id in ids:
            return strategy
    return None


def _normalize_steps(steps: list[dict]) -> list[dict]:
    """Normalize step dicts to use 'instruction' key (schema field name)."""
    normalized = []
    for i, s in enumerate(steps):
        step = {
            "stepNumber": i + 1,
            "label": s.get("label", f"Step {i + 1}"),
            "type": s.get("type", "given"),
            "instruction": s.get("content") or s.get("instruction", ""),
        }
        normalized.append(step)
    return normalized


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    inserted = 0
    skipped = 0

    async with AsyncSessionFactory() as session:
        # Seed per-unit examples
        for (unit_id, lesson_index), difficulty_map in FEW_SHOT_EXAMPLES.items():
            strategy = _get_strategy(unit_id)
            for difficulty, ex in difficulty_map.items():
                existing = await session.execute(
                    select(FewShotExample).where(
                        FewShotExample.unit_id == unit_id,
                        FewShotExample.lesson_index == lesson_index,
                        FewShotExample.difficulty == difficulty,
                        FewShotExample.level == 1,
                    )
                )
                if existing.scalar_one_or_none():
                    skipped += 1
                    continue

                example_json = {
                    "title": ex["title"],
                    "statement": ex["statement"],
                    "topic": ex.get("topic", ""),
                    "steps": _normalize_steps(ex["steps"]),
                }
                session.add(FewShotExample(
                    unit_id=unit_id,
                    lesson_index=lesson_index,
                    difficulty=difficulty,
                    level=1,
                    strategy=strategy,
                    example_json=example_json,
                    is_active=True,
                    promoted=False,
                ))
                inserted += 1

        # Seed default (global fallback) examples under unit_id="__default__", lesson_index=-1
        for difficulty, ex in DEFAULT_FEW_SHOT_EXAMPLES.items():
            existing = await session.execute(
                select(FewShotExample).where(
                    FewShotExample.unit_id == "__default__",
                    FewShotExample.lesson_index == -1,
                    FewShotExample.difficulty == difficulty,
                    FewShotExample.level == 1,
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            example_json = {
                "title": ex["title"],
                "statement": ex["statement"],
                "topic": ex.get("topic", ""),
                "steps": _normalize_steps(ex["steps"]),
            }
            session.add(FewShotExample(
                unit_id="__default__",
                lesson_index=-1,
                difficulty=difficulty,
                level=1,
                strategy="quantitative",
                example_json=example_json,
                is_active=True,
                promoted=False,
            ))
            inserted += 1

        await session.commit()

    print(f"few_shot_examples seeded: {inserted} inserted, {skipped} skipped")


if __name__ == "__main__":
    asyncio.run(seed())
