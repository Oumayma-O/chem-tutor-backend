from app.services.mastery_service import (
    _compute_attempt_score_from_step_log,
    _compute_category_scores,
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
