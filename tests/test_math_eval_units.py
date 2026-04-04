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
