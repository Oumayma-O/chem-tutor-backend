"""Shared API authorization dependencies and guards."""

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Query, status
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


def _auth_context_from_token(raw_token: str, *, expected_type: str | None = None) -> AuthContext:
    """Shared decode logic used by both header-based and query-param auth."""
    try:
        payload = decode_token(raw_token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        ) from exc
    token_type = payload.get("typ")
    if expected_type is not None and token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
        )
    return AuthContext(
        user_id=_parse_subject(payload.get("sub")),
        role=str(payload.get("role") or ""),
        email=payload.get("email"),
    )


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthContext:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    return _auth_context_from_token(credentials.credentials)


async def get_auth_context_from_query(
    token: str = Query(..., description="JWT access token (used by SSE endpoints that cannot send an Authorization header)"),
) -> AuthContext:
    """
    FastAPI dependency for endpoints where the client cannot set request headers
    (e.g. EventSource / SSE).  Validates the JWT using identical logic to
    `get_auth_context`; the only difference is where the token is read from.
    """
    return _auth_context_from_token(token, expected_type="sse")


def require_self(target_user_id: uuid.UUID, auth: AuthContext) -> None:
    if target_user_id != auth.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")


def require_role(auth: AuthContext, *allowed_roles: str) -> None:
    if auth.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role.")


def require_teacher(auth: AuthContext) -> None:
    require_role(auth, "teacher")


def require_admin(auth: AuthContext) -> None:
    require_role(auth, "admin", "superadmin")


def require_superadmin(auth: AuthContext) -> None:
    require_role(auth, "superadmin")


def require_teacher_or_admin(auth: AuthContext) -> None:
    require_role(auth, "teacher", "admin", "superadmin")


# FastAPI dependency alias (JWT role claim; extend later with DB is_active checks)
async def get_current_active_user(
    auth: AuthContext = Depends(get_auth_context),
) -> AuthContext:
    return auth

