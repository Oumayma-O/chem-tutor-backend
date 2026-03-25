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


def test_normalize_upgrades_calculator_style_equation() -> None:
    """ASCII * , e-notation, ln( → LaTeX in $...$ (Arrhenius-style substitution lines)."""
    d = _minimal_problem_dict()
    raw = "Ea = 8.314 * ln(8.10e-3/1.20e-3) / (1/298.15 - 1/318.15)"
    d["steps"][0]["instruction"] = raw
    out = normalize_and_validate_problem(d)
    s = out["steps"][0]["instruction"]
    assert s.startswith("$") and s.endswith("$")
    assert "8.10e-3" not in s
    assert r"\times 10^{-3}" in s
    assert r"\times" in s
    assert r"\ln(" in s
    assert "E_a =" in s or "E_a=" in s.replace(" ", "")


def test_normalize_skips_short_sci_without_star_or_ln() -> None:
    d = _minimal_problem_dict()
    d["statement"] = "Given rate k = 1.20e-3 at 298 K."
    out = normalize_and_validate_problem(d)
    assert "e-3" in out["statement"] or "e^{" in out["statement"]


def test_normalize_fixes_backslash_cdotk_units() -> None:
    """LLM emits \\backslash\\text{cdotK} instead of \\cdot between J/mol and K."""
    d = _minimal_problem_dict()
    d["statement"] = r"Use $R = 8.314 \text{ J/mol}\backslash\text{cdotK}$."
    out = normalize_and_validate_problem(d)
    assert r"\backslash\text{cdotK}" not in out["statement"]
    assert r"\cdot \text{K}" in out["statement"]


def test_normalize_fixes_text_cdotk_only() -> None:
    d = _minimal_problem_dict()
    d["steps"][0]["instruction"] = r"Gas constant $8.314 \text{ J/mol}\text{cdotK}$."
    out = normalize_and_validate_problem(d)
    assert r"\text{cdotK}" not in out["steps"][0]["instruction"]
    assert r"\cdot \text{K}" in out["steps"][0]["instruction"]


def test_normalize_forces_cdot_kelvin_to_text() -> None:
    """\\cdotK is invalid; \\cdot K must become \\cdot \\text{K} for KaTeX."""
    d = _minimal_problem_dict()
    d["statement"] = r"$R = 8.314 \text{ J/(mol\cdotK)}$ and also $k = 1/\text{mol}\cdot K$."
    out = normalize_and_validate_problem(d)
    assert r"\cdotK" not in out["statement"]
    assert r"\cdot \text{K}" in out["statement"]


def test_normalize_converts_slash_division_to_frac() -> None:
    """Paren division, sci-not division, E_a/R — not unit slashes inside \\text."""
    d = _minimal_problem_dict()
    d["steps"][0]["explanation"] = (
        r"$\ln\left((4.50 \times 10^{-3}) / (1.20 \times 10^{-3})\right)$ and "
        r"$E_a / R$ and $E_a/RT$ and units $8.314 \text{ J/(mol}\cdot \text{K)}$."
    )
    out = normalize_and_validate_problem(d)
    s = out["steps"][0]["explanation"]
    assert r"\frac{4.50 \times 10^{-3}}{1.20 \times 10^{-3}}" in s
    assert r"\frac{E_a}{R}" in s
    assert r"\frac{E_a}{RT}" in s
    assert r"\text{ J/(mol}" in s  # unit slash preserved inside \text


def test_normalize_fixes_lazy_x_times_before_sci_frac() -> None:
    """LLM writes 1.15x10^{-2}; must become \\times then \\frac for a/b."""
    d = _minimal_problem_dict()
    d["steps"][0]["explanation"] = r"$\ln(1.15x10^{-2} / 2.40x10^{-3})$"
    out = normalize_and_validate_problem(d)
    s = out["steps"][0]["explanation"]
    assert "x10" not in s
    assert r"\times 10" in s
    assert r"\frac{1.15 \times 10^{-2}}{2.40 \times 10^{-3}}" in s


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
