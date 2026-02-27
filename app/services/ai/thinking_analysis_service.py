"""
ThinkingAnalysisService — owns error classification and class insight generation.

Responsibilities:
  - Classify per-step errors into cognitive categories (conceptual/procedural/…)
  - Populate the Thinking Tracker panel entries
  - Generate class-level teaching insights for the teacher dashboard

SRP: this service does ONE thing — analyse thinking patterns and errors.
"""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.domain.schemas.tutor import ClassInsightsOutput, ErrorClassificationOutput
from app.services.ai import prompts
from app.services.ai.provider import AIProvider, ProviderFactory

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class ThinkingAnalysisService:
    """
    Analyses student step logs to classify errors and extract thinking patterns.

    The Thinking Tracker panel (shown after attempt completion) is powered
    by the ErrorClassificationOutput.thinking_entries field.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or ProviderFactory.get()

    @_retry
    async def classify_errors(
        self,
        incorrect_steps: list[dict],
        all_steps: list[dict],
        problem_context: str,
    ) -> ErrorClassificationOutput:
        """
        Classify errors and produce Thinking Tracker entries for ALL steps.

        incorrect_steps: list of {stepId, label, studentInput, expectedValue, timeSpent}
        all_steps:       list of {stepId, label, studentInput, isCorrect, timeSpent}
        """
        step_lines = "\n".join(
            f'- {s.get("label", s.get("stepId", "?"))}: '
            f'Input "{s["studentInput"]}" '
            f'(Expected: "{s.get("expectedValue", "N/A")}"), '
            f'Time: {s.get("timeSpent", 0)}s'
            for s in incorrect_steps
        )
        all_lines = "\n".join(
            f'- {s.get("label", s.get("stepId", "?"))}: '
            f'{"✓" if s.get("isCorrect") else "✗"} '
            f'"{s.get("studentInput", "")}" '
            f'({s.get("timeSpent", 0)}s)'
            for s in all_steps
        )

        messages = [
            {"role": "system", "content": prompts.CLASSIFY_ERROR_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Problem: {problem_context}\n\n"
                    f"Incorrect steps:\n{step_lines or '(none)'}\n\n"
                    f"All steps:\n{all_lines}\n\n"
                    "Classify each error. Populate thinkingEntries for every step. "
                    "Do NOT include correct answers."
                ),
            },
        ]
        result = await self._provider.generate_structured(
            messages=messages,
            output_schema=ErrorClassificationOutput,
            temperature=0.2,
        )
        out: ErrorClassificationOutput = result  # type: ignore[assignment]
        logger.debug(
            "errors_classified",
            error_count=len(out.errors),
            insight_preview=out.insight[:80] if out.insight else "",
        )
        return out

    @_retry
    async def generate_class_insights(
        self,
        student_count: int,
        class_mastery: float,
        error_frequencies: dict[str, int],
        misconception_data: list[dict],
    ) -> ClassInsightsOutput:
        """
        Generate 3-5 actionable teacher insights from aggregated class data.

        misconception_data: list of {tag: str, count: int}
        """
        messages = [
            {"role": "system", "content": prompts.GENERATE_CLASS_INSIGHTS_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Class data:\n"
                    f"- Total students: {student_count}\n"
                    f"- Average mastery: {class_mastery:.0%}\n"
                    f"- Error frequencies: {error_frequencies}\n"
                    f"- Top misconceptions: {misconception_data}\n\n"
                    "Generate 3-5 specific, actionable teaching insights."
                ),
            },
        ]
        result = await self._provider.generate_structured(
            messages=messages,
            output_schema=ClassInsightsOutput,
            temperature=0.3,
        )
        return result  # type: ignore[return-value]


# ── DI factory ────────────────────────────────────────────────

def get_thinking_analysis_service() -> ThinkingAnalysisService:
    return ThinkingAnalysisService()
