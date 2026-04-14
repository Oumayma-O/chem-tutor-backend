"""Shared helpers for API routers."""

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from fastapi import HTTPException

P = ParamSpec("P")
R = TypeVar("R")


def map_unexpected_errors(
    *,
    logger,
    event: str,
    status_code: int,
    detail: str,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """
    Decorator to translate unexpected exceptions into a consistent HTTPException.
    Existing HTTPException values pass through unchanged.
    """

    def _decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(event, error=str(exc), exc_info=True)
                raise HTTPException(status_code=status_code, detail=detail) from exc

        return _wrapper

    return _decorator

