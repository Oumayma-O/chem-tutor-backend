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

    @staticmethod
    def _build_format_instruction(question_count: int, question_format: str) -> str:
        if question_format == "mcq":
            return "All questions MUST use question_type 'mcq'."
        if question_format == "structured":
            return "All questions MUST use question_type 'numeric' or 'short_answer' (no MCQ)."
        # "mixed" — balanced split
        mcq_count = question_count // 2
        structured_count = question_count - mcq_count
        return (
            f"Use a balanced mix: exactly {mcq_count} questions with question_type 'mcq' "
            f"and exactly {structured_count} questions with question_type 'numeric' or 'short_answer'."
        )

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

    # ── Teacher flow: lesson-context-aware generation ────────

    @llm_retry
    async def generate_for_teacher(
        self,
        topic: str | None = None,
        question_count: int = 4,
        difficulty: str = "medium",
        question_format: str = "mixed",
        lesson_name: str | None = None,
        lesson_context: dict | None = None,
        unit_id: str | None = None,
        grade_level: str | None = None,
    ) -> list[dict]:
        """Generate exit ticket questions for the teacher dashboard.

        When ``lesson_context`` is provided (fetched from the DB), the richer
        lesson-aware prompt is used so questions target the lesson's actual
        equations, rules, and misconceptions.  Falls back to the generic
        topic-based prompt when no curriculum context is available.
        """
        qc = max(1, min(10, question_count))
        display_name = (lesson_name or topic or "").strip() or "(lesson)"

        format_instruction = self._build_format_instruction(qc, question_format)

        if lesson_context:
            system = prompts.GENERATE_EXIT_TICKET_SYSTEM.format(
                question_count=qc,
                difficulty=difficulty,
                lesson_name=display_name,
                chapter_id=unit_id or "",
                grade_block=f"Student level: {grade_level}." if grade_level else "",
                lesson_guidance_block=build_lesson_guidance_block(lesson_context),
            )
            user_content = (
                f"Lesson: {display_name}\n"
                f"Generate exactly {qc} exit-ticket questions at {difficulty} difficulty.\n"
                f"{format_instruction}"
            )
        else:
            system = prompts.GENERATE_TEACHER_EXIT_TICKET_SYSTEM
            user_content = (
                f"Topic / focus: {display_name}\n"
                f"Difficulty: {difficulty}\n"
                f"Generate exactly {qc} questions. "
                f"{format_instruction}"
            )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
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
            # Build structured option objects from LLM MCQOption output.
            structured_options: list[dict] = []
            correct_from_options: str | None = None
            for opt in q.mcq_options or []:
                structured_options.append({
                    "text": opt.text,
                    "is_correct": opt.is_correct,
                    "misconception_tag": opt.misconception_tag if not opt.is_correct else None,
                })
                if opt.is_correct:
                    correct_from_options = opt.text
            # Prefer the derived correct answer from the structured option objects.
            resolved_correct = correct_from_options or q.correct_answer
            out.append(
                {
                    "id": qid,
                    "prompt": q.prompt.strip(),
                    "question_type": q.question_type or "short_answer",
                    "options": structured_options,
                    "unit": q.unit or None,
                    "correct_answer": resolved_correct,
                    "points": float(q.points or 1.0),
                }
            )
        logger.info(
            "teacher_exit_ticket_generated",
            lesson=display_name,
            question_count=qc,
            context_aware=lesson_context is not None,
        )
        return out


def get_exit_ticket_generation_service() -> ExitTicketGenerationService:
    return ExitTicketGenerationService()
