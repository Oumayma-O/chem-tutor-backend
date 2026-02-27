"""
Classrooms router — classroom management and student enrollment.

POST /classrooms                    → teacher creates classroom
GET  /classrooms/{id}               → get classroom detail (teacher)
GET  /classrooms/teacher/{id}       → list teacher's classrooms
POST /classrooms/join               → student joins by code
GET  /classrooms/student/{id}       → list student's classrooms
GET  /classrooms/{id}/students      → list enrolled students
DELETE /classrooms/{id}/students/{sid} → remove student
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.domain.schemas.classrooms import (
    ClassroomCreate,
    ClassroomListItem,
    ClassroomOut,
    ClassroomStudentOut,
    JoinClassroomRequest,
    JoinClassroomResponse,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import Classroom
from app.infrastructure.database.repositories.classroom_repo import (
    ClassroomRepository,
    ClassroomStudentRepository,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/classrooms")


# ── Teacher: create / manage classrooms ───────────────────────

@router.post("", response_model=ClassroomOut, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    req: ClassroomCreate,
    db: AsyncSession = Depends(get_db),
) -> ClassroomOut:
    repo = ClassroomRepository(db)
    classroom = Classroom(
        name=req.name,
        teacher_id=req.teacher_id,
        chapter_id=req.chapter_id,
        code="",  # will be set by create_with_code
    )
    created = await repo.create_with_code(classroom)
    return ClassroomOut(
        id=created.id,
        name=created.name,
        teacher_id=created.teacher_id,
        chapter_id=created.chapter_id,
        code=created.code,
        is_active=created.is_active,
        student_count=0,
        created_at=created.created_at,
    )


@router.get("/teacher/{teacher_id}", response_model=list[ClassroomListItem])
async def list_teacher_classrooms(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ClassroomListItem]:
    repo = ClassroomRepository(db)
    classrooms = await repo.get_by_teacher(teacher_id)
    return [
        ClassroomListItem(
            id=c.id,
            name=c.name,
            code=c.code,
            chapter_id=c.chapter_id,
            student_count=len(c.students),
            is_active=c.is_active,
        )
        for c in classrooms
    ]


@router.get("/{classroom_id}", response_model=ClassroomOut)
async def get_classroom(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ClassroomOut:
    repo = ClassroomRepository(db)
    classroom = await repo.get_by_id_with_students(classroom_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    return ClassroomOut(
        id=classroom.id,
        name=classroom.name,
        teacher_id=classroom.teacher_id,
        chapter_id=classroom.chapter_id,
        code=classroom.code,
        is_active=classroom.is_active,
        student_count=len(classroom.students),
        created_at=classroom.created_at,
    )


# ── Student: join / list classrooms ───────────────────────────

@router.post("/join", response_model=JoinClassroomResponse)
async def join_classroom(
    req: JoinClassroomRequest,
    db: AsyncSession = Depends(get_db),
) -> JoinClassroomResponse:
    classroom_repo = ClassroomRepository(db)
    student_repo = ClassroomStudentRepository(db)

    classroom = await classroom_repo.get_by_code(req.code)
    if classroom is None or not classroom.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active classroom found with that code.",
        )

    await student_repo.enroll(classroom.id, req.student_id)
    logger.info("student_joined_classroom", student=str(req.student_id), classroom=str(classroom.id))

    return JoinClassroomResponse(
        classroom_id=classroom.id,
        classroom_name=classroom.name,
        chapter_id=classroom.chapter_id,
    )


@router.get("/student/{student_id}", response_model=list[ClassroomListItem])
async def list_student_classrooms(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ClassroomListItem]:
    repo = ClassroomRepository(db)
    classrooms = await repo.get_student_classrooms(student_id)
    return [
        ClassroomListItem(
            id=c.id,
            name=c.name,
            code=c.code,
            chapter_id=c.chapter_id,
            student_count=0,  # lightweight response
            is_active=c.is_active,
        )
        for c in classrooms
    ]


@router.get("/{classroom_id}/students", response_model=list[ClassroomStudentOut])
async def list_classroom_students(
    classroom_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ClassroomStudentOut]:
    repo = ClassroomStudentRepository(db)
    members = await repo.get_class_students(classroom_id)
    return [
        ClassroomStudentOut(student_id=m.student_id, joined_at=m.joined_at)
        for m in members
    ]
