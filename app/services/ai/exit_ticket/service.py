"""ExitTicketGenerationService — AI generation for both tutor and teacher flows."""

from app.core.logging import get_logger
from app.domain.schemas.tutor import ExitTicketOutput
from app.domain.schemas.tutor.exit_ticket import ExitTicketGenerationBundle
from app.services.ai.exit_ticket import prompts
from app.services.ai.shared.lesson_guidance import build_lesson_guidance_block
from app.services.ai.shared.llm import generate_structured
from app.services.ai.shared.retries import llm_retry

logger = get_logger(__name__)


class ExitTicketGenerationService:
    # ── Tutor flow: lesson-aware generation ──────────────────

    @llm_retry
    async def generate(
        self,
        lesson_name: str,
        unit_id: str,
        errors_summary: list[dict] | None = None,
        grade_level: str | None = None,
        lesson_context: dict | None = None,
    ) -> ExitTicketOutput:
        """Generate exit ticket questions for the tutor (lesson-aware, error context)."""
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

    # ── Teacher flow: topic-based generation ─────────────────

    @llm_retry
    async def generate_for_teacher(
        self,
        topic: str,
        question_count: int = 4,
    ) -> list[dict]:
        """Generate exit ticket questions from a free-form topic string (teacher dashboard)."""
        qc = max(3, min(5, question_count))
        messages = [
            {"role": "system", "content": prompts.GENERATE_TEACHER_EXIT_TICKET_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Topic / focus: {topic}\n"
                    f"Generate exactly {qc} questions. "
                    "Use question_type 'mcq' or 'short_answer' or 'numeric' as appropriate."
                ),
            },
        ]
        raw = await generate_structured(
            messages,
            ExitTicketGenerationBundle,
            temperature=0.4,
            fast=True,
        )
        out: list[dict] = []
        for i, q in enumerate(raw.questions):
            qid = (q.id or "").strip() or f"q{i + 1}"
            out.append(
                {
                    "id": qid,
                    "prompt": q.prompt.strip(),
                    "question_type": q.question_type or "short_answer",
                    "options": list(q.options or []),
                    "correct_answer": q.correct_answer,
                    "points": float(q.points or 1.0),
                }
            )
        logger.info("teacher_exit_ticket_generated", topic=topic, question_count=qc)
        return out


def get_exit_ticket_generation_service() -> ExitTicketGenerationService:
    return ExitTicketGenerationService()
