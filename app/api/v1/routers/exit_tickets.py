"""
Exit tickets — AI generation and class-scoped listing.

POST /teacher/exit-tickets/generate
GET  /teacher/exit-tickets/{class_id}
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_teacher
from app.domain.schemas.dashboards import (
    ExitTicketAnalytics,
    ExitTicketBundleOut,
    ExitTicketConfig,
    ExitTicketGenerateRequest,
    ExitTicketGenerateResponse,
    ExitTicketResponseItem,
    ExitTicketsForClassOut,
)
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import ExitTicket, User
from app.infrastructure.database.repositories.classroom_repo import ClassroomRepository
from app.services.ai.exit_ticket.service import get_exit_ticket_generation_service
from app.services.ai.exit_ticket.persistence import ExitTicketPersistenceService
from app.services.ai.exit_ticket.config_serialization import exit_ticket_row_to_config

router = APIRouter(prefix="/teacher/exit-tickets")


@router.post("/generate", response_model=ExitTicketGenerateResponse)
async def generate_exit_ticket(
    req: ExitTicketGenerateRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ExitTicketGenerateResponse:
    require_teacher(auth)
    c_repo = ClassroomRepository(db)
    classroom = await c_repo.get_by_id_with_students(req.classroom_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    if classroom.teacher_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class.")

    gen = get_exit_ticket_generation_service()
    raw_questions = await gen.generate_for_teacher(req.topic, question_count=req.question_count)
    unit_key = req.unit_id or classroom.unit_id or "general"
    svc = ExitTicketPersistenceService(db)
    row = await svc.create_ticket(
        class_id=req.classroom_id,
        teacher_id=auth.user_id,
        unit_id=unit_key,
        lesson_index=req.lesson_index,
        difficulty=req.difficulty,
        time_limit_minutes=req.time_limit_minutes,
        questions=raw_questions,
        is_active=True,
    )
    cfg = exit_ticket_row_to_config(row)
    return ExitTicketGenerateResponse(ticket=cfg)


@router.get("/{class_id}", response_model=ExitTicketsForClassOut)
async def list_exit_tickets_for_class(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ExitTicketsForClassOut:
    require_teacher(auth)
    c_repo = ClassroomRepository(db)
    classroom = await c_repo.get_by_id_with_students(class_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    if classroom.teacher_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class.")

    svc = ExitTicketPersistenceService(db)
    tickets = await svc.list_for_class(class_id)
    items: list[ExitTicketBundleOut] = []
    total_submissions = 0
    scores: list[float] = []
    last_activity: datetime | None = None

    for t in tickets:
        resp_out: list[ExitTicketResponseItem] = []
        if t.responses:
            user_ids = list({r.student_id for r in t.responses})
            res_u = await db.execute(select(User).where(User.id.in_(user_ids)))
            users = {u.id: u for u in res_u.scalars().all()}
            for r in t.responses:
                u = users.get(r.student_id)
                resp_out.append(
                    ExitTicketResponseItem(
                        id=r.id,
                        student_id=r.student_id,
                        student_name=u.name if u else None,
                        student_email=u.email if u else None,
                        answers=list(r.answers or []),
                        score=r.score,
                        submitted_at=r.submitted_at,
                    )
                )
                total_submissions += 1
                if r.score is not None:
                    scores.append(r.score)
                if last_activity is None or r.submitted_at > last_activity:
                    last_activity = r.submitted_at

        items.append(ExitTicketBundleOut(ticket=exit_ticket_row_to_config(t), responses=resp_out))

    avg = sum(scores) / len(scores) if scores else None
    analytics = ExitTicketAnalytics(
        class_id=class_id,
        total_sessions=len(tickets),
        total_submissions=total_submissions,
        average_score=round(avg, 4) if avg is not None else None,
        last_activity_at=last_activity,
    )
    return ExitTicketsForClassOut(analytics=analytics, items=items)
