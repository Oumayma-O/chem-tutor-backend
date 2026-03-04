"""ExitTicketService — end-of-session comprehension check generator."""

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.logging import get_logger
from app.domain.schemas.tutor import ExitTicketOutput
from app.services.ai.llm import generate_structured
from app.services.ai.exit_ticket import prompts

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
        rag_context: dict | None = None,
    ) -> ExitTicketOutput:
        system = prompts.GENERATE_EXIT_TICKET_SYSTEM.format(
            grade_block=f"Student level: {grade_level}." if grade_level else "",
            rag_block=_format_rag(rag_context),
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


def _format_rag(rag_context: dict | None) -> str:
    if not rag_context:
        return ""
    lines = []
    if s := rag_context.get("standards"):
        lines.append(f"STANDARDS: {'; '.join(s)}")
    if e := rag_context.get("equations"):
        lines.append(f"KEY EQUATIONS: {'; '.join(e)}")
    return "\n".join(lines)


def get_exit_ticket_service() -> ExitTicketService:
    return ExitTicketService()
