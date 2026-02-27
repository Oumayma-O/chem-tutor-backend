"""
ProblemGenerationService — owns all problem generation logic.

Responsibilities:
  - Build prompts for Level 1 (worked), Level 2 (faded), Level 3 (unresolved)
  - Call the AI provider with structured output parsing
  - Return validated ProblemOutput models
  - No caching, no routing logic — see ProblemCacheService for caching

SRP: this service does ONE thing — generate problems.
"""

import time
from typing import Literal

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.tutor import ProblemOutput
from app.services.ai import prompts
from app.services.ai.provider import AIProvider, ProviderFactory

logger = get_logger(__name__)

_retry = retry(
    retry=retry_if_exception_type((TimeoutError, ConnectionError, Exception)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)


class ProblemGenerationService:
    """
    Stateless service. Instantiate with a provider or use the default.
    Exposes provider_name, model_name, prompt_version for benchmarking.
    """

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider or ProviderFactory.get()
        self._settings = get_settings()

    # ── Benchmarking metadata ──────────────────────────────────

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def model_name(self) -> str:
        return {
            "openai":    self._settings.openai_model,
            "anthropic": self._settings.anthropic_model,
            "gemini":    self._settings.gemini_model,
        }.get(self._provider.name, "unknown")

    @property
    def prompt_version(self) -> str:
        return prompts.PROMPT_VERSION

    # ── Core generation ────────────────────────────────────────

    @_retry
    async def generate(
        self,
        chapter_id: str,
        topic_index: int,
        topic_name: str,
        level: Literal[1, 2, 3] = 2,
        difficulty: Literal["easy", "medium", "hard"] = "medium",
        interests: list[str] | None = None,
        grade_level: str | None = None,
        focus_areas: list[str] | None = None,
        problem_style: str | None = None,
        rag_context: dict | None = None,
    ) -> ProblemOutput:
        """
        Generate a problem at the requested level.

        Level 1 → fully worked example (all steps given)
        Level 2 → faded example (steps 1-2 given, 3-5 interactive)
        Level 3 → fully unresolved (drag-drop + variable-id + interactive)
        """
        interest_block = (
            f"The student is interested in: {', '.join(interests)}. "
            "Weave this context into the scenario naturally without changing the chemistry. "
            f"Set context_tag to \"{interests[0]}\"."
            if interests else ""
        )
        grade_block = (
            f"Student grade level: {grade_level}. Adjust language complexity accordingly."
            if grade_level else ""
        )
        focus_block = (
            f"FOCUS AREAS: Target these weak spots: {', '.join(focus_areas)}"
            if focus_areas else ""
        )
        style_block = f"PROBLEM STYLE: {problem_style}" if problem_style else ""
        rag_block = _format_rag(rag_context)

        level_block = prompts.get_level_block(level)
        few_shot_block = prompts.get_few_shot_block(chapter_id, topic_index, difficulty)

        system = prompts.GENERATE_PROBLEM_SYSTEM.format(
            level_block=level_block,
            difficulty=difficulty,
            topic_name=topic_name,
            chapter_id=chapter_id,
            focus_areas_block=focus_block,
            problem_style_block=style_block,
            interest_block=interest_block,
            grade_block=grade_block,
            rag_block=rag_block,
        ) + few_shot_block

        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    f"Generate a Level {level} {difficulty} difficulty problem about {topic_name}."
                ),
            },
        ]

        t0 = time.perf_counter()
        result = await self._provider.generate_structured(
            messages=messages,
            output_schema=ProblemOutput,
            temperature=0.4,
        )
        elapsed_s = round(time.perf_counter() - t0, 3)

        problem: ProblemOutput = result  # type: ignore[assignment]
        problem.level = level  # inject if LLM forgot

        logger.info(
            "problem_generated",
            provider=self.provider_name,
            model=self.model_name,
            prompt_version=self.prompt_version,
            execution_time_s=elapsed_s,
            chapter=chapter_id,
            topic=topic_index,
            level=level,
            difficulty=difficulty,
            context_tag=problem.context_tag,
        )
        return problem


# ── Helpers ───────────────────────────────────────────────────

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


# ── DI factory ────────────────────────────────────────────────

def get_problem_generation_service() -> ProblemGenerationService:
    return ProblemGenerationService()
