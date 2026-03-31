"""
Phase 1 — fast local validation for the hybrid pipeline.

- Symbolic/formula answers: defer to Phase 2 when not an exact local match.
- Numeric comparison: if values match but units differ (or are ambiguous), defer to Phase 2.
- Naked number when canonical has a unit: immediate ``local_numeric_missing_unit``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation.canonicalize import canonical_equivalent
from app.services.ai.step_validation.checkers import normalise, try_float
from app.services.ai.step_validation.validation_feedback import FEEDBACK_INCLUDE_UNIT_SHORT
from app.services.ai.step_validation.symbolic_equivalent import symbolic_equivalent
from app.services.ai.step_validation.unit_guard import student_provided_unit
from app.utils.math_eval import _strip_unit, extract_unit, numeric_equivalent, unit_equivalent

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

    formula_like = _math_core_has_letters(student_answer) or _math_core_has_letters(correct_answer)

    if formula_like:
        # No numeric shortcut: only exact normalised string match counts (handled above).
        return Phase1Result(False, None)

    ne = numeric_equivalent(student_answer, correct_answer, rtol=rtol)
    if ne is True:
        correct_u = extract_unit(correct_answer)
        if correct_u:
            if not student_provided_unit(student_answer):
                return Phase1Result(
                    True,
                    ValidationOutput(
                        is_correct=False,
                        student_value=try_float(student_answer),
                        correct_value=try_float(correct_answer),
                        feedback=FEEDBACK_INCLUDE_UNIT_SHORT,
                        unit_correct=False,
                        validation_method="local_numeric_missing_unit",
                    ),
                )
            if not unit_equivalent(student_answer, correct_answer):
                # Numbers match but units differ or parse ambiguously — let Phase 2 judge (M vs M/s, g vs kg, etc.).
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
