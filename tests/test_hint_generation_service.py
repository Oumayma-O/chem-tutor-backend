from unittest.mock import AsyncMock

import pytest

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.hint_generation import prompts
from app.services.ai.hint_generation.validation_context import (
    resolve_validation_feedback_for_hint,
)
from app.services.ai.hint_generation.service import _enforce_hint_constraints


@pytest.mark.asyncio
async def test_resolve_validation_feedback_prefers_client_string() -> None:
    r = await resolve_validation_feedback_for_hint(
        client_feedback="  Include the overall order.  ",
        student_input="rate = k[A]",
        correct_answer="x",
        step_label="L",
        step_instruction=None,
        problem_context=None,
        step_type=None,
    )
    assert r == "Include the overall order."


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
    assert r == "Not quite right for this step."


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
