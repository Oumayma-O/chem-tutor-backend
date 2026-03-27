"""
Reference Card generation service.

Few-shot examples are embedded in the system prompt (same pattern as problem
generation) so this service can use generate_structured() — which handles the
OpenAI function_calling method, provider abstraction, and message building.

Normalization pipeline (same guarantees as problem generation):
  LLM → model_dump → normalize_strings → validate_math_strings → model_validate
Retries up to MAX_ATTEMPTS times if validation fails.
"""

from app.core.logging import get_logger
from app.domain.schemas.tutor.problems import ReferenceCardOutput
from app.services.ai.shared.llm import generate_structured
from app.services.ai.reference_card.prompts import build_reference_card_system
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
    Call the LLM to generate a conceptual reference card for a lesson.

    Args:
        lesson_name:   Human-readable lesson name, e.g. "Boyle's Law".
        unit_id:       Unit slug, e.g. "unit-gas-laws".
        lesson_index:  0-based lesson index within the unit.
        key_equations: Optional list of canonical equations stored on the Lesson row.
        blueprint:     Lesson's cognitive blueprint (from Lesson.blueprint in DB).
    """
    system_prompt = build_reference_card_system(blueprint, key_equations)
    user_prompt = (
        f"Generate a reference card for lesson '{lesson_name}' "
        f"(unit_id='{unit_id}', lesson_index={lesson_index})."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

    last_error: ValueError | None = None

    for attempt in range(MAX_ATTEMPTS):
        raw: ReferenceCardOutput = await generate_structured(
            messages, ReferenceCardOutput, temperature=0.4
        )
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
