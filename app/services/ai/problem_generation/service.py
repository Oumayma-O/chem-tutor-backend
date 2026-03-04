"""
ProblemGenerationService + enforce_step_types utility.

Uses get_llm / generate_structured from llm.py — no separate provider layer.
"""

import time
from typing import Literal

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.tutor import ProblemOutput
from app.services.ai.llm import generate_structured, get_llm
from app.services.ai.problem_generation import prompts

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)

_LEVEL_STEP_TYPES: dict[int, list[str]] = {
    1: ["given", "given", "given", "given", "given"],
    2: ["given", "given", "interactive", "interactive", "interactive"],
    3: ["drag_drop", "variable_id", "interactive", "interactive", "interactive"],
}


def enforce_step_types(problem: ProblemOutput, level: int) -> ProblemOutput:
    """Fix stale step types on cache hits served at a different level."""
    expected = _LEVEL_STEP_TYPES.get(level)
    if expected is None:
        return problem
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
        rag_context: dict | None = None,
    ) -> ProblemOutput:
        system = prompts.GENERATE_PROBLEM_SYSTEM.format(
            level_block=prompts.get_level_block(level),
            difficulty=difficulty,
            topic_name=topic_name,
            chapter_id=unit_id,
            focus_areas_block=f"FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else "",
            problem_style_block=f"PROBLEM STYLE: {problem_style}" if problem_style else "",
            interest_block=(
                f"The student is interested in: {', '.join(interests)}. "
                f'Set context_tag to "{interests[0]}".' if interests else ""
            ),
            grade_block=f"Student grade level: {grade_level}." if grade_level else "",
            rag_block=_format_rag(rag_context),
        ) + prompts.get_few_shot_block(unit_id, lesson_index, difficulty)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Generate a Level {level} {difficulty} problem about {topic_name}."},
        ]

        t0 = time.perf_counter()
        problem: ProblemOutput = await generate_structured(messages, ProblemOutput, temperature=0.4)
        elapsed_s = round(time.perf_counter() - t0, 3)

        problem.level = level
        logger.info(
            "problem_generated",
            provider=self.provider_name, model=self.model_name,
            execution_time_s=elapsed_s, unit=unit_id,
            lesson=lesson_index, level=level, difficulty=difficulty,
        )
        return problem


def _format_rag(rag_context: dict | None) -> str:
    if not rag_context:
        return ""
    lines = []
    if standards := rag_context.get("standards"):
        lines.append(f"STANDARDS: {'; '.join(standards)}")
    if equations := rag_context.get("equations"):
        lines.append(f"KEY EQUATIONS: {'; '.join(equations)}")
    if skills := rag_context.get("skills"):
        lines.append(f"SKILLS: {'; '.join(skills)}")
    return "\n".join(lines)


def get_problem_generation_service() -> ProblemGenerationService:
    return ProblemGenerationService()
