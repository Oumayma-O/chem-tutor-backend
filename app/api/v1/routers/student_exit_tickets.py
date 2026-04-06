"""
Student exit tickets — fetch published ticket + submit attempt.

GET  /student/exit-tickets/{ticket_id}
POST /student/exit-tickets/{ticket_id}/submit
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_role
from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.dashboards import ExitTicketConfig
from app.services.ai.exit_ticket.config_serialization import exit_ticket_row_to_config
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.models import Classroom, ClassroomStudent, ExitTicket, ExitTicketResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/student/exit-tickets")


class ExitTicketSubmitBody(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


def _score_submission(questions: list, answers: dict[str, str]) -> float | None:
    total = 0.0
    earned = 0.0
    for raw in questions or []:
        if not isinstance(raw, dict):
            continue
        qid = str(raw.get("id", ""))
        pts = float(raw.get("points", 1.0) or 1.0)
        total += pts
        ca = (raw.get("correct_answer") or "").strip().lower()
        sa = (answers.get(qid) or "").strip().lower()
        if ca and sa == ca:
            earned += pts
    if total <= 0:
        return None
    return round(100.0 * earned / total, 4)


async def _assert_student_enrolled(db: AsyncSession, student_id: uuid.UUID, class_id: uuid.UUID) -> None:
    r = await db.execute(
        select(ClassroomStudent.id).where(
            ClassroomStudent.student_id == student_id,
            ClassroomStudent.classroom_id == class_id,
        )
    )
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled in this class.")


async def _assert_ticket_published_for_class(db: AsyncSession, classroom_id: uuid.UUID, ticket_id: uuid.UUID) -> None:
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

    await _assert_student_enrolled(db, auth.user_id, t_row.class_id)
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

    await _assert_student_enrolled(db, auth.user_id, t_row.class_id)
    await _assert_ticket_published_for_class(db, t_row.class_id, ticket_id)

    score = _score_submission(list(t_row.questions or []), body.answers)
    row = ExitTicketResponse(
        exit_ticket_id=ticket_id,
        student_id=auth.user_id,
        answers=[{"question_id": k, "answer": v} for k, v in body.answers.items()],
        score=score,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(row)
    await db.flush()
