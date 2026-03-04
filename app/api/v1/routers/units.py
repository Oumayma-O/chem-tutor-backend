"""
Units router — content catalog management.

GET  /units               → list all active units (filtered by grade/course)
GET  /units/{id}          → unit detail with lessons
POST /units               → create unit (teacher/admin)
POST /curriculum/upload   → upload curriculum document for RAG context
GET  /units/{id}/rag-context → get aggregated RAG context for a unit/lesson
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.units import (
    CurriculumDocOut,
    CurriculumUploadRequest,
    LessonCreate,
    LessonOut,
    StandardOut,
    UnitCreate,
    UnitListItem,
    UnitOut,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import CurriculumDocument, Lesson, LessonStandard, Standard, Unit
from app.infrastructure.database.repositories.unit_repo import (
    CurriculumDocumentRepository,
    LessonRepository,
    StandardRepository,
    UnitRepository,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/units")


# ── Unit Endpoints ─────────────────────────────────────────────

@router.get("", response_model=list[UnitListItem])
async def list_units(
    grade_id: int | None = Query(default=None),
    course_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[UnitListItem]:
    repo = UnitRepository(db)
    units = await repo.get_all_active(grade_id=grade_id, course_id=course_id)
    return [
        UnitListItem(
            id=u.id,
            title=u.title,
            description=u.description,
            icon=u.icon,
            gradient=u.gradient,
            grade_id=u.grade_id,
            course_id=u.course_id,
            course_name=u.course.name if u.course else None,
            sort_order=u.sort_order,
            is_active=u.is_active,
            is_coming_soon=u.is_coming_soon,
            lesson_count=len(u.unit_lessons),
            skill_count=sum(len(ul.lesson.objectives or []) for ul in u.unit_lessons),
            lesson_titles=[ul.lesson.title for ul in sorted(u.unit_lessons, key=lambda x: x.lesson_order)],
        )
        for u in units
    ]


@router.get("/{unit_id}", response_model=UnitOut)
async def get_unit(
    unit_id: str,
    db: AsyncSession = Depends(get_db),
) -> UnitOut:
    repo = UnitRepository(db)
    unit = await repo.get_by_id(unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found.")

    lessons_out = []
    for ul in sorted(unit.unit_lessons, key=lambda x: x.lesson_order):
        l = ul.lesson
        stds = [
            StandardOut(
                code=ls.standard.code,
                framework=ls.standard.framework,
                description=ls.standard.description,
            )
            for ls in (l.standards or [])
            if ls.standard
        ]
        lessons_out.append(
            LessonOut(
                id=l.id,
                unit_id=l.unit_id,
                title=l.title,
                description=l.description,
                lesson_index=ul.lesson_order,
                slug=l.slug,
                is_ap_only=l.is_ap_only,
                objectives=l.objectives or [],
                key_equations=l.key_equations or [],
                standards=stds,
                is_active=l.is_active,
            )
        )

    return UnitOut(
        id=unit.id,
        title=unit.title,
        description=unit.description,
        icon=unit.icon,
        gradient=unit.gradient,
        grade_id=unit.grade_id,
        course_id=unit.course_id,
        course_name=unit.course.name if unit.course else None,
        sort_order=unit.sort_order,
        is_active=unit.is_active,
        is_coming_soon=unit.is_coming_soon,
        lessons=lessons_out,
    )


@router.post("", response_model=UnitOut, status_code=status.HTTP_201_CREATED)
async def create_unit(
    req: UnitCreate,
    db: AsyncSession = Depends(get_db),
) -> UnitOut:
    unit_repo = UnitRepository(db)
    lesson_repo = LessonRepository(db)
    std_repo = StandardRepository(db)

    unit = Unit(
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
    await unit_repo.create(unit)

    for l in req.lessons:
        lesson = Lesson(
            unit_id=req.id,
            title=l.title,
            description=l.description,
            lesson_index=l.lesson_index,
            objectives=l.objectives,
            key_equations=l.key_equations,
            is_active=l.is_active,
        )
        db.add(lesson)
        await db.flush()

        for code in l.standard_codes:
            framework = code.split(" ")[0] if " " in code else "OTHER"
            std = await std_repo.get_or_create(code=code, framework=framework)
            db.add(LessonStandard(topic_id=lesson.id, standard_id=std.id))

    return await get_unit(req.id, db)


@router.get("/{unit_id}/rag-context")
async def get_rag_context(
    unit_id: str,
    lesson_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Aggregate curriculum documents into the rag_context dict for AI services.
    Also includes key_equations and objectives from lessons.
    """
    doc_repo = CurriculumDocumentRepository(db)
    lesson_repo = LessonRepository(db)

    rag = await doc_repo.build_rag_context(unit_id=unit_id, lesson_id=lesson_id)

    # Augment with lesson key_equations and objectives
    if lesson_id is not None:
        lesson = await lesson_repo.get_by_index(unit_id, lesson_id)
        if lesson:
            if lesson.key_equations:
                existing = set(rag.get("equations", []))
                for eq in lesson.key_equations:
                    if eq not in existing:
                        rag.setdefault("equations", []).append(eq)
            if lesson.objectives:
                existing = set(rag.get("objectives", []))
                for obj in lesson.objectives:
                    if obj not in existing:
                        rag.setdefault("objectives", []).append(obj)
    else:
        lessons = await lesson_repo.get_by_unit(unit_id)
        eq_existing = set(rag.get("equations", []))
        obj_existing = set(rag.get("objectives", []))
        for l in lessons:
            for eq in (l.key_equations or []):
                if eq not in eq_existing:
                    rag.setdefault("equations", []).append(eq)
                    eq_existing.add(eq)
            for obj in (l.objectives or []):
                if obj not in obj_existing:
                    rag.setdefault("objectives", []).append(obj)
                    obj_existing.add(obj)

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
        unit_id=req.unit_id,
        lesson_id=req.lesson_id,
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
        unit_id=doc.unit_id,
        lesson_id=doc.lesson_id,
        title=doc.title,
        source_type=doc.source_type,
        filename=doc.filename,
        standards=req.standards,
        equations=req.equations,
    )


@curriculum_router.get("/units/{unit_id}", response_model=list[CurriculumDocOut])
async def list_curriculum_docs(
    unit_id: str,
    lesson_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[CurriculumDocOut]:
    repo = CurriculumDocumentRepository(db)
    docs = await repo.get_for_lesson(unit_id=unit_id, lesson_id=lesson_id)
    return [
        CurriculumDocOut(
            id=str(d.id),
            unit_id=d.unit_id,
            lesson_id=d.lesson_id,
            title=d.title,
            source_type=d.source_type,
            filename=d.filename,
            standards=d.doc_metadata.get("standards", []) if d.doc_metadata else [],
            equations=d.doc_metadata.get("equations", []) if d.doc_metadata else [],
        )
        for d in docs
    ]
