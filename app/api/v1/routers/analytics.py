"""
Analytics router — teacher-facing class analytics.

All aggregation business logic lives in AnalyticsService.
This router only handles auth checks and HTTP plumbing.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context
from app.api.v1.classroom_access import ensure_teacher_classroom
from app.api.v1.router_utils import map_unexpected_errors
from app.core.logging import get_logger
from app.domain.schemas.analytics import (
    ClassAnalyticsRequest,
    ClassAnalyticsResponse,
    ClassStandardsMasteryResponse,
    StudentStandardsMasteryResponse,
)
from app.infrastructure.database.connection import get_db
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
    await ensure_teacher_classroom(db, auth, req.class_id)
    return await service.aggregate_class(req)


@router.get("/classes/{class_id}/standards", response_model=ClassStandardsMasteryResponse)
@map_unexpected_errors(
    logger=logger,
    event="class_standards_analytics_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to generate class standards analytics.",
)
async def get_class_standards_analytics(
    class_id: uuid.UUID,
    unit_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_get_analytics_service),
    auth: AuthContext = Depends(get_auth_context),
) -> ClassStandardsMasteryResponse:
    await ensure_teacher_classroom(db, auth, class_id)
    return await service.aggregate_class_standards(class_id=class_id, unit_id=unit_id)


@router.get("/students/{student_id}/standards", response_model=StudentStandardsMasteryResponse)
@map_unexpected_errors(
    logger=logger,
    event="student_standards_analytics_failed",
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Failed to generate student standards analytics.",
)
async def get_student_standards_analytics(
    student_id: uuid.UUID,
    class_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(_get_analytics_service),
    auth: AuthContext = Depends(get_auth_context),
) -> StudentStandardsMasteryResponse:
    # Teacher viewing a student → verify classroom ownership
    if class_id is not None:
        await ensure_teacher_classroom(db, auth, class_id)
    # Student viewing their own data → verified by matching auth user
    elif auth.user_id != student_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Not authorised to view this student's data.")
    return await service.aggregate_student_standards(student_id=student_id)
