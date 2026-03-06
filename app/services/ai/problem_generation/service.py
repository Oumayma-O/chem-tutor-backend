"""
ProblemGenerationService + enforce_step_types utility.

Uses get_llm / generate_structured from llm.py — no separate provider layer.

Problem id: always assigned server-side (UUID). The LLM may return an id in
structured output, but we overwrite it so "See Another" never gets a duplicate id.
"""

import time
import uuid
from typing import TYPE_CHECKING, Literal

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.tutor import ProblemOutput
from app.services.ai.llm import generate_structured, get_llm
from app.services.ai.problem_generation import prompts

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)

def _expected_step_types(level: int, n: int) -> list[str]:
    """Return the expected step-type sequence for `level` with `n` steps (3–6)."""
    if level == 1:
        return ["given"] * n
    if level == 2:
        given = min(2, n)
        return ["given"] * given + ["interactive"] * (n - given)
    # level == 3
    if n == 1:
        return ["drag_drop"]
    if n == 2:
        return ["drag_drop", "variable_id"]
    return ["drag_drop", "variable_id"] + ["interactive"] * (n - 2)


def enforce_step_types(problem: ProblemOutput, level: int) -> ProblemOutput:
    """Fix stale step types on cache hits served at a different level."""
    expected = _expected_step_types(level, len(problem.steps))
    for step, expected_type in zip(problem.steps, expected):
        step.type = expected_type  # type: ignore[assignment]
        if expected_type == "drag_drop" and not step.equation_parts:
            step.type = "interactive"  # type: ignore[assignment]
        if expected_type == "variable_id" and not step.known_variables:
            step.type = "interactive"  # type: ignore[assignment]
    return problem


class ProblemGenerationService:
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def provider_name(self) -> str:
        return self._settings.default_ai_provider

    @property
    def model_name(self) -> str:
        return {
            "openai":    self._settings.openai_model,
            "anthropic": self._settings.anthropic_model,
            "gemini":    self._settings.gemini_model,
        }.get(self._settings.default_ai_provider, "unknown")

    @property
    def prompt_version(self) -> str:
        return prompts.PROMPT_VERSION

    @_retry
    async def generate(
        self,
        unit_id: str,
        lesson_index: int,
        topic_name: str,
        level: Literal[1, 2, 3] = 2,
        difficulty: Literal["easy", "medium", "hard"] = "medium",
        interests: list[str] | None = None,
        grade_level: str | None = None,
        focus_areas: list[str] | None = None,
        problem_style: str | None = None,
        lesson_context: dict | None = None,
        db: "AsyncSession | None" = None,
    ) -> ProblemOutput:
        strategy = prompts.get_strategy_for_unit(unit_id)
        step_count = prompts.get_step_count_for_prompt(strategy, difficulty)
        strategy_block = prompts.STRATEGY_BLOCKS.get(strategy, prompts.STRATEGY_BLOCKS["quantitative"])
        interest_slug = (interests[0] if interests else "general chemistry").strip() or "general chemistry"

        # Fetch curated few-shot example from DB when a session is available
        db_example: dict | None = None
        if db is not None:
            from app.services.ai.problem_generation.few_shots import get_few_shot
            db_example = await get_few_shot(db, unit_id, lesson_index, difficulty, level)

        system = prompts.GENERATE_PROBLEM_SYSTEM.format(
            strategy_block=strategy_block,
            level_block=prompts.get_level_block(level, step_count),
            step_count=step_count,
            interest_slug=interest_slug,
            difficulty=difficulty,
            topic_name=topic_name,
            unit_id=unit_id,
            focus_areas_block=f"FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else "",
            problem_style_block=f"PROBLEM STYLE: {problem_style}" if problem_style else "",
            interest_block=(
                f"The student is interested in: {', '.join(interests)}. "
                f'Set context_tag to "{interests[0]}".' if interests else ""
            ),
            grade_block=f"Student grade level: {grade_level}." if grade_level else "",
            rag_block=_format_lesson_context(lesson_context),
        ) + prompts.get_few_shot_block(unit_id, lesson_index, difficulty, level, db_example=db_example)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Generate a Level {level} {difficulty} problem about {topic_name}."},
        ]

        t0 = time.perf_counter()
        problem: ProblemOutput = await generate_structured(messages, ProblemOutput, temperature=0.4)
        elapsed_s = round(time.perf_counter() - t0, 3)

        problem.level = level
        problem.strategy = strategy
        problem.id = str(uuid.uuid4())
        # Fill step ids if LLM omitted them (structured output often skips step id)
        for step in problem.steps:
            if not (step.id or "").strip():
                step.id = f"{problem.id}-step-{step.step_number}"

        logger.info(
            "problem_generated",
            provider=self.provider_name, model=self.model_name,
            problem_id=problem.id,
            execution_time_s=elapsed_s, unit=unit_id,
            lesson=lesson_index, level=level, difficulty=difficulty,
            strategy=strategy, step_count=len(problem.steps),
        )
        return problem


def _format_lesson_context(ctx: dict | None) -> str:
    """Format lesson key_equations and objectives for injection into the system prompt."""
    if not ctx:
        return ""
    lines = []
    if equations := ctx.get("equations"):
        lines.append(f"KEY EQUATIONS: {'; '.join(equations)}")
    if objectives := ctx.get("objectives"):
        lines.append(f"LEARNING OBJECTIVES: {'; '.join(objectives)}")
    return "\n".join(lines)


def get_problem_generation_service() -> ProblemGenerationService:
    return ProblemGenerationService()
