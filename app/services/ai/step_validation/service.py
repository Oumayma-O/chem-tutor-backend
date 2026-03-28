"""
StepValidationService — hybrid validation pipeline.

Phase 1: fast local checks (numeric tolerance or normalised string equality).
Phase 2: if Phase 1 is not confidently correct, call a fast LLM for equivalence + short hint.
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
from app.utils.math_eval import extract_unit

logger = get_logger(__name__)


def _apply_hard_requirements(
    out: ValidationOutput,
    student_answer: str,
    correct_answer: str,
) -> ValidationOutput:
    """Multi-segment canonical answers and units cannot be waived by local shortcuts or the LLM."""
    if not out.is_correct:
        return out
    if msg := first_missing_segment_message(student_answer, correct_answer):
        return ValidationOutput(
            is_correct=False,
            feedback=msg,
            validation_method="local_incomplete_segments",
        )
    # Only block when the student omitted a unit entirely.
    # If they provided a different unit (e.g. kg vs g), the LLM has already
    # evaluated the conversion — don't override with a hard unit string check.
    correct_unit = extract_unit(correct_answer)
    student_unit = extract_unit(student_answer)
    if correct_unit and not student_unit:
        return ValidationOutput(
            is_correct=False,
            feedback="Include the unit that goes with your value.",
            unit_correct=False,
            validation_method="local_unit_required",
        )
    return out


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
            return ValidationOutput(is_correct=False, feedback="Please enter an answer.", validation_method="local_empty")

        if step_type == "drag_drop":
            return check_string(student_answer, correct_answer, "drag_drop")

        if step_type == "multi_input":
            return check_multi_input(student_answer, correct_answer)

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

        out = await self._run_phase2(student_answer, correct_answer, step_label, step_instruction, problem_context)
        out = prefer_partial_multisegment_feedback(out, student_answer, correct_answer)
        return _apply_hard_requirements(out, student_answer, correct_answer)

    async def _run_phase2(
        self,
        student_answer: str,
        correct_answer: str,
        step_label: str,
        step_instruction: str | None,
        problem_context: str | None,
    ) -> ValidationOutput:
        """Phase 2: LLM equivalence verification with string-match fallback on error."""
        try:
            return await llm_equivalence_verify(
                student_answer,
                correct_answer,
                step_label=step_label,
                step_instruction=step_instruction or "",
                problem_context=problem_context or "",
            )
        except (TimeoutError, ConnectionError, ValueError) as exc:
            logger.warning("llm_equivalence_fallback", error=str(exc))
            return check_string(student_answer, correct_answer, "string_fallback")


def get_step_validation_service() -> StepValidationService:
    return StepValidationService()
