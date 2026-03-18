"""
Problem generation: LLM → validate/sanitize → ProblemOutput.

- Problem id is always assigned server-side (UUID). LLM output id is ignored.
- Uses get_llm / generate_structured from llm.py. No separate provider layer.
"""

import time
import uuid
from typing import TYPE_CHECKING, Literal

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.tutor import ProblemOutput
from app.services.ai.lesson_guidance import build_lesson_guidance_block
from app.services.ai.llm import generate_structured, get_llm
from app.services.ai.problem_generation import prompts
from app.utils.markdown_sanitizer import normalize_and_validate_problem

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

# ── Constants ───────────────────────────────────────────────────────────────

MAX_GENERATION_ATTEMPTS = 3
DEFAULT_TEMPERATURE = 0.5

_LLM_RETRY = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)

# Label keywords → step type (for level 3 / cache correction)
_DRAG_DROP_LABELS = {"equation", "substitute", "formula", "expression", "draft", "arrange", "order", "sequence", "configuration"}
_VARIABLE_ID_LABELS = {"knowns", "given", "variables", "identify", "known values"}


# ── Step type enforcement (cache / level correction) ─────────────────────────

def _expected_step_types(level: int, n: int, labels: list[str] | None = None) -> list[str]:
    """Expected step-type sequence for level with n steps (3–6)."""
    if level == 1:
        return ["given"] * n
    if level == 2:
        given = min(2, n)
        return ["given"] * given + ["interactive"] * (n - given)
    # Level 3: infer from labels, fallback interactive
    result = []
    for label in labels or []:
        lower = label.lower()
        if any(kw in lower for kw in _DRAG_DROP_LABELS):
            result.append("drag_drop")
        elif any(kw in lower for kw in _VARIABLE_ID_LABELS):
            result.append("variable_id")
        else:
            result.append("interactive")
    while len(result) < n:
        result.append("interactive")
    return result[:n]


def enforce_step_types(problem: ProblemOutput, level: int) -> ProblemOutput:
    """Fix step types on cache hits when served at a different level."""
    labels = [s.label for s in problem.steps]
    expected = _expected_step_types(level, len(problem.steps), labels=labels)
    for step, exp_type in zip(problem.steps, expected):
        step.type = exp_type  # type: ignore[assignment]
        if exp_type == "drag_drop" and not step.equation_parts:
            step.type = "interactive"  # type: ignore[assignment]
        if exp_type == "variable_id" and not step.labeled_values:
            step.type = "interactive"  # type: ignore[assignment]
        if exp_type == "comparison" and not step.comparison_parts:
            step.type = "interactive"  # type: ignore[assignment]
    return problem


# ── Sanitization ─────────────────────────────────────────────────────────────

def _strip_nulls(s: str) -> str:
    """Remove null bytes (PostgreSQL text columns)."""
    return s.replace("\x00", "") if s else s


def sanitize_problem(problem: ProblemOutput) -> ProblemOutput:
    """Strip null bytes and trim pipe-separated step labels."""
    problem.title = _strip_nulls(problem.title)
    problem.statement = _strip_nulls(problem.statement)
    problem.lesson = _strip_nulls(problem.lesson)
    for step in problem.steps:
        step.label = _strip_nulls(step.label)
        if " | " in step.label:
            step.label = step.label.split(" | ")[0].strip()
        step.instruction = _strip_nulls(step.instruction)
        if step.explanation:
            step.explanation = _strip_nulls(step.explanation)
        if step.correct_answer:
            step.correct_answer = _strip_nulls(step.correct_answer)
        if step.skill_used:
            step.skill_used = _strip_nulls(step.skill_used)
        if step.equation_parts:
            step.equation_parts = [_strip_nulls(p) for p in step.equation_parts]
        if step.labeled_values:
            for lv in step.labeled_values:
                lv.variable = _strip_nulls(lv.variable)
                lv.value = _strip_nulls(lv.value)
                lv.unit = _strip_nulls(lv.unit)
        if step.comparison_parts:
            step.comparison_parts = [_strip_nulls(p) for p in step.comparison_parts]
    return problem


# ── ProblemGenerationService ─────────────────────────────────────────────────

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
        }.get(self._settings.default_ai_provider, "unknown")

    @property
    def prompt_version(self) -> str:
        return prompts.PROMPT_VERSION

    def _build_system_prompt(
        self,
        *,
        resolved_blueprint: str,
        lesson_name: str,
        unit_id: str,
        level: int,
        difficulty: str,
        step_count: int,
        interests: list[str] | None,
        grade_level: str | None,
        focus_areas: list[str] | None,
        problem_style: str | None,
        lesson_context: dict | None,
        db_examples: list[dict],
    ) -> str:
        """Build the system prompt for problem generation."""
        config = prompts.BLUEPRINT_CONFIG.get(resolved_blueprint, prompts.BLUEPRINT_CONFIG["solver"])
        labels_block = " | ".join(config["labels"])
        blueprint_logic = config["logic"]
        interest_slug = (interests[0] if interests else "general chemistry").strip() or "general chemistry"
        skill_list = prompts.collect_skills_from_lesson_objectives(lesson_context, resolved_blueprint)

        return prompts.GENERATE_PROBLEM_SYSTEM.format(
            blueprint=resolved_blueprint,
            labels_block=labels_block,
            blueprint_logic=blueprint_logic,
            level_block=prompts.get_level_block(level, step_count),
            step_count=step_count,
            interest_slug=interest_slug,
            difficulty=difficulty,
            lesson_name=lesson_name,
            unit_id=unit_id,
            focus_areas_block=f"FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else "",
            problem_style_block=f"PROBLEM STYLE: {problem_style}" if problem_style else "",
            interest_block=(
                f"The student is interested in: {', '.join(interests)}. "
                f'Set context_tag to "{interests[0]}".' if interests else ""
            ),
            grade_block=f"Student grade level: {grade_level}." if grade_level else "",
            skills_block=prompts.build_skills_block(skill_list),
            lesson_guidance_block=build_lesson_guidance_block(lesson_context),
        ) + prompts.get_few_shot_block(db_examples)

    @_LLM_RETRY
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
    ) -> ProblemOutput:
        resolved_blueprint = blueprint or "solver"
        step_count = prompts.get_step_count_for_prompt(resolved_blueprint)

        db_examples: list[dict] = []
        if db is not None:
            from app.services.ai.problem_generation.few_shots import get_few_shots
            db_examples = await get_few_shots(db, unit_id, lesson_index, difficulty, level)

        system = self._build_system_prompt(
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
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Generate a Level {level} {difficulty} problem about {lesson_name}."},
        ]

        last_error: ValueError | None = None
        problem: ProblemOutput | None = None
        t0 = time.perf_counter()

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

        elapsed_s = round(time.perf_counter() - t0, 3)
        if problem is None:
            raise ValueError(
                f"Failed to generate valid LaTeX after {MAX_GENERATION_ATTEMPTS} attempts. Last error: {last_error!s}"
            ) from last_error

        problem.level = level
        problem.blueprint = resolved_blueprint
        problem.id = str(uuid.uuid4())
        for step in problem.steps:
            if not (step.id or "").strip():
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
