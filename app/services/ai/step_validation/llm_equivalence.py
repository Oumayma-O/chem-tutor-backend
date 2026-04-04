"""Phase 2 LLM equivalence verification."""

from __future__ import annotations

from app.domain.schemas.tutor import LlmEquivalenceJudgment, ValidationOutput
from app.services.ai.shared.llm import generate_structured
from app.services.ai.shared.retries import llm_retry
from app.services.ai.shared.timing import perf_now, since
from app.services.ai.step_validation.few_shots import select_examples
from app.services.ai.step_validation.prompts import build_equivalence_system


@llm_retry
async def llm_equivalence_verify(
    student_answer: str,
    correct_answer: str,
    *,
    step_label: str,
    step_instruction: str,
    problem_context: str,
    step_type: str | None = None,
) -> ValidationOutput:
    """Phase 2 — LLM verifies equivalence or returns a short diagnostic hint."""
    messages = [
        {
            "role": "system",
            "content": build_equivalence_system(
                step_type=step_type,
                examples_section=select_examples(correct_answer, step_label),
                step_label=step_label or "(none)",
                step_instruction=(step_instruction or "").strip() or "(none)",
                problem_context=(problem_context or "").strip() or "(none)",
            ),
        },
        {
            "role": "user",
            "content": (
                f'STUDENT (raw):\n"{student_answer}"\n\n'
                f'CANONICAL (expected):\n"{correct_answer}"\n\n'
                "Apply the rules and return structured fields only."
            ),
        },
    ]
    t0 = perf_now()
    raw: LlmEquivalenceJudgment | None = await generate_structured(
        messages,
        LlmEquivalenceJudgment,
        temperature=0.0,
        fast=True,
    )
    processing_s = since(t0)

    if raw is None:
        raise ValueError("LLM returned no structured output for equivalence verification")

    if raw.is_actually_correct:
        return ValidationOutput(is_correct=True, validation_method="llm_equivalence", processing_s=processing_s)

    return ValidationOutput(
        is_correct=False,
        feedback=raw.feedback or "Double-check your work and try again.",
        validation_method="llm_equivalence",
        processing_s=processing_s,
    )

