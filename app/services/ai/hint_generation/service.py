"""HintGenerationService — scaffolded, misconception-aware hints."""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.domain.schemas.tutor import HintOutput
from app.services.ai.llm import generate_structured
from app.services.ai.hint_generation import prompts
from app.services.ai.lesson_guidance import build_lesson_guidance_block

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class HintGenerationService:
    @_retry
    async def generate(
        self,
        step_label: str,
        step_instruction: str,
        student_input: str | None,
        correct_answer: str,
        attempt_count: int = 1,
        problem_context: str = "",
        interests: list[str] | None = None,
        grade_level: str | None = None,
        lesson_context: dict | None = None,
        error_category: str | None = None,
        misconception_tag: str | None = None,
        validation_feedback: str | None = None,
    ) -> HintOutput:
        hint_level = min(attempt_count, 3)
        system = prompts.GENERATE_HINT_SYSTEM.format(
            hint_level=hint_level,
            misconception_block=(
                f'\nIDENTIFIED MISCONCEPTION: "{misconception_tag}" (Category: {error_category}). '
                "Address this in your hint without revealing the answer."
                if misconception_tag else ""
            ),
            interest_block=(
                f"Student interests: {', '.join(interests)}. Use a brief analogy if natural."
                if interests else ""
            ),
            grade_block=f"Student level: {grade_level}." if grade_level else "",
            lesson_guidance_block=build_lesson_guidance_block(lesson_context),
        )
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Problem: {problem_context}\n"
                    f'Step: {step_label} — "{step_instruction}"\n'
                    f'Student entered: "{student_input or "(nothing yet)"}"\n'
                    + (f'Validation result: "{validation_feedback}"\n' if validation_feedback else "")
                    + f"Attempt #{attempt_count}\n\n"
                    f"Generate a level {hint_level} hint. "
                    f'Do NOT reveal that the answer involves "{correct_answer}".'
                ),
            },
        ]
        hint: HintOutput = await generate_structured(messages, HintOutput, temperature=0.5, fast=True)
        logger.debug("hint_generated", step=step_label, level=hint_level)
        return hint


def get_hint_generation_service() -> HintGenerationService:
    return HintGenerationService()
