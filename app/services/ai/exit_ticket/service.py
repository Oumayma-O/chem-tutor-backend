"""ExitTicketService — end-of-session comprehension check generator."""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.domain.schemas.tutor import ExitTicketOutput
from app.services.ai.llm import generate_structured
from app.services.ai.exit_ticket import prompts
from app.services.ai.lesson_guidance import build_lesson_guidance_block

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class ExitTicketService:
    @_retry
    async def generate(
        self,
        topic_name: str,
        unit_id: str,
        errors_summary: list[dict] | None = None,
        grade_level: str | None = None,
        lesson_context: dict | None = None,
    ) -> ExitTicketOutput:
        system = prompts.GENERATE_EXIT_TICKET_SYSTEM.format(
            grade_block=f"Student level: {grade_level}." if grade_level else "",
            lesson_guidance_block=build_lesson_guidance_block(lesson_context),
            question_count=3,
            difficulty="medium",
            topic_name=topic_name,
            chapter_id=unit_id,
        )
        user_msg = f"Topic: {topic_name} (Unit: {unit_id})"
        if errors_summary:
            user_msg += f"\nCommon errors to address: {errors_summary}"
        user_msg += "\n\nGenerate 3 exit-ticket questions."

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]
        result: ExitTicketOutput = await generate_structured(messages, ExitTicketOutput, temperature=0.4)
        logger.info("exit_ticket_generated", topic=topic_name, unit=unit_id)
        return result


def get_exit_ticket_service() -> ExitTicketService:
    return ExitTicketService()
