"""Unit extraction for Phase 1 numeric paths (plain value + trailing unit)."""

from app.utils.math_eval import extract_unit, unit_equivalent


def test_extract_unit_plain_value_with_slash_unit() -> None:
    assert extract_unit("0.0080 M/s") == "M/s"


def test_extract_unit_no_false_positive_on_prose() -> None:
    assert extract_unit("shift left") == ""


def test_extract_unit_parenthesized_numeric() -> None:
    assert extract_unit("(0.0080) M/s") == "M/s"


def test_unit_equivalent_plain_both_sides() -> None:
    assert unit_equivalent("0.0080 M/s", "8.0e-3 M/s") is True
