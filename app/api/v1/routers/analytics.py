"""
Analytics router — teacher-facing class analytics.

All aggregation business logic lives in AnalyticsService.
This router only handles auth checks and HTTP plumbing.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_role, require_self
from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.analytics import ClassAnalyticsRequest, ClassAnalyticsResponse
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.classroom_repo import ClassroomRepository
from app.services.ai.thinking_analysis.service import (
    ThinkingAnalysisService,
    get_thinking_analysis_service,
)
from app.services.analytics_service import AnalyticsService

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics")


def _get_analytics_service(
    db: AsyncSession = Depends(get_db),
    thinking_service: ThinkingAnalysisService = Depends(get_thinking_analysis_service),
) -> AnalyticsService:
    return AnalyticsService(db, thinking_service)


@router.post("/classes", response_model=ClassAnalyticsResponse)
@map_unexpected_errors(
    logger=logger,
    event="class_analytics_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to generate class analytics.",
)
async def get_class_analytics(
    req: ClassAnalyticsRequest,
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_get_analytics_service),
    auth: AuthContext = Depends(get_auth_context),
) -> ClassAnalyticsResponse:
    require_role(auth, "teacher")
    classroom = await ClassroomRepository(db).get_by_id_with_students(req.class_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found.")
    require_self(classroom.teacher_id, auth)
    return await service.aggregate_class(req)
