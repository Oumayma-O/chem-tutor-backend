"""Small helpers for classroom-scoped tutor settings."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import Classroom


async def get_allow_answer_reveal(db: AsyncSession, class_id: uuid.UUID | None) -> bool | None:
    """Return the class toggle when ``class_id`` is set and the row exists; else ``None``."""
    if class_id is None:
        return None
    row = await db.scalar(select(Classroom).where(Classroom.id == class_id))
    if row is None:
        return None
    return bool(row.allow_answer_reveal)


async def get_max_answer_reveals_per_lesson(db: AsyncSession, class_id: uuid.UUID | None) -> int | None:
    """Return the class cap when ``class_id`` is set and the row exists; else ``None``."""
    if class_id is None:
        return None
    row = await db.scalar(select(Classroom).where(Classroom.id == class_id))
    if row is None:
        return None
    n = int(row.max_answer_reveals_per_lesson)
    return max(1, n)


async def get_min_level1_examples_for_level2(db: AsyncSession, class_id: uuid.UUID | None) -> int | None:
    """Return required unique L1 examples before Level 2 when ``class_id`` is set; else ``None``."""
    if class_id is None:
        return None
    row = await db.scalar(select(Classroom).where(Classroom.id == class_id))
    if row is None:
        return None
    n = int(row.min_level1_examples_for_level2)
    return max(1, n)
