"""Repository for units, lessons, standards, and curriculum documents."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    CurriculumDocument,
    Lesson,
    LessonStandard,
    Standard,
    Unit,
    UnitLesson,
)
from app.infrastructure.database.repositories.base import BaseRepository


class UnitRepository(BaseRepository[Unit]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Unit, session)

    async def get_all_active(
        self,
        grade_id: int | None = None,
        course_id: int | None = None,
    ) -> Sequence[Unit]:
        q = (
            select(Unit)
            .where(Unit.is_active == True)
            .options(
                selectinload(Unit.unit_lessons).selectinload(UnitLesson.lesson),
                selectinload(Unit.course),
            )
            .order_by(Unit.sort_order)
        )
        if grade_id is not None:
            q = q.where(Unit.grade_id == grade_id)
        if course_id is not None:
            q = q.where(Unit.course_id == course_id)
        result = await self._session.execute(q)
        return result.scalars().all()

    async def get_by_id(self, unit_id: str) -> Unit | None:
        result = await self._session.execute(
            select(Unit)
            .where(Unit.id == unit_id)
            .options(
                selectinload(Unit.course),
                selectinload(Unit.unit_lessons)
                .selectinload(UnitLesson.lesson)
                .selectinload(Lesson.standards)
                .selectinload(LessonStandard.standard),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, unit: Unit) -> Unit:
        self._session.add(unit)
        await self._session.flush()
        return unit




class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Lesson, session)

    async def get_by_unit(self, unit_id: str) -> Sequence[Lesson]:
        """Return lessons for a unit ordered by their position in unit_lessons."""
        result = await self._session.execute(
            select(Lesson)
            .join(UnitLesson, UnitLesson.lesson_id == Lesson.id)
            .where(UnitLesson.unit_id == unit_id, Lesson.is_active == True)
            .options(selectinload(Lesson.standards).selectinload(LessonStandard.standard))
            .order_by(UnitLesson.lesson_order)
        )
        return result.scalars().all()

    async def get_by_index(self, unit_id: str, lesson_index: int) -> Lesson | None:
        """
        Resolve lesson by (unit_id, lesson_order) via the unit_lessons junction.
        Falls back to canonical (unit_id, lesson_index) for backward compatibility.
        """
        # Primary: look up by lesson_order in unit_lessons
        result = await self._session.execute(
            select(Lesson)
            .join(UnitLesson, UnitLesson.lesson_id == Lesson.id)
            .where(
                UnitLesson.unit_id == unit_id,
                UnitLesson.lesson_order == lesson_index,
            )
            .options(selectinload(Lesson.standards).selectinload(LessonStandard.standard))
        )
        lesson = result.scalar_one_or_none()
        if lesson is not None:
            return lesson
        # Fallback: canonical unit_id + lesson_index (mastery tracking key)
        result = await self._session.execute(
            select(Lesson)
            .where(Lesson.unit_id == unit_id, Lesson.lesson_index == lesson_index)
            .options(selectinload(Lesson.standards).selectinload(LessonStandard.standard))
        )
        return result.scalar_one_or_none()

    async def save_reference_card(
        self,
        unit_id: str,
        lesson_index: int,
        card_data: dict,
    ) -> Lesson | None:
        """Persist a generated reference card onto the lesson row."""
        lesson = await self.get_by_index(unit_id, lesson_index)
        if lesson is None:
            return None
        lesson.reference_card_json = card_data
        await self._session.flush()
        return lesson




class StandardRepository(BaseRepository[Standard]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Standard, session)

    async def get_by_code(self, code: str) -> Standard | None:
        result = await self._session.execute(
            select(Standard).where(Standard.code == code)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, code: str, framework: str, description: str | None = None) -> Standard:
        existing = await self.get_by_code(code)
        if existing:
            return existing
        new = Standard(code=code, framework=framework, description=description)
        self._session.add(new)
        await self._session.flush()
        return new


class CurriculumDocumentRepository(BaseRepository[CurriculumDocument]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CurriculumDocument, session)

    async def get_for_lesson(
        self,
        unit_id: str,
        lesson_id: int | None = None,
    ) -> Sequence[CurriculumDocument]:
        q = select(CurriculumDocument).where(CurriculumDocument.unit_id == unit_id)
        if lesson_id is not None:
            q = q.where(CurriculumDocument.lesson_id == lesson_id)
        result = await self._session.execute(q.order_by(CurriculumDocument.created_at.desc()))
        return result.scalars().all()
