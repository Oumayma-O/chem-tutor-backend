from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.mastery_service import (
    MasteryService,
    _compute_attempt_score_from_step_log,
    _compute_category_scores,
    _effective_mastery_score,
)


def test_compute_attempt_score_uses_attempted_steps_only() -> None:
    score, attempted = _compute_attempt_score_from_step_log(
        [
            {"is_correct": True, "attempts": 1, "hints_used": 0},
            {"is_correct": False, "attempts": 2, "hints_used": 0},
            {"is_correct": True, "attempts": 2, "hints_used": 1},  # earns 0.65
            {"is_given": True, "is_correct": True},  # ignored scaffold
            {},  # earns 0.0 (treated as incorrect/no credit)
        ]
    )
    assert attempted == 4
    assert score == round((1.0 + 0.0 + 0.65 + 0.0) / 4, 4)


def test_compute_attempt_score_empty_returns_zero() -> None:
    score, attempted = _compute_attempt_score_from_step_log([])
    assert attempted == 0
    assert score == 0.0


def test_compute_attempt_score_reveal_step_gets_zero_credit() -> None:
    score, attempted = _compute_attempt_score_from_step_log(
        [
            {"is_correct": True, "attempts": 1, "hints_used": 0},
            {"is_correct": True, "was_revealed": True},
        ]
    )
    assert attempted == 2
    assert score == 0.5


def test_compute_category_scores_updates_expected_buckets() -> None:
    base = {
        "conceptual": 0.5,
        "procedural": 0.5,
        "computational": 0.5,
    }
    out = _compute_category_scores(
        [
            {"category": "conceptual", "isCorrect": True, "attempts": 1, "hints_used": 0},
            {"category": "procedural", "isCorrect": False},
            {"category": "computational", "isCorrect": True, "attempts": 2, "hints_used": 1},
        ],
        base,
        level=2,
    )
    assert out["conceptual"] > 0.5
    assert out["procedural"] < 0.5
    assert out["computational"] > 0.5


def test_compute_category_scores_falls_back_to_step_label_when_category_missing() -> None:
    """When category is absent/invalid, map canonical blueprint labels (same as enforce_step_types)."""
    base = {"conceptual": 0.0, "procedural": 0.0, "computational": 0.0}
    out = _compute_category_scores(
        [
            {"is_correct": True, "step_label": "Goal / Setup", "attempts": 1, "hints_used": 0},
            {"is_correct": True, "step_label": "Calculate", "attempts": 1, "hints_used": 0},
        ],
        base,
        level=2,
    )
    assert out["conceptual"] > 0.0
    assert out["computational"] > 0.0


def test_compute_category_scores_accepts_snake_case_is_correct() -> None:
    base = {"conceptual": 0.0, "procedural": 0.0, "computational": 0.0}
    out = _compute_category_scores(
        [{"category": "conceptual", "is_correct": True, "attempts": 1, "hints_used": 0}],
        base,
        level=2,
    )
    assert out["conceptual"] > 0.0


def test_compute_category_scores_progression_prevents_instant_hundred() -> None:
    out = _compute_category_scores(
        [{"category": "conceptual", "is_correct": True, "attempts": 1, "hints_used": 0}],
        {},
        level=2,
    )
    assert out["conceptual"] == 1.0


def test_compute_category_scores_hint_and_attempt_penalties_reduce_accuracy() -> None:
    base = {"conceptual": 1.0, "__conceptual_earned": 1.0, "__conceptual_possible": 1.0}
    out = _compute_category_scores(
        [{"category": "conceptual", "is_correct": True, "attempts": 3, "hints_used": 2}],
        base,
        level=2,
    )
    assert out["conceptual"] < 1.0
    assert out["conceptual"] == round((1.0 + 0.3) / 2.0, 4)


def test_compute_category_scores_reveal_gets_zero_credit() -> None:
    base = {"conceptual": 1.0, "__conceptual_earned": 1.0, "__conceptual_possible": 1.0}
    out = _compute_category_scores(
        [{"category": "conceptual", "is_correct": True, "was_revealed": True}],
        base,
        level=3,
    )
    assert out["conceptual"] == 0.5


def test_compute_category_scores_running_ratio_drops_after_second_problem_mistake() -> None:
    # Problem 1: 2 procedural steps, both perfect => 2/2 = 1.0
    first = _compute_category_scores(
        [
            {"category": "procedural", "is_correct": True, "attempts": 1, "hints_used": 0},
            {"category": "procedural", "is_correct": True, "attempts": 1, "hints_used": 0},
        ],
        {},
        level=2,
    )
    assert first["procedural"] == 1.0
    # Problem 2: 2 procedural steps, one incorrect then one correct => +1 / +2 totals => 3/4
    second = _compute_category_scores(
        [
            {"category": "procedural", "is_correct": False},
            {"category": "procedural", "is_correct": True, "attempts": 1, "hints_used": 0},
        ],
        first,
        level=2,
    )
    assert second["procedural"] == 0.75


def test_effective_mastery_score_fallback() -> None:
    assert _effective_mastery_score(0.0) == 0.0
    assert _effective_mastery_score(0.35) == 0.35


class _FakeAttemptRepo:
    def __init__(self) -> None:
        self.marked_score: float | None = None
        self.requested_passing_scores: list[tuple[int, float]] = []

    async def mark_complete(self, attempt_id, score, step_log):  # type: ignore[no-untyped-def]
        self.marked_score = score

    async def get_recent_scores_for_level(  # type: ignore[no-untyped-def]
        self,
        user_id,
        unit_id,
        lesson_index,
        level,
        window=5,
        passing_score=0.0,
    ):
        self.requested_passing_scores.append((level, float(passing_score)))
        # Return no historic scores so band-filling contribution is isolated to this attempt.
        return []


class _FakeMasteryRepo:
    def __init__(self, record) -> None:  # type: ignore[no-untyped-def]
        self.record = record

    async def get_for_lesson(self, user_id, unit_id, lesson_index):  # type: ignore[no-untyped-def]
        return self.record

    async def upsert(self, record):  # type: ignore[no-untyped-def]
        self.record = record
        return record


class _FakeMisconceptionRepo:
    pass


@pytest.mark.asyncio
async def test_complete_attempt_uses_penalty_scoring_and_category_ratio() -> None:
    user_id = uuid.uuid4()
    mastery_record = SimpleNamespace(
        user_id=user_id,
        unit_id="u1",
        lesson_index=1,
        mastery_score=0.0,
        attempts_count=0,
        consecutive_correct=0,
        current_difficulty="medium",
        level3_unlocked=False,
        level3_unlocked_at=None,
        category_scores={},
        error_counts={},
        recent_scores=[],
        updated_at=datetime.now(timezone.utc),
    )
    attempts = _FakeAttemptRepo()
    service = MasteryService(
        mastery_repo=_FakeMasteryRepo(mastery_record),
        attempt_repo=attempts,
        misconception_repo=_FakeMisconceptionRepo(),
    )

    # Four interactive steps:
    # - perfect procedural: 1.0
    # - conceptual with 2 hints + 1 wrong before success: 1 - 0.5 - 0.1 = 0.4
    # - computational revealed: 0.0
    # - procedural incorrect: 0.0
    step_log = [
        {"category": "procedural", "is_correct": True, "attempts": 1, "hints_used": 0},
        {"category": "conceptual", "is_correct": True, "attempts": 2, "hints_used": 2},
        {"category": "computational", "is_correct": True, "was_revealed": True},
        {"category": "procedural", "is_correct": False},
    ]

    decision = await service.complete_attempt(
        attempt_id=uuid.uuid4(),
        user_id=user_id,
        unit_id="u1",
        lesson_index=1,
        score=1.0,  # should be ignored; backend recomputes from penalized step_log.
        step_log=step_log,
        level=2,
    )

    expected_score = round((1.0 + 0.4 + 0.0 + 0.0) / 4, 4)
    assert attempts.marked_score == expected_score
    assert decision.attempt_score == expected_score
    assert decision.mastery.category_scores.procedural == 0.5  # 1.0 earned over 2 possible
    assert decision.mastery.category_scores.conceptual == 0.4  # 0.4 over 1
    assert decision.mastery.category_scores.computational == 0.0  # revealed => 0 credit


@pytest.mark.asyncio
async def test_complete_attempt_level1_empty_step_log_counts_as_full_credit() -> None:
    user_id = uuid.uuid4()
    mastery_record = SimpleNamespace(
        user_id=user_id,
        unit_id="u1",
        lesson_index=1,
        mastery_score=0.0,
        attempts_count=0,
        consecutive_correct=0,
        current_difficulty="medium",
        level3_unlocked=False,
        level3_unlocked_at=None,
        category_scores={},
        error_counts={},
        recent_scores=[],
        updated_at=datetime.now(timezone.utc),
    )
    attempts = _FakeAttemptRepo()
    service = MasteryService(
        mastery_repo=_FakeMasteryRepo(mastery_record),
        attempt_repo=attempts,
        misconception_repo=_FakeMisconceptionRepo(),
    )

    decision = await service.complete_attempt(
        attempt_id=uuid.uuid4(),
        user_id=user_id,
        unit_id="u1",
        lesson_index=1,
        score=0.0,  # ignored by backend
        step_log=[],
        level=1,
    )

    assert attempts.marked_score == 1.0
    assert decision.attempt_score == 1.0


@pytest.mark.asyncio
async def test_complete_attempt_fetches_band_scores_without_passing_threshold_filter() -> None:
    user_id = uuid.uuid4()
    mastery_record = SimpleNamespace(
        user_id=user_id,
        unit_id="u1",
        lesson_index=1,
        mastery_score=0.0,
        attempts_count=0,
        consecutive_correct=0,
        current_difficulty="medium",
        level3_unlocked=False,
        level3_unlocked_at=None,
        category_scores={},
        error_counts={},
        recent_scores=[],
        updated_at=datetime.now(timezone.utc),
    )
    attempts = _FakeAttemptRepo()
    service = MasteryService(
        mastery_repo=_FakeMasteryRepo(mastery_record),
        attempt_repo=attempts,
        misconception_repo=_FakeMisconceptionRepo(),
    )

    await service.complete_attempt(
        attempt_id=uuid.uuid4(),
        user_id=user_id,
        unit_id="u1",
        lesson_index=1,
        score=0.0,
        step_log=[{"category": "procedural", "is_correct": True, "attempts": 1, "hints_used": 0}],
        level=2,
    )

    assert attempts.requested_passing_scores == [(1, 0.0), (2, 0.0), (3, 0.0)]
