"""
Problems: cache-aware problem generation with playlist tracking.

Generation rules:
  - Level 1: max 3 worked examples per (user, unit, lesson, difficulty) slot.
  - Level 2/3: max 5 problems per slot.
  - Once the cap is reached, navigation via /navigate replaces further generation.
  - When user_id is absent, cap and playlist tracking are skipped (anonymous mode).

Business logic lives in ProblemDeliveryService.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_self
from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.tutor import GenerateProblemRequest, ProblemDeliveryResponse, ProblemOutput
from app.infrastructure.database.connection import get_db
from app.services.ai.problem_generation.service import (
    ProblemGenerationService,
    get_problem_generation_service,
)
from app.services.problem_delivery import ProblemDeliveryService

logger = get_logger(__name__)
router = APIRouter()


def _delivery(
    db: AsyncSession = Depends(get_db),
    gen_service: ProblemGenerationService = Depends(get_problem_generation_service),
) -> ProblemDeliveryService:
    return ProblemDeliveryService(db, gen_service)


@router.get("/worked-example", response_model=ProblemOutput)
@map_unexpected_errors(
    logger=logger,
    event="worked_example_failed",
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="Failed to generate worked example. Please try again.",
)
async def get_worked_example(
    background_tasks: BackgroundTasks,
    unit_id: str = Query(...),
    lesson_index: int = Query(...),
    service: ProblemDeliveryService = Depends(_delivery),
) -> ProblemOutput:
    """
    Level 1 fully worked example for the lesson side panel.
    Cache-first; generates and caches on miss.
    """
    return await service.deliver_worked_example(unit_id, lesson_index, background_tasks)


@router.post("/generate", response_model=ProblemDeliveryResponse)
@map_unexpected_errors(
    logger=logger,
    event="problem_generation_failed",
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="Failed to generate problem. Please try again.",
)
async def generate_problem(
    req: GenerateProblemRequest,
    background_tasks: BackgroundTasks,
    service: ProblemDeliveryService = Depends(_delivery),
    auth: AuthContext = Depends(get_auth_context),
) -> ProblemDeliveryResponse:
    """
    Deliver a problem at the requested level.

    When user_id is provided: enforces per-slot cap, appends to playlist,
    returns navigation metadata.
    When user_id is absent: anonymous / preview mode, no tracking.
    """
    if req.user_id is not None:
        require_self(req.user_id, auth)
    return await service.deliver(req, background_tasks)

