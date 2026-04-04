"""Unit extraction for Phase 1 numeric paths (plain value + trailing unit)."""

from app.utils.math_eval import (
    _unit_token_to_pint_expression,
    extract_unit,
    latex_to_python_math,
    numeric_equivalent,
    si_units_same_dimension,
    unit_equivalent,
)


def test_extract_unit_plain_value_with_slash_unit() -> None:
    assert extract_unit("0.0080 M/s") == "M/s"


def test_extract_unit_no_false_positive_on_prose() -> None:
    assert extract_unit("shift left") == ""


def test_extract_unit_parenthesized_numeric() -> None:
    assert extract_unit("(0.0080) M/s") == "M/s"


def test_unit_equivalent_plain_both_sides() -> None:
    assert unit_equivalent("0.0080 M/s", "8.0e-3 M/s") is True


def test_latex_to_python_times_and_power() -> None:
    assert latex_to_python_math(r"65\times10^{-4}") == "65*10**(-4)"


def test_latex_to_python_preserves_decimal_point() -> None:
    assert latex_to_python_math("0.0065") == "0.0065"


def test_numeric_equivalent_latex_scientific_vs_decimal() -> None:
    assert numeric_equivalent(r"65\times10^{-4}", "0.0065") is True


def test_numeric_equivalent_latex_frac() -> None:
    assert numeric_equivalent(r"\frac{1}{4}", "0.25") is True


def test_latex_to_python_left_right_parens() -> None:
    assert latex_to_python_math(r"\left( 2+3 \right) \times 4") == "( 2+3 ) * 4"


def test_numeric_equivalent_ms_vs_s_scaled() -> None:
    assert numeric_equivalent("55.4*10^3 ms", "55.4 s") is True


def test_numeric_equivalent_reverse_order_ms_s() -> None:
    assert numeric_equivalent("55.4 s", "55400 ms") is True


def test_si_units_same_dimension_ms_s() -> None:
    assert si_units_same_dimension("ms", "s") is True
    assert si_units_same_dimension("m", "s") is False


def test_numeric_equivalent_g_vs_kg() -> None:
    assert numeric_equivalent("500 g", "0.5 kg") is True


def test_numeric_equivalent_same_float_different_dimensions_false() -> None:
    assert numeric_equivalent("55.4 m", "55.4 s") is False


def test_numeric_equivalent_same_float_ms_vs_s_false() -> None:
    assert numeric_equivalent("55.4 ms", "55.4 s") is False


def test_numeric_equivalent_molarity_M_vs_mM() -> None:
    assert numeric_equivalent("0.1 M", "100 mM") is True


def test_nm_is_nanometre_not_nanomolar() -> None:
    assert _unit_token_to_pint_expression("nm") == "nanometer"


def test_nM_is_nanomolar() -> None:
    expr = _unit_token_to_pint_expression("nM")
    assert expr is not None
    assert "mol" in expr.lower()


def test_numeric_equivalent_kJ_vs_J() -> None:
    assert numeric_equivalent("4.184 kJ", "4184 J") is True


def test_numeric_equivalent_molar_energy_J_per_mol_vs_kJ_per_mol() -> None:
    assert numeric_equivalent("45000 J/mol", "45 kJ/mol") is True


def test_numeric_equivalent_unicode_times_and_superscript_scientific() -> None:
    """Calculator-style UI often uses × and Unicode superscripts (e.g. 10⁴)."""
    assert numeric_equivalent("4.03 × 10⁴", "4.03e4") is True
    assert numeric_equivalent("4.03×10⁴", "40300") is True


def test_check_multi_input_ea_J_per_mol_vs_kJ_per_mol_scaled() -> None:
    from app.services.ai.step_validation.checkers import check_multi_input

    import json

    s = json.dumps({"Ea": {"value": "45000", "unit": "J/mol"}})
    c = json.dumps({"Ea": {"value": "45", "unit": "kJ/mol"}})
    out = check_multi_input(s, c)
    assert out is not None and out.is_correct is True
    assert out.feedback == "Correct equivalent units."


def test_check_multi_input_unicode_value_matches_canonical() -> None:
    from app.services.ai.step_validation.checkers import check_multi_input

    import json

    s = json.dumps({"Ea": {"value": "4.03 × 10⁴", "unit": "J/mol"}})
    c = json.dumps({"Ea": {"value": "4.03e4", "unit": "J/mol"}})
    out = check_multi_input(s, c)
    assert out is not None and out.is_correct is True


def test_check_multi_input_ea_canonical_bare_j_defers() -> None:
    """Canonical J is wrong dimension for molar energy — defer (fix problem data)."""
    from app.services.ai.step_validation.checkers import check_multi_input

    import json

    s = json.dumps({"Ea": {"value": "4.34e4", "unit": "J/mol"}})
    c = json.dumps({"Ea": {"value": "4.34e4", "unit": "J"}})
    assert check_multi_input(s, c) is None


def test_check_multi_input_ea_student_bare_j_incorrect() -> None:
    """Strict registry: E_a must be J/mol; bare J is incorrect."""
    from app.services.ai.step_validation.checkers import check_multi_input

    import json

    s = json.dumps({"Ea": {"value": "4.34e4", "unit": "J"}})
    c = json.dumps({"Ea": {"value": "4.34e4", "unit": "J/mol"}})
    out = check_multi_input(s, c)
    assert out is not None and out.is_correct is False
    assert out.validation_method == "local_multi_input_registry_dimension"


def test_check_multi_input_energy_q_wrong_molar_unit() -> None:
    """Heat q is energy (J); J/mol does not match."""
    from app.services.ai.step_validation.checkers import check_multi_input

    import json

    s = json.dumps({"q": {"value": "100", "unit": "J/mol"}})
    c = json.dumps({"q": {"value": "100", "unit": "J"}})
    out = check_multi_input(s, c)
    assert out is not None and out.is_correct is False
