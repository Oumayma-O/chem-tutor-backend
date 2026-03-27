"""Tests for hybrid step validation — Phase 1/1.5 local logic."""

from app.domain.schemas.tutor.validation import LlmEquivalenceJudgment
from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation.completeness import (
    first_missing_segment_message,
    partial_multisegment_feedback,
    prefer_partial_multisegment_feedback,
)
from app.services.ai.step_validation.local_hybrid import run_phase1_local


def test_phase1_numeric_exact_match() -> None:
    r = run_phase1_local("18", "18", rtol=0.02)
    assert r.immediate_return is True
    assert r.output is not None
    assert r.output.is_correct is True
    assert r.output.validation_method in ("local_numeric", "local_string_exact")


def test_phase1_numeric_tolerance() -> None:
    r = run_phase1_local("18.2", "18", rtol=0.02)
    assert r.immediate_return is True
    assert r.output is not None and r.output.is_correct is True


def test_phase1_string_normalised_match() -> None:
    r = run_phase1_local("Rate = k[X][Y]^2", "rate=k[x][y]^2", rtol=0.02)
    assert r.immediate_return is True
    assert r.output is not None and r.output.is_correct is True


def test_phase1_formula_mismatch_needs_llm() -> None:
    r = run_phase1_local("k[Y]^2[X]", "k[X][Y]^2", rtol=0.02)
    assert r.immediate_return is True
    assert r.output is not None
    assert r.output.is_correct is True
    assert r.output.validation_method == "local_canonical"


def test_multi_segment_correct_requires_all_parts_in_student() -> None:
    canonical = "rate = k[X][Y]^2; 3rd order"
    assert first_missing_segment_message("rate = k[X][Y]^2", canonical) is not None
    assert partial_multisegment_feedback("rate = k[X][Y]^2", canonical) is not None
    assert first_missing_segment_message("rate = k[X][Y]^2; third order", canonical) is None


def test_partial_multisegment_only_reports_truly_missing_chunks() -> None:
    canonical = "rate = k[X][Y]^2; 3rd order"
    fb_order_only = partial_multisegment_feedback("3rd order", canonical)
    assert fb_order_only is not None
    assert "rate = k" in (fb_order_only or "")
    assert "3rd order" not in (fb_order_only or "")

    fb_rate_only = partial_multisegment_feedback("rate = k[X][Y]^2", canonical)
    assert fb_rate_only is not None
    assert "3rd" in (fb_rate_only or "") or "order" in (fb_rate_only or "").lower()

    assert partial_multisegment_feedback("nonsense xyz", canonical) is None


def test_prefer_partial_overrides_vague_llm_feedback() -> None:
    canonical = "rate = k[X][Y]^2; 3rd order"
    vague = ValidationOutput(
        is_correct=False,
        feedback="Incomplete rate law and missing order details.",
        validation_method="llm_equivalence",
    )
    fixed = prefer_partial_multisegment_feedback(vague, "3rd order", canonical)
    assert fixed.validation_method == "local_incomplete_segments"
    assert "rate = k" in (fixed.feedback or "")
    assert "Incomplete rate law and missing order" not in (fixed.feedback or "")


def test_phase1_numeric_requires_unit_when_canonical_has_unit() -> None:
    r = run_phase1_local("5", "5.0 M", rtol=0.02)
    assert r.immediate_return is True
    assert r.output is not None
    assert r.output.is_correct is False
    assert r.output.unit_correct is False
    assert r.output.validation_method == "local_numeric_missing_unit"

    r_ok = run_phase1_local("5.0 M", "5.0 M", rtol=0.02)
    assert r_ok.immediate_return is True
    assert r_ok.output is not None and r_ok.output.is_correct is True


def test_phase1_numeric_mismatch_needs_llm() -> None:
    r = run_phase1_local("9", "18", rtol=0.02)
    assert r.immediate_return is True
    assert r.output is not None
    assert r.output.is_correct is False
    assert r.output.validation_method == "local_numeric_fail"


def test_phase15_reaction_order_equivalent() -> None:
    r = run_phase1_local("3O2 + 4Al -> 2Al2O3", "4Al + 3O2 -> 2Al2O3", rtol=0.02)
    assert r.immediate_return is True
    assert r.output is not None
    assert r.output.is_correct is True
    assert r.output.validation_method == "local_canonical"


def test_llm_equivalence_hint_word_cap() -> None:
    long_hint = " ".join([f"w{i}" for i in range(30)])
    j = LlmEquivalenceJudgment(is_actually_correct=False, feedback=long_hint)
    assert len(j.feedback.split()) == 20


def test_phase16_symbolic_algebra_equivalent() -> None:
    r = run_phase1_local("2x + x", "3x", rtol=0.02)
    # With sympy installed: deterministic local pass. Without sympy: defer to Phase 2.
    if r.immediate_return:
        assert r.output is not None
        assert r.output.is_correct is True
        assert r.output.validation_method == "local_symbolic"
    else:
        assert r.output is None
