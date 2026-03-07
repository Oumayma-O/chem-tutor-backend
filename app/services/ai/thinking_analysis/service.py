"""ThinkingAnalysisService — error classification + class-level insights."""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.domain.schemas.tutor import ClassInsightsOutput, ErrorClassificationOutput
from app.services.ai.llm import generate_structured
from app.services.ai.thinking_analysis import prompts

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class ThinkingAnalysisService:
    @_retry
    async def classify_errors(
        self,
        incorrect_steps: list[dict],
        all_steps: list[dict],
        problem_context: str = "",
    ) -> ErrorClassificationOutput:
        messages = [
            {"role": "system", "content": prompts.CLASSIFY_ERROR_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Problem context: {problem_context}\n"
                    f"Incorrect steps: {incorrect_steps}\n"
                    f"All attempt steps: {all_steps}\n"
                    "Return one error entry per incorrect step."
                ),
            },
        ]
        result: ErrorClassificationOutput = await generate_structured(
            messages, ErrorClassificationOutput, temperature=0.2, fast=True
        )
        logger.debug("errors_classified", error_count=len(result.errors))
        return result

    @_retry
    async def generate_class_insights(
        self,
        student_count: int,
        class_mastery: float,
        error_frequencies: dict[str, int],
        misconception_data: list[dict],
    ) -> ClassInsightsOutput:
        messages = [
            {
                "role": "system",
                "content": prompts.GENERATE_CLASS_INSIGHTS_SYSTEM.format(student_count=student_count),
            },
            {
                "role": "user",
                "content": (
                    f"Student count: {student_count}\n"
                    f"Class mastery: {class_mastery:.2f}\n"
                    f"Error frequencies: {error_frequencies}\n"
                    f"Misconception data: {misconception_data}\n"
                ),
            },
        ]
        result: ClassInsightsOutput = await generate_structured(messages, ClassInsightsOutput, temperature=0.3)
        logger.info("class_insights_generated", students=student_count)
        return result


def get_thinking_analysis_service() -> ThinkingAnalysisService:
    return ThinkingAnalysisService()
