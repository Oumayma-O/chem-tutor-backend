"""HintGenerationService — scaffolded, misconception-aware hints."""

import re

from app.core.logging import get_logger
from app.domain.schemas.tutor import HintOutput
from app.services.ai.shared.llm import generate_structured
from app.services.ai.shared.retries import llm_retry
from app.services.ai.shared.timing import perf_now, since
from app.services.ai.hint_generation import prompts
from app.services.ai.hint_generation.validation_context import (
    resolve_validation_feedback_for_hint,
)
from app.utils.markdown_sanitizer import normalize_hint_text

logger = get_logger(__name__)


class HintGenerationService:
    @llm_retry
    async def generate(
        self,
        step_label: str,
        step_instruction: str,
        step_explanation: str | None,
        student_input: str | None,
        correct_answer: str,
        attempt_count: int = 1,
        problem_context: str = "",
        interests: list[str] | None = None,
        grade_level: str | None = None,
        key_rule: str | None = None,
        error_category: str | None = None,
        misconception_tag: str | None = None,
        validation_feedback: str | None = None,
        step_number: int | None = None,
        total_steps: int | None = None,
        step_type: str | None = None,
        prior_steps_summary: str | None = None,
    ) -> HintOutput:
        hint_level = min(attempt_count, 3)
        validation_for_model = await resolve_validation_feedback_for_hint(
            client_feedback=validation_feedback,
            student_input=student_input,
            correct_answer=correct_answer,
            step_label=step_label,
            step_instruction=step_instruction,
            problem_context=problem_context,
            step_type=step_type,
        )

        system = prompts.GENERATE_HINT_SYSTEM.format(
            hint_level=hint_level,
            key_rule_block=(
                f"Key Rule: {key_rule}\n" if key_rule else ""
            ),
            misconception_block=(
                f'\nIdentified misconception: "{misconception_tag}" (category: {error_category}). '
                "Address this without revealing the answer.\n"
                if misconception_tag else ""
            ),
            interest_block=(
                f"Student interests: {', '.join(interests)}. Use a brief analogy if natural.\n"
                if interests else ""
            ),
            grade_block=f"Student level: {grade_level}.\n" if grade_level else "",
        )

        progress_block = ""
        if step_number is not None and total_steps is not None:
            progress_block = f"Progress: step {step_number} of {total_steps}"
            if step_type:
                progress_block += f" (type: {step_type})"
            progress_block += ".\n"
        elif step_number is not None:
            progress_block = f"Progress: step {step_number}.\n"
        if prior_steps_summary:
            progress_block += f"Prior steps (already done — do not re-teach): {prior_steps_summary}\n"

        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Problem: {problem_context}\n"
                    + progress_block
                    + f'Step: {step_label} — "{step_instruction}"\n'
                    + (f'How to solve: "{step_explanation}"\n' if step_explanation else "")
                    + f'Student entered: "{student_input or "(nothing yet)"}"\n'
                    + f'Correct answer (for diagnosis only, never reveal directly): "{correct_answer}"\n'
                    + (
                        f'Validation result (authoritative — follow this): "{validation_for_model}"\n'
                        if validation_for_model
                        else ""
                    )
                    + f"Attempt #{attempt_count}\n\n"
                    + f"Generate a level {hint_level} hint scoped to THIS step only. "
                    + f'Do NOT reveal that the answer involves "{correct_answer}".'
                ),
            },
        ]
        t0 = perf_now()
        hint: HintOutput = await generate_structured(messages, HintOutput, temperature=0.5, fast=True)
        hint.processing_s = since(t0)
        hint.hint = normalize_hint_text(hint.hint)
        hint.hint = _enforce_hint_constraints(hint.hint)
        logger.debug("hint_generated", step=step_label, level=hint_level)
        return hint


def _trim_at_last_sentence_end(prefix: str) -> str | None:
    """If ``prefix`` contains sentence-ending punctuation, return through the last full sentence."""
    matches = list(re.finditer(r"[.!?](?:\s|$)", prefix))
    if not matches:
        return None
    return prefix[: matches[-1].end()].strip()


def _enforce_hint_constraints(hint: str, max_words: int = 32) -> str:
    """
    Last-mile guardrails: keep hints compact and readable even if the model drifts.
    - Collapse whitespace/newlines.
    - Hard cap word count (only when no LaTeX); never leave a dangling fragment — trim back to
      the last complete sentence inside the cap, or add an ellipsis.
    - Keep at most 2 sentences.
    """
    if not hint:
        return hint

    text = re.sub(r"\s+", " ", hint).strip()
    has_latex_tokens = any(token in text for token in ("$", "\\text{", "\\mathrm{", "\\frac{", "\\sum", "\\cdot"))
    words = text.split()
    if len(words) > max_words and not has_latex_tokens:
        chunk = " ".join(words[:max_words])
        trimmed = _trim_at_last_sentence_end(chunk)
        if trimmed:
            text = trimmed
        else:
            text = chunk.rstrip(".,;:!?") + "…"

    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) > 2:
        text = " ".join(sentences[:2]).strip()
    return text


def get_hint_generation_service() -> HintGenerationService:
    return HintGenerationService()
