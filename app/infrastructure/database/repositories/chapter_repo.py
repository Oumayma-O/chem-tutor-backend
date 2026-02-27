"""Repository for chapters, topics, standards, and curriculum documents."""

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models import (
    Chapter,
    CurriculumDocument,
    Standard,
    Topic,
    TopicStandard,
)
from app.infrastructure.database.repositories.base import BaseRepository


class ChapterRepository(BaseRepository[Chapter]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Chapter, session)

    async def get_all_active(
        self,
        grade_id: int | None = None,
        course_id: int | None = None,
    ) -> Sequence[Chapter]:
        q = (
            select(Chapter)
            .where(Chapter.is_active == True)
            .options(
                selectinload(Chapter.topics),
                selectinload(Chapter.course),
            )
            .order_by(Chapter.sort_order)
        )
        if grade_id is not None:
            q = q.where(Chapter.grade_id == grade_id)
        if course_id is not None:
            q = q.where(Chapter.course_id == course_id)
        result = await self._session.execute(q)
        return result.scalars().all()

    async def get_by_id(self, chapter_id: str) -> Chapter | None:
        result = await self._session.execute(
            select(Chapter)
            .where(Chapter.id == chapter_id)
            .options(
                selectinload(Chapter.course),
                selectinload(Chapter.topics).selectinload(Topic.standards)
                .selectinload(TopicStandard.standard),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, chapter: Chapter) -> Chapter:
        self._session.add(chapter)
        await self._session.flush()
        return chapter


class TopicRepository(BaseRepository[Topic]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Topic, session)

    async def get_by_chapter(self, chapter_id: str) -> Sequence[Topic]:
        result = await self._session.execute(
            select(Topic)
            .where(Topic.chapter_id == chapter_id, Topic.is_active == True)
            .options(
                selectinload(Topic.standards).selectinload(TopicStandard.standard)
            )
            .order_by(Topic.topic_index)
        )
        return result.scalars().all()

    async def get_by_index(self, chapter_id: str, topic_index: int) -> Topic | None:
        result = await self._session.execute(
            select(Topic)
            .where(
                Topic.chapter_id == chapter_id,
                Topic.topic_index == topic_index,
            )
            .options(
                selectinload(Topic.standards).selectinload(TopicStandard.standard)
            )
        )
        return result.scalar_one_or_none()


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

    async def get_for_topic(
        self,
        chapter_id: str,
        topic_id: int | None = None,
    ) -> Sequence[CurriculumDocument]:
        q = select(CurriculumDocument).where(CurriculumDocument.chapter_id == chapter_id)
        if topic_id is not None:
            q = q.where(CurriculumDocument.topic_id == topic_id)
        result = await self._session.execute(q.order_by(CurriculumDocument.created_at.desc()))
        return result.scalars().all()

    async def build_rag_context(
        self,
        chapter_id: str,
        topic_id: int | None = None,
    ) -> dict:
        """
        Aggregate curriculum documents into the rag_context dict that
        ProblemGenerationService and HintGenerationService accept.
        """
        docs = await self.get_for_topic(chapter_id, topic_id)
        standards: list[str] = []
        equations: list[str] = []
        skills: list[str] = []
        for doc in docs:
            meta = doc.doc_metadata or {}
            standards.extend(meta.get("standards", []))
            equations.extend(meta.get("equations", []))
            skills.extend(meta.get("skills", []))
        return {
            "standards": list(dict.fromkeys(standards)),   # deduplicate
            "equations": list(dict.fromkeys(equations)),
            "skills": list(dict.fromkeys(skills)),
        }
