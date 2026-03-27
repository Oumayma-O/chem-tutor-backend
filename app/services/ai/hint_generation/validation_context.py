"""Resolve validation text so hints are anchored to the same judgment as (or as if) validate-step."""

from __future__ import annotations

from app.services.ai.step_validation.service import get_step_validation_service


async def resolve_validation_feedback_for_hint(
    *,
    client_feedback: str | None,
    student_input: str | None,
    correct_answer: str,
    step_label: str,
    step_instruction: str | None,
    problem_context: str | None,
    step_type: str | None,
) -> str | None:
    """
    Prefer feedback from the client (same string as validate-step). If missing but the student
    entered something, run step validation once so the hint model always has grader context.
    """
    if (client_feedback or "").strip():
        return (client_feedback or "").strip()

    ans = (student_input or "").strip()
    if not ans:
        return None

    out = await get_step_validation_service().validate(
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

    return "Not quite right for this step."
