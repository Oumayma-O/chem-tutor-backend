"""
Student exit tickets — fetch published ticket + submit attempt.

GET  /student/exit-tickets/{ticket_id}
POST  /student/exit-tickets/{ticket_id}/submit
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_role
from app.api.v1.classroom_access import ensure_student_enrolled
from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.dashboards import ExitTicketConfig
from app.domain.schemas.student_exit_ticket import ExitTicketSubmitBody
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import Classroom, ExitTicket, ExitTicketResponse
from app.services.ai.exit_ticket.config_serialization import exit_ticket_row_to_config
from app.services.exit_ticket.mastery_bridge import apply_exit_ticket_to_mastery
from app.services.exit_ticket.scoring import score_exit_ticket_submission

logger = get_logger(__name__)
router = APIRouter(prefix="/student/exit-tickets")


async def _assert_ticket_published_for_class(db: AsyncSession, classroom_id: uuid.UUID, ticket_id: uuid.UUID) -> None:
    """Used by GET only — requires the ticket to be currently active in the live session."""
    c_row = await db.scalar(select(Classroom).where(Classroom.id == classroom_id))
    if c_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    raw = c_row.live_session if isinstance(c_row.live_session, dict) else {}
    active = raw.get("active_exit_ticket_id")
    if active is None or str(active) != str(ticket_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exit ticket is not published for this class.",
        )


@router.get("/{ticket_id}", response_model=ExitTicketConfig)
@map_unexpected_errors(
    logger=logger,
    event="get_exit_ticket_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to load exit ticket.",
)
async def get_exit_ticket_for_student(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> ExitTicketConfig:
    require_role(auth, "student")
    t_row = await db.scalar(select(ExitTicket).where(ExitTicket.id == ticket_id))
    if t_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exit ticket not found.")

    await ensure_student_enrolled(db, auth.user_id, t_row.class_id)
    await _assert_ticket_published_for_class(db, t_row.class_id, ticket_id)
    return exit_ticket_row_to_config(t_row)


@router.post("/{ticket_id}/submit", status_code=status.HTTP_204_NO_CONTENT)
@map_unexpected_errors(
    logger=logger,
    event="submit_exit_ticket_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to submit exit ticket.",
)
async def submit_exit_ticket_attempt(
    ticket_id: uuid.UUID,
    body: ExitTicketSubmitBody,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    require_role(auth, "student")
    t_row = await db.scalar(select(ExitTicket).where(ExitTicket.id == ticket_id))
    if t_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exit ticket not found.")

    await ensure_student_enrolled(db, auth.user_id, t_row.class_id)

    # Allow submission if the ticket was ever published (published_at set), regardless of whether
    # the live session is still active.  Using _assert_ticket_published_for_class here would
    # reject submissions from students who answered just after the teacher stopped the session,
    # silently dropping their work.
    if t_row.published_at is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This exit ticket has not been published yet.",
        )

    # Idempotency: if this student already submitted, return 204 without creating a duplicate row.
    existing = await db.scalar(
        select(ExitTicketResponse.id).where(
            ExitTicketResponse.exit_ticket_id == ticket_id,
            ExitTicketResponse.student_id == auth.user_id,
        )
    )
    if existing is not None:
        logger.info("exit_ticket_already_submitted", ticket=str(ticket_id), student=str(auth.user_id))
        return

    score, per_question = await score_exit_ticket_submission(list(t_row.questions or []), body.answers)

    answers_list = [
        {
            "question_id": k,
            "answer": v,
            **({"is_correct": per_question[k]} if k in per_question else {}),
        }
        for k, v in body.answers.items()
    ]
    row = ExitTicketResponse(
        exit_ticket_id=ticket_id,
        student_id=auth.user_id,
        answers=answers_list,
        score=score,
        submitted_at=datetime.now(timezone.utc),
        time_spent_s=max(0, body.time_spent_s),
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError:
        # Concurrent duplicate submit — unique (exit_ticket_id, student_id); treat as idempotent 204.
        await db.rollback()
        logger.info(
            "exit_ticket_submit_integrity_duplicate",
            ticket=str(ticket_id),
            student=str(auth.user_id),
        )
        return
    # Persist before response: dependency commit runs after the response is sent, so without
    # this the teacher can poll/SSE before the row is visible.
    await db.commit()
    logger.info("exit_ticket_submitted", ticket=str(ticket_id), student=str(auth.user_id), score=score)

    # Feed the exit ticket score into the mastery model (fills the top band: 85%→100%).
    if score is not None:
        try:
            await apply_exit_ticket_to_mastery(
                db,
                user_id=auth.user_id,
                unit_id=t_row.unit_id,
                lesson_index=t_row.lesson_index,
                exit_ticket_score_percent=score,
            )
            await db.commit()
        except Exception:
            logger.warning(
                "exit_ticket_mastery_bridge_failed",
                ticket=str(ticket_id),
                student=str(auth.user_id),
                exc_info=True,
            )
