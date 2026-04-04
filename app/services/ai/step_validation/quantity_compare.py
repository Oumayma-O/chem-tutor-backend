"""Shared value+unit comparison using the physical-quantity registry and Pint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.domain.physical_quantity_registry import quantity_from_value_and_unit
from app.utils.math_eval import _eval_chemistry_expr, _numeric_within_rtol, normalise_unit_string

Outcome = Literal["match", "mismatch", "unknown"]

# Brief note when magnitudes match after scaling but unit strings differ (≤15 words).
_EQUIVALENT_UNIT_NOTE = "Correct equivalent units."


@dataclass(frozen=True)
class ValueUnitCompareResult:
    outcome: Outcome
    equivalent_unit_note: str | None = None


def compare_value_unit_pair(
    sval: str,
    sunit: str,
    cval: str,
    cunit: str,
    rtol: float,
    atol: float,
) -> ValueUnitCompareResult:
    """
    Compare student vs canonical numeric fields with optional units.

    Returns:
        match — values agree in a common unit system (including prefix scaling).
        mismatch — both sides parsed; dimensions or magnitudes disagree.
        unknown — unparsed value/unit, or only one side has a unit (caller may defer to LLM).
    """
    sval = (sval or "").strip()
    cval = (cval or "").strip()
    sunit = (sunit or "").strip()
    cunit = (cunit or "").strip()

    sn = _eval_chemistry_expr(sval) if sval else None
    cn = _eval_chemistry_expr(cval) if cval else None
    if sn is None or cn is None:
        return ValueUnitCompareResult("unknown")

    if not sunit and not cunit:
        if _numeric_within_rtol(sn, cn, rtol, atol):
            return ValueUnitCompareResult("match")
        return ValueUnitCompareResult("mismatch")

    if (sunit and not cunit) or (cunit and not sunit):
        return ValueUnitCompareResult("unknown")

    qs = quantity_from_value_and_unit(sn, sunit)
    qc = quantity_from_value_and_unit(cn, cunit)
    if qs is None or qc is None:
        return ValueUnitCompareResult("unknown")

    if qs.dimensionality != qc.dimensionality:
        return ValueUnitCompareResult("mismatch")

    try:
        qs_in_c = qs.to(qc.units)
    except Exception:
        return ValueUnitCompareResult("unknown")

    if not _numeric_within_rtol(float(qs_in_c.magnitude), float(qc.magnitude), rtol, atol):
        return ValueUnitCompareResult("mismatch")

    note = None
    if normalise_unit_string(sunit) != normalise_unit_string(cunit):
        note = _EQUIVALENT_UNIT_NOTE
    return ValueUnitCompareResult("match", equivalent_unit_note=note)
