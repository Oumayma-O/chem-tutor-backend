"""Local (non-LLM) answer comparison helpers."""

import json

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation._text_norm import normalise
from app.utils.math_eval import normalise_unit_string, numeric_equivalent, si_units_same_dimension


def check_string(student: str, correct: str, method: str) -> ValidationOutput:
    return ValidationOutput(is_correct=normalise(student) == normalise(correct), validation_method=method)


def _unit_match(sunit: str, cunit: str) -> bool:
    """Bare unit token comparison — delegates to ``math_eval.normalise_unit_string``."""
    return normalise_unit_string(sunit) == normalise_unit_string(cunit)


def check_multi_input(student: str, correct: str) -> ValidationOutput | None:
    """Validate multi-field answers from a JSON wire format.

    Wire format (JSON):
      '{"k1": {"value": "3.60e-4", "unit": "s^-1"}, "T1": {"value": "290", "unit": "K"}}'

    Returns:
        ValidationOutput(is_correct=True)  — all fields match
        ValidationOutput(is_correct=False) — specific error identified locally
        None — cannot determine locally; caller must run Phase 2 (LLM)
    """
    try:
        s_data = json.loads(student)
        c_data = json.loads(correct)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None  # Unparseable — fall through to LLM

    if not isinstance(s_data, dict) or not isinstance(c_data, dict):
        return None

    for label, c_field in c_data.items():
        # Case-insensitive key lookup on student data
        s_field = next((v for k, v in s_data.items() if k.lower() == label.lower()), None)

        if s_field is None:
            return ValidationOutput(
                is_correct=False,
                feedback=f"Field '{label}' is missing.",
                validation_method="multi_input",
            )

        cval = (c_field.get("value", "") if isinstance(c_field, dict) else str(c_field)).strip()
        sval = (s_field.get("value", "") if isinstance(s_field, dict) else str(s_field)).strip()
        cunit = (c_field.get("unit", "") if isinstance(c_field, dict) else "").strip()
        sunit = (s_field.get("unit", "") if isinstance(s_field, dict) else "").strip()

        # --- Value check ---
        ne = numeric_equivalent(sval, cval)
        if ne is False:
            return ValidationOutput(
                is_correct=False,
                feedback=f"Check the value for '{label}'.",
                validation_method="multi_input",
            )
        if ne is None and normalise(sval) != normalise(cval):
            return ValidationOutput(
                is_correct=False,
                feedback=f"Check the value for '{label}'.",
                validation_method="multi_input",
            )

        # --- Unit check (only when the correct answer specifies a unit) ---
        if cunit:
            if not sunit:
                return ValidationOutput(
                    is_correct=False,
                    feedback=f"Don't forget to include the unit for '{label}'.",
                    unit_correct=False,
                    validation_method="multi_input",
                )
            if not _unit_match(sunit, cunit):
                # Same SI dimension (e.g. ms vs s) — let LLM decide equivalence
                if si_units_same_dimension(sunit, cunit):
                    return None
                return ValidationOutput(
                    is_correct=False,
                    feedback=f"Check the unit for '{label}'.",
                    unit_correct=False,
                    validation_method="multi_input",
                )

    return ValidationOutput(is_correct=True, validation_method="multi_input")


def try_float(s: str) -> str | None:
    """Parse numeric string; return as str (matches ValidationOutput.student_value type)."""
    try:
        return str(float(s.strip()))
    except ValueError:
        return None
