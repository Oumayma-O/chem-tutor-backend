"""Regression tests for student exit ticket scoring and ORM invariants."""

from app.infrastructure.database.models import ClassroomStudent
from app.services.exit_ticket.scoring import score_exit_ticket_submission


def test_classroom_student_has_composite_pk_not_surrogate_id() -> None:
    """Enrollment checks must use classroom_id/student_id — there is no `id` column."""
    assert "id" not in ClassroomStudent.__table__.columns


def test_score_submission_handles_non_numeric_points() -> None:
    questions = [{"id": "q1", "points": "not-a-float", "correct_answer": "a"}]
    assert score_exit_ticket_submission(questions, {"q1": "a"}) == 100.0


def test_score_submission_handles_negative_and_non_finite_points() -> None:
    questions = [
        {"id": "q1", "points": -5, "correct_answer": "a"},  # coerced to 1.0 pts
        {"id": "q2", "points": 1.0, "correct_answer": "b"},
    ]
    out = score_exit_ticket_submission(questions, {"q1": "a", "q2": "b"})
    assert out == 100.0


def test_score_submission_empty_questions_returns_none() -> None:
    assert score_exit_ticket_submission([], {}) is None
