"""Local (non-LLM) answer comparison helpers."""

import json

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation._text_norm import normalise
from app.utils.math_eval import normalise_unit_string, numeric_equivalent


def check_string(student: str, correct: str, method: str) -> ValidationOutput:
    return ValidationOutput(is_correct=normalise(student) == normalise(correct), validation_method=method)


def _unit_match(sunit: str, cunit: str) -> bool:
    """Bare unit token comparison — delegates to ``math_eval.normalise_unit_string``."""
    return normalise_unit_string(sunit) == normalise_unit_string(cunit)


def check_multi_input(student: str, correct: str) -> ValidationOutput | None:
    """Fast-pass filter for multi-field answers (JSON wire format).

    Wire format: '{"k1": {"value": "3.60e-4", "unit": "s^-1"}, "T1": {"value": "290", "unit": "K"}}'

    Returns:
        ValidationOutput(is_correct=True)  — every field is provably correct locally
        None — any field is uncertain or wrong; the full JSON payload is deferred to Phase 2 (LLM),
               which generates per-field feedback with rounding tolerance and unit leniency.
    """
    try:
        s_data = json.loads(student)
        c_data = json.loads(correct)
    except (json.JSONDecodeError, ValueError, TypeError):
        return None

    if not isinstance(s_data, dict) or not isinstance(c_data, dict):
        return None

    for label, c_field in c_data.items():
        s_field = next((v for k, v in s_data.items() if k.lower() == label.lower()), None)
        if s_field is None:
            return None  # missing field — LLM will identify and explain

        cval = (c_field.get("value", "") if isinstance(c_field, dict) else str(c_field)).strip()
        sval = (s_field.get("value", "") if isinstance(s_field, dict) else str(s_field)).strip()
        cunit = (c_field.get("unit", "") if isinstance(c_field, dict) else "").strip()
        sunit = (s_field.get("unit", "") if isinstance(s_field, dict) else "").strip()

        if numeric_equivalent(sval, cval) is not True:
            return None  # value uncertain or wrong — defer to LLM

        if cunit and not _unit_match(sunit, cunit):
            return None  # unit formatting variant or wrong — defer to LLM

    return ValidationOutput(is_correct=True, validation_method="local_multi_input_exact")


def try_float(s: str) -> str | None:
    """Parse numeric string; return as str (matches ValidationOutput.student_value type)."""
    try:
        return str(float(s.strip()))
    except ValueError:
        return None
