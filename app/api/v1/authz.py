"""Shared API authorization dependencies and guards."""

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.services.auth.security import decode_token

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    user_id: uuid.UUID
    role: str
    email: str | None = None


def _parse_subject(sub: str | None) -> uuid.UUID:
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
        )
    try:
        return uuid.UUID(sub)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
        ) from exc


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthContext:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc
    return AuthContext(
        user_id=_parse_subject(payload.get("sub")),
        role=str(payload.get("role") or ""),
        email=payload.get("email"),
    )


def require_self(target_user_id: uuid.UUID, auth: AuthContext) -> None:
    if target_user_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")


def require_role(auth: AuthContext, *allowed_roles: str) -> None:
    if auth.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role.")


def require_teacher(auth: AuthContext) -> None:
    require_role(auth, "teacher")


def require_admin(auth: AuthContext) -> None:
    require_role(auth, "admin")


def require_teacher_or_admin(auth: AuthContext) -> None:
    require_role(auth, "teacher", "admin")


# FastAPI dependency alias (JWT role claim; extend later with DB is_active checks)
async def get_current_active_user(
    auth: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    return auth

