"""Local (non-LLM) answer comparison helpers."""

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation._text_norm import normalise
from app.utils.math_eval import numeric_equivalent, unit_equivalent


def check_string(student: str, correct: str, method: str) -> ValidationOutput:
    return ValidationOutput(is_correct=normalise(student) == normalise(correct), validation_method=method)


def check_multi_input(student: str, correct: str) -> ValidationOutput:
    def parse_pairs(s: str) -> dict[str, str]:
        return {k.lower(): v.lower() for part in s.replace(" ", "").split(",") if "=" in part for k, _, v in [part.partition("=")]}

    s_pairs, c_pairs = parse_pairs(student), parse_pairs(correct)
    if not s_pairs or not c_pairs:
        return check_string(student, correct, "multi_input_fallback")

    for var, cval in c_pairs.items():
        sval = s_pairs.get(var)
        if sval is None:
            return ValidationOutput(is_correct=False, feedback=f"Field '{var}' is missing.", validation_method="multi_input")
        if numeric_equivalent(sval, cval) is False:
            return ValidationOutput(is_correct=False, feedback=f"Check the value for '{var}'.", validation_method="multi_input")
        if not unit_equivalent(sval, cval):
            return ValidationOutput(is_correct=False, feedback=f"Check the unit for '{var}'.", unit_correct=False, validation_method="multi_input")

    return ValidationOutput(is_correct=True, validation_method="multi_input")


# Backward-compatible alias for legacy step_type name.
def check_variable_id(student: str, correct: str) -> ValidationOutput:
    return check_multi_input(student, correct)


def try_float(s: str) -> str | None:
    """Parse numeric string; return as str (matches ValidationOutput.student_value type)."""
    try:
        return str(float(s.strip()))
    except ValueError:
        return None
