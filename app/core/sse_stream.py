"""Shared Server-Sent Events helpers for polling-backed JSON streams."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable, Coroutine

from app.core.logging import get_logger

logger = get_logger(__name__)

SSE_STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


async def sse_json_poll_events(
    *,
    poll_json: Callable[[], Coroutine[None, None, str | None]],
    interval_seconds: float = 2.0,
    heartbeat_every_ticks: int = 12,
    log_event: str = "sse_poll_error",
) -> AsyncIterator[str]:
    """
    Poll `poll_json` on an interval; emit a `data:` SSE frame when JSON changes.
    `poll_json` may return None to skip a data event for that tick (e.g. no session).
    """
    last_json: str | None = None
    tick = 0
    while True:
        try:
            current_json = await poll_json()
            if current_json is not None and current_json != last_json:
                last_json = current_json
                yield f"data: {current_json}\n\n"
            tick += 1
            if tick % heartbeat_every_ticks == 0:
                yield ": heartbeat\n\n"
            await asyncio.sleep(interval_seconds)
        except asyncio.CancelledError:
            # Must propagate so tasks and DB sessions unwind cleanly (pool check-in).
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning(log_event, error=str(exc))
            await asyncio.sleep(5)
