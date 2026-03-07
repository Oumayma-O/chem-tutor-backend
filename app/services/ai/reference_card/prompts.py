"""
Reference card generation prompts — strategy-aware, mirrors problem generation templates.

Each strategy maps to a different set of step labels and logic:
  quantitative → Knowns | Equation | Substitute | Answer  (4 steps)
  conceptual   → Governing Principle | Concept Application | Final Justification  (3 steps)
  analytical   → Data Observation | Feature Correlation | Scientific Inference  (3 steps)
"""

from app.services.ai.problem_generation.prompts import (
    STRATEGY_CONFIG,
    get_strategy_for_unit,  # re-exported for callers
)
from app.services.ai.reference_card.few_shots import get_few_shots_for_strategy  # noqa: F401

__all__ = [
    "build_reference_card_system",
    "get_few_shots_for_strategy",
    "get_strategy_for_unit",
]

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

_SYSTEM_TEMPLATE = """\
You are a chemistry teacher writing a concise "fiche de cours" (study reference card) \
for a single chemistry topic.

BLUEPRINT for {strategy} topics:
- Step Labels (use EXACTLY these, in order): {labels_block}
- Total Steps: {step_count}
- Logic: {strategy_logic}

RULES (strictly follow all of them):
1. Show the GENERAL METHOD only — NO numerical examples, NO specific values.
2. Use symbolic variables (e.g. [A]_0, k, t, n, V, DeltaH) but NEVER concrete numbers.
   Exponents: ^ (e.g. [A]^2, k^2).
   Subscripts: _ (e.g. [A]_t, t_{{1/2}}).
   Inverse units: ^-1 (e.g. M^-1 s^-1).
3. Produce exactly {step_count} steps labelled: {labels_block}.
4. Each "content" field is a SHORT phrase (max 8 words). Bullet-style when possible.
5. Write "hint" as one sentence encouraging the student to apply the card to their problem.
6. Output valid JSON matching the schema — nothing else.{equations_rule}"""


def build_reference_card_system(
    strategy: str,
    key_equations: list[str] | None = None,
) -> str:
    """Return a strategy-specific system prompt for reference card generation."""
    config = STRATEGY_CONFIG.get(strategy, STRATEGY_CONFIG["quantitative"])
    labels_block = " | ".join(config["labels"])
    equations_rule = ""
    if key_equations:
        formatted = " | ".join(key_equations)
        equations_rule = (
            f"\n7. Use these exact equation(s) verbatim in the Equation"
            f" or Governing Principle step: {formatted}"
        )
    return _SYSTEM_TEMPLATE.format(
        strategy=strategy,
        labels_block=labels_block,
        step_count=config["step_count"],
        strategy_logic=config["logic"],
        equations_rule=equations_rule,
    )

