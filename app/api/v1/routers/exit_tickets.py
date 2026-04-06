"""
Exit tickets — AI generation and class-scoped listing.

POST /teacher/exit-tickets/generate
GET  /teacher/exit-tickets/{class_id}
GET  /teacher/exit-tickets/{class_id}/misconceptions
GET  /teacher/exit-tickets/{class_id}/misconceptions/aggregate
"""

import math
import uuid
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_teacher
from app.domain.schemas.dashboards import (
    AggregateMisconceptionAnalytics,
    AggregateMisconceptionItem,
    ExitTicketAnalytics,
    ExitTicketBundleOut,
    ExitTicketConfig,
    ExitTicketGenerateRequest,
    ExitTicketGenerateResponse,
    ExitTicketResponseItem,
    ExitTicketsForClassOut,
    MisconceptionAnalytics,
    MisconceptionHit,
    QuestionMisconceptionSummary,
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
    unit_key = req.unit_id
    svc = ExitTicketPersistenceService(db)
    row = await svc.create_ticket(
        class_id=req.classroom_id,
        teacher_id=auth.user_id,
        unit_id=unit_key,
        lesson_index=req.lesson_index,
        lesson_id=getattr(req, "lesson_id", None),
        difficulty=req.difficulty,
        time_limit_minutes=req.time_limit_minutes,
        questions=raw_questions,
        is_active=True,
    )
    cfg = exit_ticket_row_to_config(row)
    return ExitTicketGenerateResponse(ticket=cfg)


@router.get("/{class_id}/misconceptions/aggregate", response_model=AggregateMisconceptionAnalytics)
async def get_aggregate_misconception_analytics(
    class_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> AggregateMisconceptionAnalytics:
    """Cross-ticket aggregate: rank misconception tags by how often students chose them across ALL published tickets."""
    require_teacher(auth)
    c_repo = ClassroomRepository(db)
    classroom = await c_repo.get_by_id_with_students(class_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    if classroom.teacher_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class.")

    from app.infrastructure.database.repositories.exit_ticket_repo import ExitTicketRepository

    repo = ExitTicketRepository(db)
    all_tickets = await repo.list_all_published_for_class(class_id)

    tag_counts: dict[str, int] = defaultdict(int)
    total_wrong = 0

    for ticket in all_tickets:
        q_tag_map: dict[str, dict[str, str | None]] = {}
        correct_map: dict[str, str | None] = {}
        for q_dict in ticket.questions or []:
            if not isinstance(q_dict, dict):
                continue
            qid = str(q_dict.get("id") or "")
            correct_map[qid] = q_dict.get("correct_answer")
            tags = q_dict.get("option_misconception_tags") or []
            opts = q_dict.get("options") or []
            q_tag_map[qid] = {
                str(opt): (str(tags[j]) if j < len(tags) and tags[j] else None)
                for j, opt in enumerate(opts)
            }

        for response in ticket.responses or []:
            for ans in response.answers or []:
                if not isinstance(ans, dict):
                    continue
                qid = str(ans.get("question_id") or ans.get("id") or "")
                chosen = str(ans.get("answer") or ans.get("value") or "")
                correct = correct_map.get(qid)
                if correct is not None and chosen == str(correct):
                    continue
                tag = q_tag_map.get(qid, {}).get(chosen)
                if tag:
                    tag_counts[tag] += 1
                    total_wrong += 1

    items = sorted(
        [
            AggregateMisconceptionItem(
                tag=t,
                count=c,
                pct=round(100 * c / total_wrong, 1) if total_wrong else 0.0,
            )
            for t, c in tag_counts.items()
        ],
        key=lambda x: x.count,
        reverse=True,
    )

    return AggregateMisconceptionAnalytics(
        class_id=class_id,
        total_wrong=total_wrong,
        items=items,
    )


@router.get("/{class_id}/misconceptions", response_model=MisconceptionAnalytics)
async def get_misconception_analytics(
    class_id: uuid.UUID,
    ticket_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> MisconceptionAnalytics:
    """Aggregate misconception hits from student MCQ responses for one exit-ticket session."""
    require_teacher(auth)
    c_repo = ClassroomRepository(db)
    classroom = await c_repo.get_by_id_with_students(class_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    if classroom.teacher_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your class.")

    from app.infrastructure.database.repositories.exit_ticket_repo import ExitTicketRepository

    repo = ExitTicketRepository(db)

    if ticket_id is not None:
        ticket = await repo.get(ticket_id)
        if ticket is None or ticket.class_id != class_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")
    else:
        all_t = await repo.list_all_published_for_class(class_id)
        if not all_t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No published tickets.")
        ticket = all_t[0]

    q_tag_map: dict[str, dict[str, str | None]] = {}
    q_prompt_map: dict[str, str] = {}
    for q_dict in ticket.questions or []:
        if not isinstance(q_dict, dict):
            continue
        qid = str(q_dict.get("id") or "")
        q_prompt_map[qid] = str(q_dict.get("prompt") or "")
        tags = q_dict.get("option_misconception_tags") or []
        opts = q_dict.get("options") or []
        q_tag_map[qid] = {
            str(opt): (str(tags[j]) if j < len(tags) and tags[j] else None)
            for j, opt in enumerate(opts)
        }

    agg: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for response in ticket.responses or []:
        for ans in response.answers or []:
            if not isinstance(ans, dict):
                continue
            qid = str(ans.get("question_id") or ans.get("id") or "")
            chosen = str(ans.get("answer") or ans.get("value") or "")
            tag = q_tag_map.get(qid, {}).get(chosen)
            if tag:
                agg[qid][tag] += 1

    question_summaries: list[QuestionMisconceptionSummary] = []
    for qid, tag_counts in agg.items():
        if not tag_counts:
            continue
        hits = sorted(
            [MisconceptionHit(tag=t, count=c) for t, c in tag_counts.items()],
            key=lambda h: h.count,
            reverse=True,
        )
        question_summaries.append(
            QuestionMisconceptionSummary(
                question_id=qid,
                prompt=q_prompt_map.get(qid, ""),
                hits=hits,
            )
        )

    return MisconceptionAnalytics(
        class_id=class_id,
        ticket_id=ticket.id,
        questions=question_summaries,
    )


@router.get("/{class_id}", response_model=ExitTicketsForClassOut)
async def list_exit_tickets_for_class(
    class_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    unit_id: str | None = Query(default=None, description="Filter by curriculum unit ID"),
    lesson_id: str | None = Query(default=None, description="Filter by curriculum lesson ID"),
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

    all_tickets = await svc.list_all_published_for_class(class_id, unit_id=unit_id, lesson_id=lesson_id)
    total_submissions = 0
    scores: list[float] = []
    last_activity: datetime | None = None
    for t in all_tickets:
        for r in t.responses or []:
            total_submissions += 1
            if r.score is not None:
                scores.append(r.score)
            if last_activity is None or r.submitted_at > last_activity:
                last_activity = r.submitted_at

    avg = sum(scores) / len(scores) if scores else None
    analytics = ExitTicketAnalytics(
        class_id=class_id,
        total_sessions=len(all_tickets),
        total_submissions=total_submissions,
        average_score=round(avg, 4) if avg is not None else None,
        last_activity_at=last_activity,
    )
    total_pages = max(1, math.ceil(len(all_tickets) / limit))

    offset = (page - 1) * limit
    page_tickets = list(all_tickets)[offset : offset + limit]

    items: list[ExitTicketBundleOut] = []
    for t in page_tickets:
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
        items.append(ExitTicketBundleOut(ticket=exit_ticket_row_to_config(t), responses=resp_out))

    return ExitTicketsForClassOut(analytics=analytics, items=items, page=page, total_pages=total_pages)
