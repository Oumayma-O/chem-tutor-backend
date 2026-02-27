"""
Chapters router — content catalog management.

GET  /chapters               → list all active chapters (filtered by grade/course)
GET  /chapters/{id}          → chapter detail with topics
POST /chapters               → create chapter (teacher/admin)
POST /chapters/{id}/topics   → add topic to chapter
POST /curriculum/upload      → upload curriculum document for RAG context
GET  /chapters/{id}/rag-context → get aggregated RAG context for a chapter/topic
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.chapters import (
    ChapterCreate,
    ChapterListItem,
    ChapterOut,
    CurriculumDocOut,
    CurriculumUploadRequest,
    StandardOut,
    TopicCreate,
    TopicOut,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import Chapter, CurriculumDocument, Standard, Topic, TopicStandard
from app.infrastructure.database.repositories.chapter_repo import (
    ChapterRepository,
    CurriculumDocumentRepository,
    StandardRepository,
    TopicRepository,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/chapters")


# ── Chapter Endpoints ─────────────────────────────────────────

@router.get("", response_model=list[ChapterListItem])
async def list_chapters(
    grade_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[ChapterListItem]:
    repo = ChapterRepository(db)
    chapters = await repo.get_all_active(grade_id=grade_id, course_id=course_id)
    return [
        ChapterListItem(
            id=c.id,
            title=c.title,
            description=c.description,
            icon=c.icon,
            gradient=c.gradient,
            grade_id=c.grade_id,
            course_id=c.course_id,
            course_name=c.course.name if c.course else None,
            sort_order=c.sort_order,
            is_active=c.is_active,
            is_coming_soon=c.is_coming_soon,
            topic_count=len(c.topics),
            topic_titles=[t.title for t in c.topics],
        )
        for c in chapters
    ]


@router.get("/{chapter_id}", response_model=ChapterOut)
async def get_chapter(
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
) -> ChapterOut:
    repo = ChapterRepository(db)
    chapter = await repo.get_by_id(chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found.")

    topics_out = []
    for t in chapter.topics:
        stds = [
            StandardOut(
                code=ts.standard.code,
                framework=ts.standard.framework,
                description=ts.standard.description,
            )
            for ts in (t.standards or [])
            if ts.standard
        ]
        topics_out.append(
            TopicOut(
                id=t.id,
                chapter_id=t.chapter_id,
                title=t.title,
                description=t.description,
                topic_index=t.topic_index,
                key_equations=t.key_equations or [],
                standards=stds,
                is_active=t.is_active,
            )
        )

    return ChapterOut(
        id=chapter.id,
        title=chapter.title,
        description=chapter.description,
        icon=chapter.icon,
        gradient=chapter.gradient,
        grade_id=chapter.grade_id,
        course_id=chapter.course_id,
        course_name=chapter.course.name if chapter.course else None,
        sort_order=chapter.sort_order,
        is_active=chapter.is_active,
        is_coming_soon=chapter.is_coming_soon,
        topics=topics_out,
    )


@router.post("", response_model=ChapterOut, status_code=status.HTTP_201_CREATED)
async def create_chapter(
    req: ChapterCreate,
    db: AsyncSession = Depends(get_db),
) -> ChapterOut:
    chapter_repo = ChapterRepository(db)
    topic_repo = TopicRepository(db)
    std_repo = StandardRepository(db)

    chapter = Chapter(
        id=req.id,
        title=req.title,
        description=req.description,
        icon=req.icon,
        gradient=req.gradient,
        grade_id=req.grade_id,
        course_id=req.course_id,
        sort_order=req.sort_order,
        is_coming_soon=req.is_coming_soon,
    )
    await chapter_repo.create(chapter)

    for t in req.topics:
        topic = Topic(
            chapter_id=req.id,
            title=t.title,
            description=t.description,
            topic_index=t.topic_index,
            key_equations=t.key_equations,
            is_active=t.is_active,
        )
        db.add(topic)
        await db.flush()

        for code in t.standard_codes:
            framework = code.split(" ")[0] if " " in code else "OTHER"
            std = await std_repo.get_or_create(code=code, framework=framework)
            db.add(TopicStandard(topic_id=topic.id, standard_id=std.id))

    return await get_chapter(req.id, db)


@router.get("/{chapter_id}/rag-context")
async def get_rag_context(
    chapter_id: str,
    topic_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Aggregate curriculum documents into the rag_context dict for AI services.
    Also includes key_equations from topics.
    """
    doc_repo = CurriculumDocumentRepository(db)
    topic_repo = TopicRepository(db)

    rag = await doc_repo.build_rag_context(chapter_id=chapter_id, topic_id=topic_id)

    # Augment with topic key_equations
    if topic_id is not None:
        topic = await topic_repo.get_by_index(chapter_id, topic_id)
        if topic and topic.key_equations:
            existing = set(rag.get("equations", []))
            for eq in topic.key_equations:
                if eq not in existing:
                    rag.setdefault("equations", []).append(eq)
    else:
        topics = await topic_repo.get_by_chapter(chapter_id)
        existing = set(rag.get("equations", []))
        for t in topics:
            for eq in (t.key_equations or []):
                if eq not in existing:
                    rag.setdefault("equations", []).append(eq)
                    existing.add(eq)

    return rag


# ── Curriculum Document Endpoints ────────────────────────────

curriculum_router = APIRouter(prefix="/curriculum")


@curriculum_router.post("/upload", response_model=CurriculumDocOut, status_code=status.HTTP_201_CREATED)
async def upload_curriculum(
    req: CurriculumUploadRequest,
    uploaded_by: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> CurriculumDocOut:
    """
    Upload a curriculum document (text extracted by the caller from PDF/JSON/text).
    The extracted text is stored for RAG context injection into AI prompts.
    """
    doc = CurriculumDocument(
        chapter_id=req.chapter_id,
        topic_id=req.topic_id,
        title=req.title,
        source_type=req.source_type,
        filename=req.filename,
        content_text=req.content_text,
        doc_metadata={
            "standards": req.standards,
            "equations": req.equations,
            "skills": req.skills,
        },
        uploaded_by=uploaded_by,
    )
    db.add(doc)
    await db.flush()

    return CurriculumDocOut(
        id=str(doc.id),
        chapter_id=doc.chapter_id,
        topic_id=doc.topic_id,
        title=doc.title,
        source_type=doc.source_type,
        filename=doc.filename,
        standards=req.standards,
        equations=req.equations,
    )


@curriculum_router.get("/chapters/{chapter_id}", response_model=list[CurriculumDocOut])
async def list_curriculum_docs(
    chapter_id: str,
    topic_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[CurriculumDocOut]:
    repo = CurriculumDocumentRepository(db)
    docs = await repo.get_for_topic(chapter_id=chapter_id, topic_id=topic_id)
    return [
        CurriculumDocOut(
            id=str(d.id),
            chapter_id=d.chapter_id,
            topic_id=d.topic_id,
            title=d.title,
            source_type=d.source_type,
            filename=d.filename,
            standards=d.doc_metadata.get("standards", []) if d.doc_metadata else [],
            equations=d.doc_metadata.get("equations", []) if d.doc_metadata else [],
        )
        for d in docs
    ]
