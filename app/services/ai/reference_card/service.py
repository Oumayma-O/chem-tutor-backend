"""
Reference Card generation service.

Uses a few-shot LangChain chain with structured output.
The result is meant to be generated ONCE per lesson and persisted in the DB.

Normalization pipeline (same guarantees as problem generation):
  LLM → model_dump → normalize_strings → validate_math_strings → model_validate
Retries up to MAX_ATTEMPTS times if validation fails.
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.core.logging import get_logger
from app.domain.schemas.tutor.problems import ReferenceCardOutput
from app.services.ai.llm import get_llm
from app.services.ai.reference_card.prompts import (
    build_reference_card_system,
    get_few_shots_for_blueprint,
)
from app.utils.markdown_sanitizer import normalize_strings, validate_math_strings

logger = get_logger(__name__)

MAX_ATTEMPTS = 3


async def generate_reference_card(
    lesson_name: str,
    unit_id: str,
    lesson_index: int,
    key_equations: list[str] | None = None,
    blueprint: str = "solver",
) -> ReferenceCardOutput:
    """
    Call the LLM chain to generate a conceptual reference card for a lesson.

    Args:
        lesson_name:   Human-readable lesson name, e.g. "Boyle's Law".
        unit_id:       Unit slug, e.g. "unit-gas-laws".
        lesson_index:  0-based lesson index within the unit.
        key_equations: Optional list of canonical equations stored on the Lesson row.
        blueprint:     Lesson's cognitive blueprint (from Lesson.blueprint in DB).
    """
    system_prompt = build_reference_card_system(blueprint, key_equations)

    llm = get_llm(fast=True, temperature=0.1)
    structured_llm = llm.with_structured_output(ReferenceCardOutput)

    user_prompt = (
        f"Generate a reference card for lesson '{lesson_name}' "
        f"(unit_id='{unit_id}', lesson_index={lesson_index})."
    )

    messages: list = [SystemMessage(content=system_prompt)]
    for ex in get_few_shots_for_blueprint(blueprint):
        messages.append(HumanMessage(content=ex["human"]))
        messages.append(AIMessage(content=ex["assistant"]))
    messages.append(HumanMessage(content=user_prompt))

    last_error: ValueError | None = None

    for attempt in range(MAX_ATTEMPTS):
        raw: ReferenceCardOutput = await structured_llm.ainvoke(messages)
        card_dict = normalize_strings(raw.model_dump(mode="json"))

        ok, msg = validate_math_strings(card_dict)
        if not ok:
            last_error = ValueError(msg)
            logger.warning(
                "reference_card_validation_failed",
                error=msg,
                attempt=attempt + 1,
                max_attempts=MAX_ATTEMPTS,
                lesson=lesson_name,
            )
            continue

        result = ReferenceCardOutput.model_validate(card_dict)
        # Ensure metadata fields match the request (guard against hallucination)
        result.unit_id = unit_id
        result.lesson_index = lesson_index
        result.lesson = lesson_name
        return result

    raise ValueError(
        f"Reference card LaTeX validation failed after {MAX_ATTEMPTS} attempts "
        f"for '{lesson_name}'. Last error: {last_error}"
    ) from last_error
