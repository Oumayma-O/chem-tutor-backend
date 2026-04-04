"""
Phase 1 — fast local validation for the hybrid pipeline.

- Symbolic/formula answers: defer to Phase 2 when not an exact local match.
- Numeric comparison: if values match but units differ (or are ambiguous), defer to Phase 2.
- Naked number when canonical has a unit but the numeric value matches: defer to Phase 2 so the LLM
  can give tutor-style feedback (e.g. ask for the unit). Clear numeric mismatch still uses
  ``local_numeric_fail``; ambiguous cases still defer to Phase 2.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation.canonicalize import canonical_equivalent
from app.services.ai.step_validation.checkers import normalise, try_float
from app.services.ai.step_validation.symbolic_equivalent import symbolic_equivalent
from app.services.ai.step_validation.unit_guard import student_provided_unit
from app.utils.math_eval import (
    _strip_unit,
    extract_unit,
    latex_to_python_math,
    numeric_equivalent,
    si_units_same_dimension,
    unit_equivalent,
)

# Strip scientific-notation clusters before detecting alphabetic variables (avoid flagging `e` in 1e-3).
_RE_SCI = re.compile(r"[+\-]?\d+\.?\d*[eE][+\-]?\d+")


def _math_core_has_letters(s: str) -> bool:
    """True if the numeric/core part of the answer still contains A–Z (formula / text answer).

    Distinct from ``student_provided_unit`` in ``unit_guard``: this uses ``_strip_unit`` + sci-e
    stripping to classify formula-like answers for the numeric shortcut; that heuristic strips
    LaTeX/commands to detect a *missing* trailing unit after a value.
    """
    num_part, _ = _strip_unit((s or "").strip())
    core = _RE_SCI.sub("", num_part)
    return bool(re.search(r"[A-Za-z]", core))


@dataclass(frozen=True)
class Phase1Result:
    """If ``immediate_return`` is True, ``output`` is ready to send to the client; else run Phase 2 (LLM)."""

    immediate_return: bool
    output: ValidationOutput | None


def run_phase1_local(
    student_answer: str,
    correct_answer: str,
    *,
    rtol: float,
) -> Phase1Result:
    """
    Phase 1 waterfall — local only.

    Returns a terminal ValidationOutput when the answer is definitely correct.
    Otherwise returns ``immediate_return=False`` so the caller may invoke Phase 2.
    """
    if normalise(student_answer) == normalise(correct_answer):
        return Phase1Result(
            True,
            ValidationOutput(
                is_correct=True,
                student_value=try_float(student_answer),
                correct_value=try_float(correct_answer),
                unit_correct=True,
                validation_method="local_string_exact",
            ),
        )

    if canonical_equivalent(student_answer, correct_answer):
        return Phase1Result(
            True,
            ValidationOutput(
                is_correct=True,
                student_value=try_float(student_answer),
                correct_value=try_float(correct_answer),
                unit_correct=True,
                validation_method="local_canonical",
            ),
        )

    if symbolic_equivalent(student_answer, correct_answer):
        return Phase1Result(
            True,
            ValidationOutput(
                is_correct=True,
                student_value=try_float(student_answer),
                correct_value=try_float(correct_answer),
                unit_correct=True,
                validation_method="local_symbolic",
            ),
        )

    s_math = latex_to_python_math(student_answer)
    c_math = latex_to_python_math(correct_answer)
    formula_like = _math_core_has_letters(s_math) or _math_core_has_letters(c_math)

    if formula_like:
        # No numeric shortcut: only exact normalised string match counts (handled above).
        return Phase1Result(False, None)

    ne = numeric_equivalent(student_answer, correct_answer, rtol=rtol)
    if ne is True:
        # Unit parsing uses the same math-normalized text as numeric_equivalent (LaTeX ``\times`` etc.).
        correct_u = extract_unit(c_math)
        if correct_u:
            if not student_provided_unit(student_answer):
                return Phase1Result(False, None)
            if not unit_equivalent(s_math, c_math):
                su = extract_unit(s_math)
                cu = extract_unit(c_math)
                # Same SI dimension with different prefix (e.g. 55.4×10³ ms vs 55.4 s) — numeric_equivalent already matched in SI.
                if not (su and cu and si_units_same_dimension(su, cu)):
                    return Phase1Result(False, None)
        return Phase1Result(
            True,
            ValidationOutput(
                is_correct=True,
                student_value=try_float(student_answer),
                correct_value=try_float(correct_answer),
                unit_correct=True,
                validation_method="local_numeric",
            ),
        )

    if ne is False:
        return Phase1Result(
            True,
            ValidationOutput(
                is_correct=False,
                student_value=try_float(student_answer),
                correct_value=try_float(correct_answer),
                validation_method="local_numeric_fail",
            ),
        )

    # Cannot classify as numeric — treat as non-terminal string mismatch (LLM).
    return Phase1Result(False, None)
