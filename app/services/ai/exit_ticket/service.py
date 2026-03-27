"""ExitTicketService — end-of-session comprehension check generator."""

from app.core.logging import get_logger
from app.domain.schemas.tutor import ExitTicketOutput
from app.services.ai.exit_ticket import prompts
from app.services.ai.shared.lesson_guidance import build_lesson_guidance_block
from app.services.ai.shared.llm import generate_structured
from app.services.ai.shared.retries import llm_retry

logger = get_logger(__name__)


class ExitTicketService:
    @llm_retry
    async def generate(
        self,
        lesson_name: str,
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
            lesson_name=lesson_name,
            chapter_id=unit_id,
        )
        user_msg = f"Lesson: {lesson_name} (Unit: {unit_id})"
        if errors_summary:
            user_msg += f"\nCommon errors to address: {errors_summary}"
        user_msg += "\n\nGenerate 3 exit-ticket questions."

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ]
        result: ExitTicketOutput = await generate_structured(messages, ExitTicketOutput, temperature=0.4)
        logger.info("exit_ticket_generated", lesson=lesson_name, unit=unit_id)
        return result


def get_exit_ticket_service() -> ExitTicketService:
    return ExitTicketService()
