"""Problems: navigate prev/next through a student's problem playlist."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.schemas.tutor import ProblemDeliveryResponse, ProblemOutput
from app.core.config import get_settings
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.playlist_repo import UserLessonPlaylistRepository
from app.services.ai.problem_generation.service import enforce_step_types

router = APIRouter()


class NavigateProblemRequest(BaseModel):
    user_id: uuid.UUID
    unit_id: str
    lesson_index: int
    level: int
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    direction: Literal["prev", "next"]


@router.post("/navigate", response_model=ProblemDeliveryResponse)
async def navigate_problem(
    req: NavigateProblemRequest,
    db: AsyncSession = Depends(get_db),
) -> ProblemDeliveryResponse:
    """
    Move backward (prev) or forward (next) through a student's already-seen problems.

    - prev: move to the previous problem in the playlist.
    - next: move to the next already-seen problem (does NOT generate new ones).
      Call /generate when at the end to add the next new problem.

    Returns 404 if no playlist exists yet.
    Returns 400 if already at the boundary.
    """
    repo = UserLessonPlaylistRepository(db)
    playlist = await repo.get(
        req.user_id, req.unit_id, req.lesson_index, req.level, req.difficulty
    )

    if not playlist or not playlist.problems:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No problems found for this lesson. Call /generate first.",
        )

    total = len(playlist.problems)
    _s = get_settings()
    max_p = {1: _s.l1_max_problems, 2: _s.l2_max_problems, 3: _s.l3_max_problems}.get(req.level, _s.l2_max_problems)
    ci = playlist.current_index

    if req.direction == "prev":
        if ci == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already at the first problem.",
            )
        new_index = ci - 1
    else:  # next
        if ci >= total - 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No more seen problems ahead. Call /generate to get a new one.",
            )
        new_index = ci + 1

    updated = await repo.update_index(playlist, new_index)
    problem = ProblemOutput.model_validate(updated.problems[new_index])
    enforce_step_types(problem, req.level)  # fix stale step types from old cache

    return ProblemDeliveryResponse(
        problem=problem,
        current_index=new_index,
        total=total,
        max_problems=max_p,
        has_prev=new_index > 0,
        has_next=new_index < total - 1,
        at_limit=total >= max_p,
    )
