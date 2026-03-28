"""
Phase 1 — fast local validation for the hybrid pipeline.

- If either side looks like a symbolic/formula answer (letters in the math core),
  compare using normalised string equality only.
    - Otherwise compare numerically with tolerance; if the canonical answer includes a unit, require it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation.canonicalize import canonical_equivalent
from app.services.ai.step_validation.checkers import normalise, try_float
from app.services.ai.step_validation.symbolic_equivalent import symbolic_equivalent
from app.utils.math_eval import _strip_unit, extract_unit, numeric_equivalent, unit_equivalent

# Strip scientific-notation clusters before detecting alphabetic variables (avoid flagging `e` in 1e-3).
_RE_SCI = re.compile(r"[+\-]?\d+\.?\d*[eE][+\-]?\d+")


def _math_core_has_letters(s: str) -> bool:
    """True if the numeric/core part of the answer still contains A–Z (formula / text answer)."""
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

    formula_like = _math_core_has_letters(student_answer) or _math_core_has_letters(correct_answer)

    if formula_like:
        # No numeric shortcut: only exact normalised string match counts (handled above).
        return Phase1Result(False, None)

    ne = numeric_equivalent(student_answer, correct_answer, rtol=rtol)
    if ne is True:
        if extract_unit(correct_answer) and not unit_equivalent(student_answer, correct_answer):
            return Phase1Result(
                True,
                ValidationOutput(
                    is_correct=False,
                    student_value=try_float(student_answer),
                    correct_value=try_float(correct_answer),
                    feedback="Include the unit that goes with your value.",
                    unit_correct=False,
                    validation_method="local_numeric_missing_unit",
                ),
            )
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
        # If the student and correct answers carry DIFFERENT units, the mismatch may be
        # a valid SI prefix or unit-system conversion (e.g. "121 × 10⁻³ kg" == "121 g"
        # or "48800 J/mol" == "48.8 kJ/mol"). Local arithmetic cannot convert units,
        # so hand off to the LLM only in that case.
        student_unit = extract_unit(student_answer)
        correct_unit = extract_unit(correct_answer)
        if correct_unit and student_unit != correct_unit:
            return Phase1Result(False, None)
        # Same unit (or no unit) — deterministic numeric mismatch, no need for LLM.
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
