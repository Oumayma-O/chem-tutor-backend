from app.services.mastery_service import (
    _category_average,
    _compute_attempt_score_from_step_log,
    _compute_category_scores,
    _effective_mastery_score,
)


def test_compute_attempt_score_uses_attempted_steps_only() -> None:
    score, attempted = _compute_attempt_score_from_step_log(
        [
            {"isCorrect": True},
            {"isCorrect": False},
            {"isCorrect": True},
            {"isCorrect": "pending"},  # ignored (not a boolean)
            {},  # ignored
        ]
    )
    assert attempted == 3
    assert score == 2 / 3


def test_compute_attempt_score_empty_returns_zero() -> None:
    score, attempted = _compute_attempt_score_from_step_log([])
    assert attempted == 0
    assert score == 0.0


def test_compute_category_scores_updates_expected_buckets() -> None:
    base = {
        "conceptual": 0.5,
        "procedural": 0.5,
        "computational": 0.5,
        "representation": 0.5,
    }
    out = _compute_category_scores(
        [
            {"reasoningPattern": "Conceptual", "isCorrect": True},
            {"reasoningPattern": "Arithmetic", "isCorrect": False},
            {"reasoningPattern": "Units", "isCorrect": True},
        ],
        base,
    )
    assert out["conceptual"] > 0.5
    assert out["computational"] != 0.5
    assert out["representation"] == 0.5


def test_category_average() -> None:
    assert _category_average({}) == 0.0
    assert _category_average({"conceptual": 0.2, "procedural": 0.2, "computational": 0.2, "representation": 0.2}) == 0.2
    assert _category_average({"conceptual": 0.0, "procedural": 0.2, "computational": 0.2, "representation": 0.0}) == 0.1


def test_effective_mastery_score_fallback() -> None:
    # When band-based mastery is 0 but categories exist, use category average
    assert _effective_mastery_score(0.0, {"conceptual": 0.0, "procedural": 0.2, "computational": 0.2, "representation": 0.0}) == 0.1
    assert _effective_mastery_score(0.0, None) == 0.0
    # When band-based mastery is non-zero, use it
    assert _effective_mastery_score(0.35, {"conceptual": 0.2, "procedural": 0.2, "computational": 0.2, "representation": 0.2}) == 0.35
