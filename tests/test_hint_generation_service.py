from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation.validation_feedback import FEEDBACK_GENERIC_INCORRECT
from app.services.ai.hint_generation import prompts
from app.services.ai.hint_generation.validation_context import (
    resolve_validation_feedback_for_hint,
)
from app.services.ai.hint_generation.service import _enforce_hint_constraints


@pytest.mark.asyncio
async def test_resolve_validation_feedback_revalidates_ignores_stale_client_when_student_present() -> None:
    """client_feedback must not win when student_input is set — avoids split-brain stale hints."""
    mock_out = ValidationOutput(
        is_correct=False,
        feedback="Fresh server feedback for current answer.",
        validation_method="llm_equivalence",
    )
    mock_validate = AsyncMock(return_value=mock_out)
    r = await resolve_validation_feedback_for_hint(
        client_feedback="  Stale feedback from a previous wrong answer.  ",
        student_input="rate = k[A]",
        correct_answer="x",
        step_label="L",
        step_instruction=None,
        problem_context=None,
        step_type=None,
        validate_fn=mock_validate,
    )
    assert r == "Fresh server feedback for current answer."
    mock_validate.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_validation_feedback_lazy_import_uses_step_validation_service() -> None:
    """Patch the real get_step_validation_service target used by the lazy import path."""
    mock_out = ValidationOutput(
        is_correct=False,
        feedback="From lazy service.",
        validation_method="local_numeric",
    )
    mock_validate = AsyncMock(return_value=mock_out)
    mock_svc = MagicMock()
    mock_svc.validate = mock_validate
    with patch(
        "app.services.ai.step_validation.service.get_step_validation_service",
        return_value=mock_svc,
    ):
        r = await resolve_validation_feedback_for_hint(
            client_feedback="Ignored when student_input present.",
            student_input="1",
            correct_answer="2",
            step_label="L",
            step_instruction=None,
            problem_context=None,
            step_type=None,
        )
    assert r == "From lazy service."
    mock_validate.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_validation_feedback_uses_client_when_student_input_empty() -> None:
    mock_validate = AsyncMock()
    r = await resolve_validation_feedback_for_hint(
        client_feedback="  Last validate message from client.  ",
        student_input=None,
        correct_answer="1",
        step_label="L",
        step_instruction=None,
        problem_context=None,
        step_type=None,
        validate_fn=mock_validate,
    )
    assert r == "Last validate message from client."
    mock_validate.assert_not_called()


@pytest.mark.asyncio
async def test_resolve_validation_feedback_calls_validate_when_client_empty() -> None:
    mock_out = ValidationOutput(
        is_correct=False,
        feedback="Include this in your answer: 3rd order",
        validation_method="local_incomplete_segments",
    )
    mock_validate = AsyncMock(return_value=mock_out)
    r = await resolve_validation_feedback_for_hint(
        client_feedback=None,
        student_input="rate = k[X][Y]^2",
        correct_answer="rate = k[X][Y]^2; 3rd order",
        step_label="Conclusion",
        step_instruction="State the rate law and overall order.",
        problem_context="",
        step_type="interactive",
        validate_fn=mock_validate,
    )
    assert r == "Include this in your answer: 3rd order"
    mock_validate.assert_awaited_once()


@pytest.mark.asyncio
async def test_resolve_validation_feedback_fallback_when_no_grader_message() -> None:
    mock_out = ValidationOutput(is_correct=False, validation_method="local_numeric_fail")
    mock_validate = AsyncMock(return_value=mock_out)
    r = await resolve_validation_feedback_for_hint(
        client_feedback=None,
        student_input="9",
        correct_answer="18",
        step_label="L",
        step_instruction=None,
        problem_context=None,
        step_type=None,
        validate_fn=mock_validate,
    )
    assert r == FEEDBACK_GENERIC_INCORRECT


@pytest.mark.asyncio
async def test_resolve_validation_feedback_none_when_empty_student() -> None:
    mock_validate = AsyncMock()
    r = await resolve_validation_feedback_for_hint(
        client_feedback=None,
        student_input=None,
        correct_answer="1",
        step_label="L",
        step_instruction=None,
        problem_context=None,
        step_type=None,
        validate_fn=mock_validate,
    )
    assert r is None
    mock_validate.assert_not_called()


def test_generate_hint_system_format_has_no_stray_brace_fields() -> None:
    """GENERATE_HINT_SYSTEM must .format() without KeyError (LaTeX uses {{ }} in few_shots)."""
    s = prompts.GENERATE_HINT_SYSTEM.format(
        hint_level=1,
        key_rule_block="",
        misconception_block="",
        interest_block="",
        grade_block="",
    )
    assert "Current level: 1" in s
    assert len(s) > 2000  # includes few-shots + LaTeX rules


def test_enforce_hint_constraints_limits_words() -> None:
    # No $...$ here — LaTeX skips the hard word cap (see service docstring).
    raw = (
        "Rule/Equation: e minus equals p plus minus charge. Do: Check ion sign, then recompute electrons carefully "
        "using proton count before writing final value."
    )
    out = _enforce_hint_constraints(raw, max_words=20)
    assert len(out.split()) <= 20


def test_enforce_hint_constraints_never_ends_mid_phrase_after_word_cap() -> None:
    """Regression: blind words[:N] used to produce '... general form of a' (20-word chop)."""
    raw = (
        "You've got the overall order, but the rate law itself is still missing. "
        "What does the general form of a rate law look like for this reaction?"
    )
    out = _enforce_hint_constraints(raw, max_words=20)
    assert out.endswith(".")
    assert "form of a" not in out
    assert "missing." in out


def test_enforce_hint_constraints_collapses_whitespace() -> None:
    raw = "Rule/Equation: $1\\ \\mathrm{kJ}=1000\\ \\mathrm{J}$\n\nDo:   Convert J to kJ."
    out = _enforce_hint_constraints(raw, max_words=20)
    assert "\n" not in out
    assert "  " not in out
