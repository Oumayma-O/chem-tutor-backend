"""Tests for exit ticket scoring — app/services/exit_ticket/scoring.py.

Strategy
--------
All questions go through StepValidationService regardless of type.
MCQ answers (e.g. "A", "B") are plain strings that hit Phase 1's normalised string
match instantly — no LLM call is made for them either.

StepValidationService.validate is mocked with a simple normalised string comparison
so tests run without a real LLM or network, while still exercising all scoring logic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.domain.schemas.tutor import ValidationOutput
from app.services.exit_ticket.scoring import score_exit_ticket_submission


# ─── helpers ──────────────────────────────────────────────────────────────────

def _q(
    qid: str,
    correct_answer: str | None,
    question_type: str = "short_answer",
    points: float = 1.0,
    prompt: str = "Question",
) -> dict:
    return {
        "id": qid,
        "correct_answer": correct_answer,
        "question_type": question_type,
        "points": points,
        "prompt": prompt,
    }


def _mock_validate(student_answer: str, correct_answer: str, **_kwargs) -> ValidationOutput:
    """Simulate Phase 1 normalised string match — no LLM."""
    is_correct = student_answer.strip().lower() == correct_answer.strip().lower()
    return ValidationOutput(is_correct=is_correct, validation_method="mock_string")


@pytest.fixture
def mock_svc():
    """Patch StepValidationService.validate with the normalised-string mock."""
    with patch(
        "app.services.exit_ticket.scoring.StepValidationService.validate",
        new_callable=AsyncMock,
        side_effect=_mock_validate,
    ) as m:
        yield m


# ─── MCQ (resolved by Phase 1 — same pipeline, no LLM) ───────────────────────

class TestMcqScoring:
    @pytest.mark.asyncio
    async def test_exact_match(self, mock_svc):
        questions = [_q("q1", "A", question_type="mcq")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "A"})
        assert score == 100.0
        assert per_q == {"q1": True}

    @pytest.mark.asyncio
    async def test_case_insensitive(self, mock_svc):
        """normalise() lowercases, so 'Option B' matches 'option b'."""
        questions = [_q("q1", "option b", question_type="mcq")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "Option B"})
        assert score == 100.0
        assert per_q["q1"] is True

    @pytest.mark.asyncio
    async def test_wrong_answer(self, mock_svc):
        questions = [_q("q1", "A", question_type="mcq")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "B"})
        assert score == 0.0
        assert per_q["q1"] is False

    @pytest.mark.asyncio
    async def test_empty_answer(self, mock_svc):
        questions = [_q("q1", "A", question_type="mcq")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": ""})
        assert score == 0.0
        assert per_q["q1"] is False

    @pytest.mark.asyncio
    async def test_three_questions_two_correct(self, mock_svc):
        questions = [
            _q("q1", "A", question_type="mcq"),
            _q("q2", "B", question_type="mcq"),
            _q("q3", "C", question_type="mcq"),
        ]
        score, per_q = await score_exit_ticket_submission(
            questions, {"q1": "A", "q2": "X", "q3": "C"}
        )
        assert score == pytest.approx(100 * 2 / 3, rel=1e-3)
        assert per_q == {"q1": True, "q2": False, "q3": True}

    @pytest.mark.asyncio
    async def test_weighted_points(self, mock_svc):
        questions = [
            _q("q1", "A", question_type="mcq", points=3.0),
            _q("q2", "B", question_type="mcq", points=1.0),
        ]
        score, per_q = await score_exit_ticket_submission(
            questions, {"q1": "A", "q2": "X"}
        )
        assert score == pytest.approx(75.0, rel=1e-3)  # 3/4 * 100


# ─── Numeric / short-answer ───────────────────────────────────────────────────

class TestNumericScoring:
    @pytest.mark.asyncio
    async def test_exact_match(self, mock_svc):
        questions = [_q("q1", "2.5")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "2.5"})
        assert score == 100.0
        assert per_q["q1"] is True

    @pytest.mark.asyncio
    async def test_wrong_answer(self, mock_svc):
        questions = [_q("q1", "2.5")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "3.0"})
        assert score == 0.0
        assert per_q["q1"] is False

    @pytest.mark.asyncio
    async def test_empty_student_answer(self, mock_svc):
        questions = [_q("q1", "2.5")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": ""})
        assert score == 0.0
        assert per_q["q1"] is False

    @pytest.mark.asyncio
    async def test_service_called_with_correct_args(self, mock_svc):
        prompt = "What is the rate constant?"
        questions = [_q("q1", "2.5", prompt=prompt)]
        await score_exit_ticket_submission(questions, {"q1": "2.5"})
        mock_svc.assert_awaited_once()
        kw = mock_svc.call_args.kwargs
        assert kw["student_answer"] == "2.5"
        assert kw["correct_answer"] == "2.5"
        assert kw["step_label"] == prompt
        assert kw["step_type"] == "final_answer"

    @pytest.mark.asyncio
    async def test_service_exception_counts_as_wrong(self, mock_svc):
        mock_svc.side_effect = RuntimeError("LLM unavailable")
        questions = [_q("q1", "2.5")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "2.5"})
        assert score == 0.0
        assert per_q["q1"] is False

    @pytest.mark.asyncio
    async def test_partial_credit(self, mock_svc):
        questions = [_q("q1", "2.5"), _q("q2", "10")]
        score, per_q = await score_exit_ticket_submission(
            questions, {"q1": "2.5", "q2": "99"}
        )
        assert score == pytest.approx(50.0, rel=1e-3)
        assert per_q == {"q1": True, "q2": False}


# ─── Mixed question types ─────────────────────────────────────────────────────

class TestMixedQuestions:
    @pytest.mark.asyncio
    async def test_mcq_and_numeric_both_correct(self, mock_svc):
        questions = [_q("q1", "A", question_type="mcq"), _q("q2", "9.8")]
        score, per_q = await score_exit_ticket_submission(
            questions, {"q1": "A", "q2": "9.8"}
        )
        assert score == 100.0
        assert per_q == {"q1": True, "q2": True}

    @pytest.mark.asyncio
    async def test_mcq_correct_numeric_wrong(self, mock_svc):
        questions = [_q("q1", "B", question_type="mcq"), _q("q2", "42")]
        score, per_q = await score_exit_ticket_submission(
            questions, {"q1": "B", "q2": "0"}
        )
        assert score == pytest.approx(50.0)
        assert per_q == {"q1": True, "q2": False}

    @pytest.mark.asyncio
    async def test_ungradable_question_excluded_from_numerator(self, mock_svc):
        """Question with no correct_answer counts toward total weight but earns 0."""
        questions = [_q("q1", "A", question_type="mcq"), _q("q2", None)]
        score, per_q = await score_exit_ticket_submission(
            questions, {"q1": "A", "q2": "anything"}
        )
        assert score == pytest.approx(50.0)  # 1 earned / 2 total
        assert "q2" not in per_q

    @pytest.mark.asyncio
    async def test_skipped_answer_counts_wrong(self, mock_svc):
        questions = [_q("q1", "A", question_type="mcq"), _q("q2", "B", question_type="mcq")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "A"})
        assert score == pytest.approx(50.0)
        assert per_q["q2"] is False


# ─── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_questions_returns_none(self):
        score, per_q = await score_exit_ticket_submission([], {})
        assert score is None
        assert per_q == {}

    @pytest.mark.asyncio
    async def test_all_ungradable_returns_zero(self):
        questions = [_q("q1", None), _q("q2", "")]
        score, per_q = await score_exit_ticket_submission(
            questions, {"q1": "x", "q2": "y"}
        )
        assert score == 0.0
        assert per_q == {}

    @pytest.mark.asyncio
    async def test_non_dict_entries_skipped(self, mock_svc):
        questions = ["not a dict", None, _q("q1", "A", question_type="mcq")]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "A"})
        assert score == 100.0

    @pytest.mark.asyncio
    async def test_invalid_points_defaults_to_one(self, mock_svc):
        questions = [{"id": "q1", "correct_answer": "A", "question_type": "mcq", "points": "bad"}]
        score, per_q = await score_exit_ticket_submission(questions, {"q1": "A"})
        assert score == 100.0

    @pytest.mark.asyncio
    async def test_all_correct(self, mock_svc):
        questions = [_q(f"q{i}", str(i), question_type="mcq") for i in range(5)]
        answers = {f"q{i}": str(i) for i in range(5)}
        score, per_q = await score_exit_ticket_submission(questions, answers)
        assert score == 100.0
        assert all(per_q.values())

    @pytest.mark.asyncio
    async def test_all_wrong(self, mock_svc):
        questions = [_q("q1", "A", question_type="mcq"), _q("q2", "B", question_type="mcq")]
        score, per_q = await score_exit_ticket_submission(
            questions, {"q1": "Z", "q2": "Z"}
        )
        assert score == 0.0
        assert not any(per_q.values())
