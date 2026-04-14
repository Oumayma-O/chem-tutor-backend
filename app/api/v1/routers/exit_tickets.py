"""
Exit tickets — AI generation and class-scoped listing.

POST /teacher/exit-tickets/generate
GET  /teacher/exit-tickets/{class_id}
GET  /teacher/exit-tickets/{class_id}/stream
GET  /teacher/exit-tickets/{class_id}/misconceptions
GET  /teacher/exit-tickets/{class_id}/misconceptions/aggregate
"""

import math
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, get_auth_context_from_query, require_teacher, require_teacher_or_admin
from app.api.v1.classroom_access import ensure_teacher_classroom
from app.core.sse_stream import SSE_STREAM_HEADERS, sse_json_poll_events
from app.infrastructure.database.connection import AsyncSessionFactory, fresh_session, get_db, sse_poll_session
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
from app.infrastructure.database.models import User
from app.infrastructure.database.models.teacher import ExitTicketResponse
from app.infrastructure.database.repositories.exit_ticket_repo import ExitTicketRepository
from app.services.ai.exit_ticket.service import get_exit_ticket_generation_service
from app.services.ai.exit_ticket.persistence import ExitTicketPersistenceService
from app.services.ai.exit_ticket.config_serialization import exit_ticket_row_to_config
from app.services.classroom.access import require_classroom_owned_by_teacher
from app.services.exit_ticket.misconceptions import (
    aggregate_misconception_tag_counts,
    per_question_misconception_hits,
)
from app.services.problem_delivery.generation_orchestrator import LessonContextLoader

router = APIRouter(prefix="/teacher/exit-tickets")


def _effective_score(r: "ExitTicketResponse") -> float | None:
    """Return the best available score for a response row.

    Prefers the stored ``score`` when it is a positive number.  Falls back to
    deriving the score from per-answer ``is_correct`` flags so that rows
    submitted before the scoring fix (which stored 0 instead of the real value)
    still show the correct percentage.
    """
    if r.score is not None and r.score > 0:
        return r.score
    answers = list(r.answers or [])
    gradable = [a for a in answers if isinstance(a, dict) and a.get("is_correct") is not None]
    if not gradable:
        return r.score  # keep None / 0 as-is when no is_correct data exists
    correct = sum(1 for a in gradable if a.get("is_correct") is True)
    return round(100.0 * correct / len(gradable), 4)


async def build_exit_tickets_for_class_out(
    db: AsyncSession,
    class_id: uuid.UUID,
    teacher_id: uuid.UUID | None,
    page: int,
    limit: int,
    unit_id: str | None,
    lesson_id: str | None,
    days: int | None = None,
) -> ExitTicketsForClassOut:
    """Shared by GET list and SSE stream. Pass teacher_id=None for admin (ownership bypass)."""
    if teacher_id is not None:
        await require_classroom_owned_by_teacher(db, class_id, teacher_id)

    since: datetime | None = (
        datetime.now(timezone.utc) - timedelta(days=days) if days is not None else None
    )

    svc = ExitTicketPersistenceService(db)

    all_tickets = await svc.list_all_published_for_class(
        class_id, unit_id=unit_id, lesson_id=lesson_id, since=since
    )
    total_submissions = 0
    scores: list[float] = []
    last_activity: datetime | None = None
    for t in all_tickets:
        for r in t.responses or []:
            total_submissions += 1
            # Derive score from per-answer is_correct flags when stored score is
            # absent or zero (covers rows submitted before the scoring fix).
            effective_score = _effective_score(r)
            if effective_score is not None:
                scores.append(effective_score)
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
                        score=_effective_score(r),
                        submitted_at=r.submitted_at,
                    )
                )
        items.append(ExitTicketBundleOut(ticket=exit_ticket_row_to_config(t), responses=resp_out))

    return ExitTicketsForClassOut(analytics=analytics, items=items, page=page, total_pages=total_pages)


@router.post("/generate", response_model=ExitTicketGenerateResponse)
async def generate_exit_ticket(
    req: ExitTicketGenerateRequest,
    auth: AuthContext = Depends(get_auth_context),
) -> ExitTicketGenerateResponse:
    # Load lesson in a short DB session, then release the connection before the LLM call
    # (generation often takes 30–120s; holding get_db across it ties up a pool connection).
    async with AsyncSessionFactory() as db:
        classroom = await ensure_teacher_classroom(db, auth, req.classroom_id)

        unit_key = req.unit_id or classroom.unit_id
        if unit_key is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Set the classroom unit or pass unit_id so the lesson can be resolved.",
            )

        loader = LessonContextLoader(db)
        lesson, lesson_context = await loader.load_lesson_and_context(unit_key, req.lesson_index)
        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson not found for unit '{unit_key}', index {req.lesson_index}.",
            )
        lesson_title = lesson.title
        resolved_lesson_id = req.lesson_id or lesson.slug

    gen = get_exit_ticket_generation_service()
    raw_questions = await gen.generate_for_teacher(
        topic=None,
        question_count=req.question_count,
        difficulty=req.difficulty,
        question_format=req.question_format,
        lesson_name=lesson_title,
        lesson_context=lesson_context,
        unit_id=unit_key,
    )

    async with fresh_session() as db:
        svc = ExitTicketPersistenceService(db)
        row = await svc.create_ticket(
            class_id=req.classroom_id,
            teacher_id=auth.user_id,
            unit_id=unit_key,
            lesson_index=req.lesson_index,
            lesson_id=resolved_lesson_id,
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
    require_teacher_or_admin(auth)
    await ensure_teacher_classroom(db, auth, class_id)

    repo = ExitTicketRepository(db)
    all_tickets = await repo.list_all_published_for_class(class_id)

    tag_counts, total_wrong = aggregate_misconception_tag_counts(all_tickets)

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
    require_teacher_or_admin(auth)
    await ensure_teacher_classroom(db, auth, class_id)

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

    agg, q_prompt_map = per_question_misconception_hits(list(ticket.questions or []), ticket.responses or [])

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


@router.get("/{class_id}/stream")
async def stream_exit_tickets_for_class(
    class_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    unit_id: str | None = Query(default=None, description="Filter by curriculum unit ID"),
    lesson_id: str | None = Query(default=None, description="Filter by curriculum lesson ID"),
    days: int | None = Query(default=None, ge=1, description="Limit to tickets published within this many days"),
    auth: AuthContext = Depends(get_auth_context_from_query),
) -> StreamingResponse:
    """SSE: push exit ticket list + responses when submissions change (replaces teacher polling)."""
    require_teacher_or_admin(auth)
    teacher_id: uuid.UUID | None = auth.user_id if auth.role == "teacher" else None

    # Lightweight ownership check before opening the stream — avoids a full
    # build_exit_tickets_for_class_out call just for auth.
    async with sse_poll_session() as db:
        if teacher_id is not None:
            try:
                await require_classroom_owned_by_teacher(db, class_id, teacher_id)
            except LookupError as exc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
            except PermissionError as exc:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        else:
            from sqlalchemy import select as _select
            from app.infrastructure.database.models import Classroom as _Classroom
            cls = await db.scalar(_select(_Classroom).where(_Classroom.id == class_id))
            if cls is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")

    async def event_stream():
        async def poll_json() -> str:
            async with sse_poll_session() as sdb:
                out = await build_exit_tickets_for_class_out(
                    sdb, class_id, teacher_id, page, limit, unit_id, lesson_id, days
                )
            return out.model_dump_json()

        async for chunk in sse_json_poll_events(
            poll_json=poll_json,
            log_event="teacher_exit_tickets_sse_error",
        ):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers=dict(SSE_STREAM_HEADERS),
    )


@router.get("/{class_id}", response_model=ExitTicketsForClassOut)
async def list_exit_tickets_for_class(
    class_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    unit_id: str | None = Query(default=None, description="Filter by curriculum unit ID"),
    lesson_id: str | None = Query(default=None, description="Filter by curriculum lesson ID"),
    days: int | None = Query(default=None, ge=1, description="Limit to tickets published within this many days"),
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ExitTicketsForClassOut:
    require_teacher_or_admin(auth)
    teacher_id: uuid.UUID | None = auth.user_id if auth.role == "teacher" else None
    try:
        return await build_exit_tickets_for_class_out(db, class_id, teacher_id, page, limit, unit_id, lesson_id, days)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
