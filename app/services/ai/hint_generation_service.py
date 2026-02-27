"""
HintGenerationService — owns all hint generation logic.

Hints are scaffolded in 3 levels:
  1: Conceptual nudge
  2: Procedural guidance
  3: Targeted misconception correction (no numbers)

SRP: this service does ONE thing — generate contextual hints.
"""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.domain.schemas.tutor import HintOutput
from app.services.ai import prompts
from app.services.ai.provider import AIProvider, ProviderFactory

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class HintGenerationService:
    """
    Generates scaffolded hints for a step.

    Hint level is capped at 3; attempt_count drives escalation.
    Misconception tag (from ThinkingAnalysisService) sharpens the hint when available.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or ProviderFactory.get()

    @_retry
    async def generate(
        self,
        step_label: str,
        step_instruction: str,
        student_input: str,
        correct_answer: str,
        attempt_count: int = 1,
        problem_context: str = "",
        interests: list[str] | None = None,
        grade_level: str | None = None,
        rag_context: dict | None = None,
        error_category: str | None = None,
        misconception_tag: str | None = None,
    ) -> HintOutput:
        hint_level = min(attempt_count, 3)

        misconception_block = (
            f'\nIDENTIFIED MISCONCEPTION: "{misconception_tag}" '
            f"(Category: {error_category}). "
            "Address this misconception in your hint without revealing the answer."
            if misconception_tag else ""
        )
        interest_block = (
            f"Student interests: {', '.join(interests)}. Use a brief analogy if natural."
            if interests else ""
        )
        grade_block = f"Student level: {grade_level}." if grade_level else ""
        rag_block = _format_rag(rag_context)

        system = prompts.GENERATE_HINT_SYSTEM.format(
            hint_level=hint_level,
            misconception_block=misconception_block,
            interest_block=interest_block,
            grade_block=grade_block,
            rag_block=rag_block,
        )
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Problem: {problem_context}\n"
                    f'Step: {step_label} — "{step_instruction}"\n'
                    f'Student entered: "{student_input or "(nothing yet)"}"\n'
                    f"Attempt #{attempt_count}\n\n"
                    f"Generate a level {hint_level} hint. "
                    f'Do NOT reveal that the answer involves "{correct_answer}".'
                ),
            },
        ]
        result = await self._provider.generate_structured(
            messages=messages,
            output_schema=HintOutput,
            temperature=0.5,
        )

        hint: HintOutput = result  # type: ignore[assignment]
        logger.debug(
            "hint_generated",
            step=step_label,
            level=hint_level,
            attempt=attempt_count,
        )
        return hint


# ── Helpers ───────────────────────────────────────────────────

def _format_rag(rag_context: dict | None) -> str:
    if not rag_context:
        return ""
    lines = []
    if standards := rag_context.get("standards"):
        lines.append(f"STANDARDS: {'; '.join(standards)}")
    if equations := rag_context.get("equations"):
        lines.append(f"KEY EQUATIONS: {'; '.join(equations)}")
    if skills := rag_context.get("skills"):
        lines.append(f"SKILLS: {'; '.join(skills)}")
    return "\n".join(lines)


# ── DI factory ────────────────────────────────────────────────

def get_hint_generation_service() -> HintGenerationService:
    return HintGenerationService()
