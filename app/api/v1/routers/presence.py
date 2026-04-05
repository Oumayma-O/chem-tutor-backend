"""
Student presence heartbeat for live panels (poll-based).

POST /presence/heartbeat
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.authz import AuthContext, get_auth_context, require_role
from app.domain.schemas.dashboards import HeartbeatRequest
from app.infrastructure.database.connection import get_db
from app.services.presence.service import PresenceService

router = APIRouter(prefix="/presence")


@router.post("/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
async def post_heartbeat(
    body: HeartbeatRequest,
    db: AsyncSession = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
) -> None:
    require_role(auth, "student")
    try:
        await PresenceService(db).record_heartbeat(auth.user_id, body.classroom_id, body.step_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
