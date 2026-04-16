"""
Problem generation: LLM → validate/sanitize → ProblemOutput.

- Problem id is always assigned server-side (UUID). LLM output id is ignored.
- Uses generate_structured from llm.py. No separate provider layer.
"""

import uuid

from app.services.ai.shared.timing import perf_now, since
from typing import TYPE_CHECKING, Literal

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.tutor import ProblemOutput
from app.services.ai.shared.llm import generate_structured
from app.services.ai.shared.retries import llm_retry
from app.services.ai.problem_generation import prompts
from app.services.ai.problem_generation.sanitize import sanitize_problem
from app.utils.markdown_sanitizer import normalize_and_validate_problem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

MAX_GENERATION_ATTEMPTS = 3
DEFAULT_TEMPERATURE = 0.5


class ProblemGenerationService:
    """Generates chemistry problems via LLM with validation and sanitization."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def provider_name(self) -> str:
        return self._settings.default_ai_provider

    @property
    def model_name(self) -> str:
        return {
            "openai": self._settings.openai_model,
            "anthropic": self._settings.anthropic_model,
            "gemini": self._settings.gemini_model,
            "mistral": self._settings.mistral_model,
        }.get(self._settings.default_ai_provider, "unknown")

    @property
    def prompt_version(self) -> str:
        return prompts.PROMPT_VERSION

    @llm_retry
    async def generate(
        self,
        unit_id: str,
        lesson_index: int,
        lesson_name: str,
        level: Literal[1, 2, 3] = 2,
        difficulty: Literal["easy", "medium", "hard"] = "medium",
        interests: list[str] | None = None,
        grade_level: str | None = None,
        focus_areas: list[str] | None = None,
        problem_style: str | None = None,
        lesson_context: dict | None = None,
        db: "AsyncSession | None" = None,
        blueprint: str | None = None,
        previous_problems: list[str] | None = None,
    ) -> ProblemOutput:
        resolved_blueprint = blueprint or "solver"
        step_count = prompts.get_step_count_for_prompt(resolved_blueprint)

        db_examples: list[dict] = []
        if db is not None:
            from app.services.ai.problem_generation.few_shots import get_few_shots
            db_examples = await get_few_shots(db, unit_id, lesson_index, difficulty, level)

        system = prompts.build_system_prompt(
            resolved_blueprint=resolved_blueprint,
            lesson_name=lesson_name,
            unit_id=unit_id,
            level=level,
            difficulty=difficulty,
            step_count=step_count,
            interests=interests,
            grade_level=grade_level,
            focus_areas=focus_areas,
            problem_style=problem_style,
            lesson_context=lesson_context,
            db_examples=db_examples,
            previous_problems=previous_problems,
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Generate a Level {level} {difficulty} problem about {lesson_name}."},
        ]

        last_error: ValueError | None = None
        problem: ProblemOutput | None = None
        t0 = perf_now()

        for attempt in range(MAX_GENERATION_ATTEMPTS):
            raw = await generate_structured(messages, ProblemOutput, temperature=DEFAULT_TEMPERATURE)
            problem_dict = raw.model_dump(mode="json")
            try:
                problem_dict = normalize_and_validate_problem(problem_dict)
            except ValueError as e:
                last_error = e
                logger.warning(
                    "markdown_validation_failed",
                    error=str(e), problem_id=raw.id, attempt=attempt + 1, max_attempts=MAX_GENERATION_ATTEMPTS,
                )
                continue
            problem = ProblemOutput.model_validate(problem_dict)
            break

        elapsed_s = since(t0, decimals=3)
        if problem is None:
            raise ValueError(
                f"Failed to generate valid LaTeX after {MAX_GENERATION_ATTEMPTS} attempts. Last error: {last_error!s}"
            ) from last_error

        problem.level = level
        problem.blueprint = resolved_blueprint
        problem.id = str(uuid.uuid4())
        for step in problem.steps:
            step.id = f"{problem.id}-step-{step.step_number}"

        sanitize_problem(problem)

        logger.info(
            "problem_generated",
            provider=self.provider_name,
            model=self.model_name,
            problem_id=problem.id,
            execution_time_s=elapsed_s,
            unit=unit_id,
            lesson=lesson_index,
            level=level,
            difficulty=difficulty,
            blueprint=resolved_blueprint,
            step_count=len(problem.steps),
        )
        return problem



def get_problem_generation_service() -> ProblemGenerationService:
    return ProblemGenerationService()
