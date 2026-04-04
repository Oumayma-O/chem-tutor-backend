"""Resolve validation text so hints are anchored to the same judgment as (or as if) validate-step."""

from __future__ import annotations

from typing import Protocol

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation.validation_feedback import FEEDBACK_GENERIC_INCORRECT


class _ValidateFn(Protocol):
    async def __call__(
        self,
        *,
        student_answer: str,
        correct_answer: str,
        step_label: str,
        step_type: str,
        problem_context: str,
        step_instruction: str | None,
    ) -> ValidationOutput: ...


async def resolve_validation_feedback_for_hint(
    *,
    client_feedback: str | None,
    student_input: str | None,
    correct_answer: str,
    step_label: str,
    step_instruction: str | None,
    problem_context: str | None,
    step_type: str | None,
    validate_fn: _ValidateFn | None = None,
) -> str | None:
    """
    ``student_input`` is the source of truth when non-empty: always run step validation and use
    that feedback for the hint model. ``client_feedback`` is ignored in that case so the server
    cannot be anchored to stale validate-step text after the student edits their answer.

    When ``student_input`` is empty/whitespace, ``client_feedback`` may be used (hint before the
    student has typed anything, or client-only context).

    ``validate_fn`` is injected by tests; when omitted the step-validation service is resolved
    lazily so the module-level import graph stays acyclic.
    """
    ans = (student_input or "").strip()
    if ans:
        if validate_fn is None:
            # Lazy import keeps the module-level dependency graph acyclic.
            from app.services.ai.step_validation.service import get_step_validation_service  # noqa: PLC0415
            validate_fn = get_step_validation_service().validate  # type: ignore[assignment]

        out = await validate_fn(
            student_answer=ans,
            correct_answer=(correct_answer or "").strip(),
            step_label=step_label,
            step_type=step_type or "interactive",
            problem_context=problem_context or "",
            step_instruction=step_instruction,
        )

        if out.is_correct:
            return None

        if out.feedback and out.feedback.strip():
            return out.feedback.strip()

        return FEEDBACK_GENERIC_INCORRECT

    if (client_feedback or "").strip():
        return (client_feedback or "").strip()

    return None
