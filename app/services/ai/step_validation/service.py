"""
StepValidationService — fast-first validation pipeline.

Pipeline: string normalise → numeric eval → unit check → LLM fallback.
"""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.llm import generate_structured
from app.services.ai.step_validation import prompts
from app.utils.math_eval import extract_unit, numeric_equivalent, unit_equivalent

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class StepValidationService:
    async def validate(
        self,
        student_answer: str,
        correct_answer: str,
        step_label: str,
        step_type: str | None = "interactive",
        problem_context: str | None = "",
    ) -> ValidationOutput:
        student_answer = (student_answer or "").strip()
        correct_answer = (correct_answer or "").strip()

        if not student_answer:
            return ValidationOutput(is_correct=False, feedback="Please enter an answer.", validation_method="local_empty")

        if step_type == "drag_drop":
            return _check_string(student_answer, correct_answer, "drag_drop")

        if step_type == "variable_id":
            return _check_variable_id(student_answer, correct_answer)

        # Final "Answer" / "Final Answer" steps: strict 1% tolerance + unit check.
        # All intermediate steps: looser 5% tolerance, no unit penalty
        # (students often omit units mid-calculation and that's fine).
        is_final_step = "answer" in step_label.strip().lower()
        rtol = 0.01 if is_final_step else 0.05
        numeric_result = numeric_equivalent(student_answer, correct_answer, rtol=rtol)

        if numeric_result is True:
            if not is_final_step or unit_equivalent(student_answer, correct_answer):
                return ValidationOutput(
                    is_correct=True,
                    student_value=_try_float(student_answer),
                    correct_value=_try_float(correct_answer),
                    unit_correct=True,
                    validation_method="local_numeric",
                )
            su = extract_unit(student_answer)
            return ValidationOutput(
                is_correct=False,
                feedback=f"Number is correct but check your units — you wrote '{su or '(none)'}'.",
                student_value=_try_float(student_answer),
                correct_value=_try_float(correct_answer),
                unit_correct=False,
                validation_method="local_numeric_unit_fail",
            )

        if numeric_result is False:
            return ValidationOutput(
                is_correct=False,
                student_value=_try_float(student_answer),
                correct_value=_try_float(correct_answer),
                validation_method="local_numeric",
            )

        return await self._llm_validate(student_answer, correct_answer, step_label, problem_context or "")

    @_retry
    async def _llm_validate(
        self, student_answer: str, correct_answer: str, step_label: str, problem_context: str
    ) -> ValidationOutput:
        messages = [
            {"role": "system", "content": prompts.VALIDATE_ANSWER_SYSTEM.format(
                step_label=step_label, problem_context=problem_context
            )},
            {"role": "user", "content": f'Student: "{student_answer}"\nCorrect: "{correct_answer}"\nAre these equivalent?'},
        ]
        out: ValidationOutput = await generate_structured(messages, ValidationOutput, temperature=0.0, fast=True)
        out.validation_method = "llm"
        return out


def _normalise(s: str) -> str:
    return s.strip().lower().replace(" ", "").replace("×", "*").replace("·", "*").replace("−", "-").replace("–", "-")


def _check_string(student: str, correct: str, method: str) -> ValidationOutput:
    return ValidationOutput(is_correct=_normalise(student) == _normalise(correct), validation_method=method)


def _check_variable_id(student: str, correct: str) -> ValidationOutput:
    def parse_pairs(s: str) -> dict[str, str]:
        return {k.lower(): v.lower() for part in s.replace(" ", "").split(",") if "=" in part for k, _, v in [part.partition("=")]}

    s_pairs, c_pairs = parse_pairs(student), parse_pairs(correct)
    if not s_pairs or not c_pairs:
        return _check_string(student, correct, "variable_id_fallback")

    for var, cval in c_pairs.items():
        sval = s_pairs.get(var)
        if sval is None:
            return ValidationOutput(is_correct=False, feedback=f"Variable '{var}' is missing.", validation_method="variable_id")
        if numeric_equivalent(sval, cval) is False:
            return ValidationOutput(is_correct=False, feedback=f"Check the value for '{var}'.", validation_method="variable_id")
        if not unit_equivalent(sval, cval):
            return ValidationOutput(is_correct=False, feedback=f"Check the unit for '{var}'.", unit_correct=False, validation_method="variable_id")

    return ValidationOutput(is_correct=True, validation_method="variable_id")


def _try_float(s: str) -> float | None:
    try:
        return float(s.strip())
    except ValueError:
        return None


def get_step_validation_service() -> StepValidationService:
    return StepValidationService()
