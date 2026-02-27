"""
TutorService — thin orchestration façade.

Delegates to the dedicated SRP services:
  ProblemGenerationService, StepValidationService,
  HintGenerationService, ThinkingAnalysisService.

Kept for backward-compatibility with existing /tutor/* routes.
New code should depend on the dedicated services directly.
"""

from typing import Literal

from app.core.logging import get_logger
from app.domain.schemas.tutor import (
    ClassInsightsOutput,
    ErrorClassificationOutput,
    ExitTicketOutput,
    HintOutput,
    ProblemOutput,
    ValidationOutput,
)
from app.services.ai.hint_generation_service import HintGenerationService
from app.services.ai.problem_generation_service import ProblemGenerationService
from app.services.ai.provider import AIProvider, ProviderFactory
from app.services.ai.step_validation_service import StepValidationService
from app.services.ai.thinking_analysis_service import ThinkingAnalysisService
from app.services.ai import prompts

logger = get_logger(__name__)


class TutorService:
    """
    Stateless orchestration façade. Delegates all logic to dedicated services.
    Inject via FastAPI Depends.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or ProviderFactory.get()
        self._problem_gen = ProblemGenerationService(self._provider)
        self._validator = StepValidationService(self._provider)
        self._hint_gen = HintGenerationService(self._provider)
        self._thinking = ThinkingAnalysisService(self._provider)

    # ── Problem Generation ─────────────────────────────────────

    async def generate_problem(
        self,
        chapter_id: str,
        topic_index: int,
        topic_name: str,
        level: Literal[1, 2, 3] = 2,
        difficulty: Literal["easy", "medium", "hard"] = "medium",
        interests: list[str] | None = None,
        grade_level: str | None = None,
        focus_areas: list[str] | None = None,
        problem_style: str | None = None,
        rag_context: dict | None = None,
    ) -> ProblemOutput:
        return await self._problem_gen.generate(
            chapter_id=chapter_id,
            topic_index=topic_index,
            topic_name=topic_name,
            level=level,
            difficulty=difficulty,
            interests=interests,
            grade_level=grade_level,
            focus_areas=focus_areas,
            problem_style=problem_style,
            rag_context=rag_context,
        )

    # ── Answer Validation ──────────────────────────────────────

    async def validate_answer(
        self,
        student_answer: str,
        correct_answer: str,
        step_label: str,
        step_type: str = "interactive",
        problem_context: str = "",
    ) -> ValidationOutput:
        return await self._validator.validate(
            student_answer=student_answer,
            correct_answer=correct_answer,
            step_label=step_label,
            step_type=step_type,
            problem_context=problem_context,
        )

    # ── Hint Generation ────────────────────────────────────────

    async def generate_hint(
        self,
        step_label: str,
        step_instruction: str,
        student_input: str,
        correct_answer: str,
        attempt_count: int,
        problem_context: str = "",
        interests: list[str] | None = None,
        grade_level: str | None = None,
        rag_context: dict | None = None,
        error_category: str | None = None,
        misconception_tag: str | None = None,
    ) -> HintOutput:
        return await self._hint_gen.generate(
            step_label=step_label,
            step_instruction=step_instruction,
            student_input=student_input,
            correct_answer=correct_answer,
            attempt_count=attempt_count,
            problem_context=problem_context,
            interests=interests,
            grade_level=grade_level,
            rag_context=rag_context,
            error_category=error_category,
            misconception_tag=misconception_tag,
        )

    # ── Error Classification ───────────────────────────────────

    async def classify_errors(
        self,
        incorrect_steps: list[dict],
        all_steps: list[dict],
        problem_context: str,
    ) -> ErrorClassificationOutput:
        return await self._thinking.classify_errors(
            incorrect_steps=incorrect_steps,
            all_steps=all_steps,
            problem_context=problem_context,
        )

    # ── Exit Ticket Generation ─────────────────────────────────

    async def generate_exit_ticket(
        self,
        chapter_id: str,
        topic_name: str,
        difficulty: str = "medium",
        question_count: int = 3,
        format: str = "mixed",
    ) -> ExitTicketOutput:
        """Exit ticket generation — not delegated (kept in-service)."""
        from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
        from langchain_core.messages import SystemMessage, HumanMessage

        system = prompts.GENERATE_EXIT_TICKET_SYSTEM.format(
            question_count=question_count,
            difficulty=difficulty,
            topic_name=topic_name,
            chapter_id=chapter_id,
        )
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Generate {question_count} {format} format questions about "
                    f"{topic_name} at {difficulty} difficulty."
                ),
            },
        ]
        result = await self._provider.generate_structured(
            messages=messages,
            output_schema=ExitTicketOutput,
            temperature=0.4,
        )
        return result  # type: ignore[return-value]

    # ── Class Insights ─────────────────────────────────────────

    async def generate_class_insights(
        self,
        student_count: int,
        class_mastery: float,
        error_frequencies: dict[str, int],
        misconception_data: list[dict],
    ) -> ClassInsightsOutput:
        return await self._thinking.generate_class_insights(
            student_count=student_count,
            class_mastery=class_mastery,
            error_frequencies=error_frequencies,
            misconception_data=misconception_data,
        )


# ── DI factory ────────────────────────────────────────────────

def get_tutor_service() -> TutorService:
    return TutorService()
