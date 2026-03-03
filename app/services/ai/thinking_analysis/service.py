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
        student_input: str,
        step_instruction: str,
        correct_answer: str,
        thinking_entries: list[dict],
        topic_name: str = "",
    ) -> ErrorClassificationOutput:
        messages = [
            {"role": "system", "content": prompts.CLASSIFY_ERRORS_SYSTEM.format(topic_name=topic_name)},
            {
                "role": "user",
                "content": (
                    f"Step instruction: {step_instruction}\n"
                    f"Correct answer: {correct_answer}\n"
                    f"Student's final answer: {student_input}\n"
                    f"Thinking entries: {thinking_entries}"
                ),
            },
        ]
        result: ErrorClassificationOutput = await generate_structured(
            messages, ErrorClassificationOutput, temperature=0.2, fast=True
        )
        logger.debug("errors_classified", topic=topic_name)
        return result

    @_retry
    async def generate_class_insights(
        self,
        topic_name: str,
        error_patterns: list[dict],
        student_count: int,
    ) -> ClassInsightsOutput:
        messages = [
            {"role": "system", "content": prompts.CLASS_INSIGHTS_SYSTEM.format(student_count=student_count)},
            {
                "role": "user",
                "content": (
                    f"Topic: {topic_name}\n"
                    f"Error patterns from {student_count} students:\n{error_patterns}"
                ),
            },
        ]
        result: ClassInsightsOutput = await generate_structured(messages, ClassInsightsOutput, temperature=0.3)
        logger.info("class_insights_generated", topic=topic_name, students=student_count)
        return result


def get_thinking_analysis_service() -> ThinkingAnalysisService:
    return ThinkingAnalysisService()
