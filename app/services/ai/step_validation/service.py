"""
StepValidationService — hybrid validation pipeline.

Phase 1: fast local checks (numeric tolerance or normalised string equality).
Phase 2: if Phase 1 is not confidently correct, call a fast LLM for equivalence + short hint.

Post-processing: semicolon-separated completeness; lightweight "any letters left?" unit hint
when canonical parses a unit — catches naked numbers after LLM approval without brittle LaTeX parsing.
"""

from app.core.logging import get_logger
from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation.checkers import check_multi_input, check_string
from app.services.ai.step_validation.completeness import (
    first_missing_segment_message,
    partial_multisegment_feedback,
    prefer_partial_multisegment_feedback,
)
from app.services.ai.step_validation.llm_equivalence import llm_equivalence_verify
from app.services.ai.step_validation.local_hybrid import run_phase1_local
from app.services.ai.step_validation.validation_feedback import (
    FEEDBACK_EMPTY_STUDENT_ANSWER,
    FEEDBACK_INCLUDE_UNIT_SHORT,
    FEEDBACK_LLM_VALUE_OK_MISSING_UNIT,
    FEEDBACK_MISSING_CANONICAL,
)
from app.services.ai.step_validation.unit_guard import student_provided_unit
from app.utils.math_eval import extract_unit

logger = get_logger(__name__)


def _enforce_semicolon_segments_when_correct(
    out: ValidationOutput,
    student_answer: str,
    correct_answer: str,
) -> ValidationOutput:
    if msg := first_missing_segment_message(student_answer, correct_answer):
        return ValidationOutput(
            is_correct=False,
            feedback=msg,
            validation_method="local_incomplete_segments",
        )
    return out


def _enforce_unit_presence_hint_when_correct(
    out: ValidationOutput,
    student_answer: str,
    correct_answer: str,
) -> ValidationOutput:
    correct_unit = extract_unit(correct_answer)
    if not correct_unit or student_provided_unit(student_answer):
        return out
    method = out.validation_method or ""
    if method == "llm_equivalence":
        return ValidationOutput(
            is_correct=False,
            feedback=FEEDBACK_LLM_VALUE_OK_MISSING_UNIT,
            unit_correct=False,
            validation_method="llm_equivalence_missing_unit",
        )
    return ValidationOutput(
        is_correct=False,
        feedback=FEEDBACK_INCLUDE_UNIT_SHORT,
        unit_correct=False,
        validation_method="local_unit_required",
    )


def _apply_hard_requirements(
    out: ValidationOutput,
    student_answer: str,
    correct_answer: str,
) -> ValidationOutput:
    """Semicolon completeness + naked-number guard when canonical includes a parsed unit."""
    if not out.is_correct:
        return out
    out = _enforce_semicolon_segments_when_correct(out, student_answer, correct_answer)
    if not out.is_correct:
        return out
    return _enforce_unit_presence_hint_when_correct(out, student_answer, correct_answer)


class StepValidationService:
    async def validate(
        self,
        student_answer: str,
        correct_answer: str,
        step_label: str,
        step_type: str | None = "interactive",
        problem_context: str | None = "",
        step_instruction: str | None = None,
    ) -> ValidationOutput:
        student_answer = (student_answer or "").strip()
        correct_answer = (correct_answer or "").strip()

        if not student_answer:
            return ValidationOutput(
                is_correct=False,
                feedback=FEEDBACK_EMPTY_STUDENT_ANSWER,
                validation_method="local_empty",
            )

        if not correct_answer:
            return ValidationOutput(
                is_correct=False,
                feedback=FEEDBACK_MISSING_CANONICAL,
                validation_method="missing_canonical",
            )

        if step_type == "multi_input":
            result = check_multi_input(student_answer, correct_answer)
            if result is not None:
                return result
            # result is None → JSON parse failed or ambiguous unit → fall through to LLM

        if msg := partial_multisegment_feedback(student_answer, correct_answer):
            return ValidationOutput(
                is_correct=False,
                feedback=msg,
                validation_method="local_incomplete_segments",
            )

        is_final_step = "answer" in step_label.strip().lower()
        # Intermediate steps: ~2% relative tolerance; final numeric steps: 1%.
        rtol = 0.01 if is_final_step else 0.02

        phase1 = run_phase1_local(student_answer, correct_answer, rtol=rtol)
        if phase1.immediate_return and phase1.output is not None:
            out = prefer_partial_multisegment_feedback(phase1.output, student_answer, correct_answer)
            return _apply_hard_requirements(out, student_answer, correct_answer)

        out = await self._run_phase2(
            student_answer,
            correct_answer,
            step_label,
            step_instruction,
            problem_context,
            step_type,
        )
        out = prefer_partial_multisegment_feedback(out, student_answer, correct_answer)
        return _apply_hard_requirements(out, student_answer, correct_answer)

    async def _run_phase2(
        self,
        student_answer: str,
        correct_answer: str,
        step_label: str,
        step_instruction: str | None,
        problem_context: str | None,
        step_type: str | None,
    ) -> ValidationOutput:
        """Phase 2: LLM equivalence verification with string-match fallback on error."""
        try:
            return await llm_equivalence_verify(
                student_answer,
                correct_answer,
                step_label=step_label,
                step_instruction=step_instruction or "",
                problem_context=problem_context or "",
                step_type=step_type,
            )
        except Exception as exc:
            # LangChain / provider errors (auth, rate limit, parse failures, etc.) are not all
            # TimeoutError/ConnectionError/ValueError — degrade to string match instead of 502.
            logger.warning("llm_equivalence_fallback", error=str(exc))
            return check_string(student_answer, correct_answer, "string_fallback")


def get_step_validation_service() -> StepValidationService:
    return StepValidationService()
