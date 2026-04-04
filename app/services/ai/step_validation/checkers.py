"""Local (non-LLM) answer comparison helpers."""

import json

from app.domain.physical_quantity_registry import (
    QUANTITY_SPECS,
    quantity_for_variable_key,
    unit_matches_quantity,
)
from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation._text_norm import normalise
from app.services.ai.step_validation.quantity_compare import compare_value_unit_pair

# Align with hybrid Phase 1 intermediate steps (see StepValidationService.validate rtol).
_MULTI_INPUT_RTOL = 0.02
_MULTI_INPUT_ATOL = 1e-9


def check_string(student: str, correct: str, method: str) -> ValidationOutput:
    return ValidationOutput(is_correct=normalise(student) == normalise(correct), validation_method=method)


def check_multi_input(student: str, correct: str) -> ValidationOutput | None:
    """Fast-pass filter for multi-field answers (JSON wire format).

    Wire format: '{"k1": {"value": "3.60e-4", "unit": "s^-1"}, "T1": {"value": "290", "unit": "K"}}'

    Returns:
        ValidationOutput(is_correct=True)  — every field is provably correct locally
        ValidationOutput(is_correct=False) — wrong dimension or other definite error (registry)
        None — uncertain, wrong value, bad canonical, or unknown variable — defer to Phase 2 (LLM)
    """
    try:
        s_data = json.loads(student)
        c_data = json.loads(correct)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None

    if not isinstance(s_data, dict) or not isinstance(c_data, dict):
        return None

    optional_feedback: str | None = None

    for label, c_field in c_data.items():
        s_field = next((v for k, v in s_data.items() if k.lower() == label.lower()), None)
        if s_field is None:
            return None  # missing field — LLM will identify and explain

        cval = (c_field.get("value", "") if isinstance(c_field, dict) else str(c_field)).strip()
        sval = (s_field.get("value", "") if isinstance(s_field, dict) else str(s_field)).strip()
        cunit = (c_field.get("unit", "") if isinstance(c_field, dict) else "").strip()
        sunit = (s_field.get("unit", "") if isinstance(s_field, dict) else "").strip()

        qty = quantity_for_variable_key(label)

        if qty is not None:
            spec = QUANTITY_SPECS[qty]
            if cunit and not unit_matches_quantity(cunit, qty):
                return None  # canonical does not match registry — defer (fix problem data)
            if sunit and not unit_matches_quantity(sunit, qty):
                return ValidationOutput(
                    is_correct=False,
                    feedback=spec.wrong_dimension_hint,
                    validation_method="local_multi_input_registry_dimension",
                    unit_correct=False,
                )
            if cunit and not sunit:
                return None
            cmp = compare_value_unit_pair(sval, sunit, cval, cunit, _MULTI_INPUT_RTOL, _MULTI_INPUT_ATOL)
            if cmp.outcome != "match":
                return None
            if cmp.equivalent_unit_note:
                optional_feedback = cmp.equivalent_unit_note
            continue

        # Unknown variable: Pint-backed value+unit scaling (any equivalent metric form).
        cmp = compare_value_unit_pair(sval, sunit, cval, cunit, _MULTI_INPUT_RTOL, _MULTI_INPUT_ATOL)
        if cmp.outcome != "match":
            return None
        if cmp.equivalent_unit_note:
            optional_feedback = cmp.equivalent_unit_note

    return ValidationOutput(
        is_correct=True,
        validation_method="local_multi_input_exact",
        feedback=optional_feedback,
    )


def try_float(s: str) -> str | None:
    """Parse numeric string; return as str (matches ValidationOutput.student_value type)."""
    try:
        return str(float(s.strip()))
    except ValueError:
        return None
