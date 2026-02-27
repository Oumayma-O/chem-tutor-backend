"""
StepValidationService — owns all step answer validation logic.

Validation pipeline (fast → slow):
  1. String normalisation (exact match after normalising whitespace/symbols)
  2. Safe numeric expression evaluation (AST-based, no eval)
     — handles "0.025*8", "0.80 - 0.40", "1.5e-3", etc.
  3. Unit check (separate from numeric check)
  4. LLM fallback (only when local check is ambiguous)

SRP: this service does ONE thing — validate a student step answer.
"""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.domain.schemas.tutor import ValidationOutput
from app.services.ai import prompts
from app.services.ai.provider import AIProvider, ProviderFactory
from app.utils.math_eval import extract_unit, numeric_equivalent, unit_equivalent

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class StepValidationService:
    """
    Validates a single step answer.

    Validation approach:
      - For numeric steps: local math parser first; LLM only as fallback.
      - For equation/drag-drop: normalised string comparison.
      - For variable-id: per-variable comparison.
      - Unit validation is always separate from numeric validation.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or ProviderFactory.get()

    async def validate(
        self,
        student_answer: str,
        correct_answer: str,
        step_label: str,
        step_type: str = "interactive",
        problem_context: str = "",
    ) -> ValidationOutput:
        """
        Validate a student's step answer.

        Returns ValidationOutput with is_correct, feedback, and diagnostic fields.
        """
        student_answer = (student_answer or "").strip()
        correct_answer = (correct_answer or "").strip()

        if not student_answer:
            return ValidationOutput(
                is_correct=False,
                feedback="Please enter an answer.",
                validation_method="local_empty",
            )

        # ── Drag-drop equation (Step 1 L3) ────────────────────
        if step_type == "drag_drop":
            return _check_string(student_answer, correct_answer, "drag_drop")

        # ── Variable identification (Step 2 L3) ───────────────
        if step_type == "variable_id":
            return _check_variable_id(student_answer, correct_answer)

        # ── Numeric / Expression steps ─────────────────────────
        numeric_result = numeric_equivalent(student_answer, correct_answer)

        if numeric_result is True:
            # Numeric match — now check units
            unit_ok = unit_equivalent(student_answer, correct_answer)
            if unit_ok:
                return ValidationOutput(
                    is_correct=True,
                    student_value=_try_float(student_answer),
                    correct_value=_try_float(correct_answer),
                    unit_correct=True,
                    validation_method="local_numeric",
                )
            else:
                su = extract_unit(student_answer)
                cu = extract_unit(correct_answer)
                return ValidationOutput(
                    is_correct=False,
                    feedback=f"Your number is correct, but check your units. "
                             f"You wrote '{su or '(none)'}' — make sure it's the right unit.",
                    student_value=_try_float(student_answer),
                    correct_value=_try_float(correct_answer),
                    unit_correct=False,
                    validation_method="local_numeric_unit_fail",
                )

        if numeric_result is False:
            return ValidationOutput(
                is_correct=False,
                feedback=None,
                student_value=_try_float(student_answer),
                correct_value=_try_float(correct_answer),
                validation_method="local_numeric",
            )

        # ── LLM fallback ───────────────────────────────────────
        return await self._llm_validate(student_answer, correct_answer, step_label, problem_context)

    @_retry
    async def _llm_validate(
        self,
        student_answer: str,
        correct_answer: str,
        step_label: str,
        problem_context: str,
    ) -> ValidationOutput:
        system = prompts.VALIDATE_ANSWER_SYSTEM.format(
            step_label=step_label,
            problem_context=problem_context,
        )
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f'Student answer: "{student_answer}"\n'
                    f'Correct answer: "{correct_answer}"\n'
                    "Are these equivalent? Respond with is_correct and optional feedback."
                ),
            },
        ]
        result = await self._provider.generate_structured(
            messages=messages,
            output_schema=ValidationOutput,
            temperature=0.0,
        )
        out: ValidationOutput = result  # type: ignore[assignment]
        out.validation_method = "llm"
        return out


# ── Local check helpers ───────────────────────────────────────

def _normalise(s: str) -> str:
    return (
        s.strip().lower()
        .replace(" ", "")
        .replace("×", "*").replace("·", "*")
        .replace("−", "-").replace("–", "-")
    )


def _check_string(student: str, correct: str, method: str) -> ValidationOutput:
    is_correct = _normalise(student) == _normalise(correct)
    return ValidationOutput(is_correct=is_correct, validation_method=method)


def _check_variable_id(student: str, correct: str) -> ValidationOutput:
    """
    Variable-id step: student answer is expected to match the correct answer
    as a comma-separated list of "var=valueunit" pairs, order-independent.

    e.g. student: "[A]0=0.75M,k=0.025M/s,t=8s"
         correct: "[A]0=0.75M,k=0.025M/s,t=8s"
    """
    def parse_pairs(s: str) -> dict[str, str]:
        pairs: dict[str, str] = {}
        for part in s.replace(" ", "").split(","):
            if "=" in part:
                k, _, v = part.partition("=")
                pairs[k.lower()] = v.lower()
        return pairs

    student_pairs = parse_pairs(student)
    correct_pairs = parse_pairs(correct)

    if not student_pairs or not correct_pairs:
        return _check_string(student, correct, "variable_id_fallback")

    # Check all correct variables are present and values match numerically
    for var, cval in correct_pairs.items():
        sval = student_pairs.get(var)
        if sval is None:
            return ValidationOutput(
                is_correct=False,
                feedback=f"Variable '{var}' is missing from your answer.",
                validation_method="variable_id",
            )
        match = numeric_equivalent(sval, cval)
        if match is False:
            return ValidationOutput(
                is_correct=False,
                feedback=f"Check the value for '{var}'.",
                validation_method="variable_id",
            )
        if not unit_equivalent(sval, cval):
            return ValidationOutput(
                is_correct=False,
                feedback=f"Check the unit for '{var}'.",
                unit_correct=False,
                validation_method="variable_id",
            )

    return ValidationOutput(is_correct=True, validation_method="variable_id")


def _try_float(s: str) -> float | None:
    try:
        return float(s.strip())
    except ValueError:
        return None


# ── DI factory ────────────────────────────────────────────────

def get_step_validation_service() -> StepValidationService:
    return StepValidationService()
