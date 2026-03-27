"""Shared rules for per-level problem caps."""

from app.core.config import get_settings


def max_problems_for_level(level: int) -> int:
    settings = get_settings()
    return {
        1: settings.l1_max_problems,
        2: settings.l2_max_problems,
        3: settings.l3_max_problems,
    }.get(level, settings.l2_max_problems)

