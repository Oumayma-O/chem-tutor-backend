"""AuthZ regression tests for short-lived SSE token flow."""

from fastapi import HTTPException
import pytest

from app.api.v1.authz import get_auth_context_from_query
from app.services.auth.security import create_access_token, create_sse_token, decode_token


def test_create_sse_token_sets_expected_type_claim() -> None:
    token = create_sse_token(
        user_id="11111111-1111-1111-1111-111111111111",
        email="teacher@example.com",
        role="teacher",
        ttl_seconds=120,
    )
    payload = decode_token(token)
    assert payload["typ"] == "sse"
    assert payload["role"] == "teacher"


@pytest.mark.asyncio
async def test_get_auth_context_from_query_rejects_regular_access_token() -> None:
    token = create_access_token(
        user_id="11111111-1111-1111-1111-111111111111",
        email="teacher@example.com",
        role="teacher",
    )
    with pytest.raises(HTTPException) as exc:
        await get_auth_context_from_query(token=token)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid token type."


@pytest.mark.asyncio
async def test_get_auth_context_from_query_accepts_sse_token() -> None:
    token = create_sse_token(
        user_id="11111111-1111-1111-1111-111111111111",
        email="teacher@example.com",
        role="teacher",
        ttl_seconds=120,
    )
    ctx = await get_auth_context_from_query(token=token)
    assert str(ctx.user_id) == "11111111-1111-1111-1111-111111111111"
    assert ctx.role == "teacher"
