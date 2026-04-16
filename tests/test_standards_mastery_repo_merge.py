"""Regression tests for standards sample merge behavior."""

import uuid

from app.infrastructure.database.repositories.standards_mastery_repo import (
    StandardsMasteryRepository,
    _StdAggRow,
)


def test_merge_standard_samples_uses_weighted_average() -> None:
    user_id = uuid.uuid4()
    rows = [
        _StdAggRow(
            code="STD-1",
            framework="NGSS",
            title="Title",
            description="Desc",
            user_id=user_id,
            score_sum=9.0,
            score_count=10,
        ),
        _StdAggRow(
            code="STD-1",
            framework="NGSS",
            title="Title",
            description="Desc",
            user_id=user_id,
            score_sum=1.0,
            score_count=1,
        ),
    ]
    out = StandardsMasteryRepository._merge_standard_samples(rows)
    assert len(out) == 1
    # Weighted mean: (9 + 1) / (10 + 1) = 10/11
    assert out[0].avg_mastery == 10.0 / 11.0


def test_merge_standard_samples_merges_by_standard_and_user() -> None:
    user_a = uuid.uuid4()
    user_b = uuid.uuid4()
    rows = [
        _StdAggRow("STD-1", "NGSS", None, None, user_a, 2.0, 2),
        _StdAggRow("STD-2", "NGSS", None, None, user_a, 1.0, 1),
        _StdAggRow("STD-1", "NGSS", None, None, user_b, 3.0, 3),
    ]
    out = StandardsMasteryRepository._merge_standard_samples(rows)
    keys = {(r.code, r.user_id) for r in out}
    assert ("STD-1", user_a) in keys
    assert ("STD-1", user_b) in keys
    assert ("STD-2", user_a) in keys
