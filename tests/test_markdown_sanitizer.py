"""Tests for deterministic Markdown/LaTeX sanitizer pipeline."""

import pytest

from app.utils.markdown_sanitizer import (
    normalize_and_validate_problem,
    validate_math_blocks,
)


def test_normalize_fixes_unbracketed_exponents() -> None:
    d = _minimal_problem_dict()
    d["statement"] = "Use 10^23 and 10^n."
    out = normalize_and_validate_problem(d)
    assert "10^{23}" in out["statement"]
    assert "10^{n}" in out["statement"]


def test_normalize_fixes_orphan_text() -> None:
    d = _minimal_problem_dict()
    d["statement"] = "Mass in \\textamu."
    out = normalize_and_validate_problem(d)
    assert "\\text{amu}" in out["statement"]


def test_normalize_fixes_orphan_mathrm() -> None:
    d = _minimal_problem_dict()
    d["statement"] = "Formula \\mathrmMg and \\mathrmH2O."
    out = normalize_and_validate_problem(d)
    assert "\\mathrm{Mg}" in out["statement"]
    assert "\\mathrm{H2O}" in out["statement"]


def test_normalize_fixes_unclosed_mathrm() -> None:
    d = _minimal_problem_dict()
    d["statement"] = "See $\\mathrm{Mg$ and $\\mathrm{Ca$."
    out = normalize_and_validate_problem(d)
    assert "\\mathrm{Mg}" in out["statement"] and "Mg}$" in out["statement"]
    assert "\\mathrm{Ca}" in out["statement"] and "Ca}$" in out["statement"]


def test_normalize_strips_tabs_and_control_chars() -> None:
    d = _minimal_problem_dict()
    d["title"] = "Title\twith\x00null"
    out = normalize_and_validate_problem(d)
    assert "\t" not in out["title"]
    assert "\x00" not in out["title"]


def test_normalize_math_wrappers() -> None:
    d = _minimal_problem_dict()
    d["statement"] = "Formula \\( x^2 \\) and \\) y \\)."
    out = normalize_and_validate_problem(d)
    assert "\\(" not in out["statement"] and "\\)" not in out["statement"]
    assert "$" in out["statement"]


def test_normalize_trims_step_label_pipe() -> None:
    d = _minimal_problem_dict()
    d["steps"][0]["label"] = "Concept ID | Claim | Evidence"
    out = normalize_and_validate_problem(d)
    assert out["steps"][0]["label"] == "Concept ID"


def test_validate_math_balanced_braces_ok() -> None:
    ok, _ = validate_math_blocks("$q_{\\text{system}}$")
    assert ok is True


def test_validate_math_unbalanced_braces_fails() -> None:
    ok, msg = validate_math_blocks("$q_{\\text{system}$")
    assert ok is False
    assert "Unbalanced" in msg


def test_validate_math_forbidden_command_fails() -> None:
    ok, msg = validate_math_blocks("$\\begin{align} x \\end{align}$")
    assert ok is False
    assert "Forbidden" in msg


def test_normalize_and_validate_raises_on_bad_math() -> None:
    d = _minimal_problem_dict()
    # Unclosed brace inside a $...$ block so the validator can detect it
    d["steps"][0]["explanation"] = "Check $\\text{unclosed$ (missing } before $)."
    with pytest.raises(ValueError, match="Markdown/LaTeX validation failed"):
        normalize_and_validate_problem(d)


def test_normalize_and_validate_returns_new_dict() -> None:
    d = _minimal_problem_dict()
    d["statement"] = "10^5"
    out = normalize_and_validate_problem(d)
    assert out is not d
    assert "10^{5}" in out["statement"]
    assert "10^5" in d["statement"]


def _minimal_problem_dict() -> dict:
    return {
        "id": "test-id",
        "title": "Test",
        "statement": "Test statement.",
        "topic": "Test Topic",
        "difficulty": "medium",
        "level": 2,
        "blueprint": None,
        "context_tag": None,
        "steps": [
            {
                "id": "step-1",
                "step_number": 1,
                "type": "given",
                "label": "Step 1",
                "instruction": "Do it",
                "explanation": None,
                "skill_used": None,
                "correct_answer": "42",
                "equation_parts": None,
                "labeled_values": None,
                "comparison_parts": None,
            },
        ],
    }
