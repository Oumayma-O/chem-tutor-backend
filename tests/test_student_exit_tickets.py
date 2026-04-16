"""Regression tests for student exit ticket scoring and ORM invariants."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.domain.schemas.tutor import ValidationOutput
from app.infrastructure.database.models import ClassroomStudent
from app.services.exit_ticket.scoring import score_exit_ticket_submission


def test_classroom_student_has_composite_pk_not_surrogate_id() -> None:
    """Enrollment checks must use classroom_id/student_id — there is no `id` column."""
    assert "id" not in ClassroomStudent.__table__.columns


def _mock_validate(correct: bool) -> AsyncMock:
    return AsyncMock(return_value=ValidationOutput(is_correct=correct, feedback=""))


@pytest.mark.asyncio
async def test_score_submission_handles_non_numeric_points() -> None:
    questions = [{"id": "q1", "points": "not-a-float", "correct_answer": "a"}]
    with patch(
        "app.services.exit_ticket.scoring.StepValidationService.validate",
        _mock_validate(True),
    ):
        score, _ = await score_exit_ticket_submission(questions, {"q1": "a"})
    assert score == 100.0


@pytest.mark.asyncio
async def test_score_submission_handles_negative_and_non_finite_points() -> None:
    questions = [
        {"id": "q1", "points": -5, "correct_answer": "a"},
        {"id": "q2", "points": 1.0, "correct_answer": "b"},
    ]
    with patch(
        "app.services.exit_ticket.scoring.StepValidationService.validate",
        _mock_validate(True),
    ):
        score, _ = await score_exit_ticket_submission(questions, {"q1": "a", "q2": "b"})
    assert score == 100.0


@pytest.mark.asyncio
async def test_score_submission_empty_questions_returns_none() -> None:
    score, per_q = await score_exit_ticket_submission([], {})
    assert score is None
    assert per_q == {}
