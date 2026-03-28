"""Shared timing utilities for measuring LLM call latency."""

from __future__ import annotations

import time


def perf_now() -> float:
    """Return current perf counter value (seconds)."""
    return time.perf_counter()


def since(t0: float, decimals: int = 2) -> float:
    """Return seconds elapsed since t0, rounded to ``decimals`` places."""
    return round(time.perf_counter() - t0, decimals)
