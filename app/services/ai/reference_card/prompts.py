"""
Reference card generation prompts — blueprint-aware.

Blueprint config is imported from app/services/ai/shared/blueprints.py
so step labels and logic stay in sync with problem generation automatically.
Shared LaTeX/JSON escaping rules are imported from app/services/ai/shared/latex_rules.py.
"""

from app.services.ai.shared.blueprints import BLUEPRINT_CONFIG
from app.services.ai.shared.latex_rules import SHARED_LATEX_RULES
from app.services.ai.reference_card.few_shots import get_few_shot_text_block  # noqa: F401

__all__ = [
    "build_reference_card_system",
]

_SYSTEM_TEMPLATE = (
    """\
You are an expert chemistry teacher writing a concise "fiche de cours" (study reference card) \
for a single lesson. This card will be shown to students alongside a practice problem to guide them.

BLUEPRINT for {blueprint} lessons:
- Step Labels (use EXACTLY these, in order): {labels_block}
- Total Steps: {step_count}
- Logic: {blueprint_logic}

"""
    + SHARED_LATEX_RULES
    + """

REFERENCE CARD RULES:
1. Show the GENERAL METHOD only. NO concrete numeric values (e.g. use $m$ not $5.0 \\\\text{{ g}}$).
2. Produce exactly {step_count} steps labelled: {labels_block}.
3. Each "content" field MUST be a SHORT, punchy phrase (max 10 words). Bullet-style logic only.
4. Output valid JSON matching the schema.{equations_rule}
5. MATH IN CONTENT FIELDS: Any formula, variable, or LaTeX expression in a "content" string MUST be wrapped in $...$. NEVER write bare LaTeX outside of dollar signs.
   CORRECT: "Use $\\\\bar{{A}} = \\\\sum(\\\\text{{mass}} \\\\times \\\\text{{abundance}})$"
   WRONG:   "\\\\text{{Avg Atomic Mass}} = \\\\sum (...)" — bare LaTeX without $...$ renders as raw text."""
)


def build_reference_card_system(
    blueprint: str,
    key_equations: list[str] | None = None,
) -> str:
    """Return a blueprint-specific system prompt with embedded few-shot example."""
    config = BLUEPRINT_CONFIG.get(blueprint, BLUEPRINT_CONFIG["solver"])
    labels_block = " | ".join(config["labels"])
    equations_rule = ""
    if key_equations:
        formatted = " | ".join(key_equations)
        equations_rule = (
            f"\n\nCRITICAL EQUATIONS: You must include these exact equations somewhere "
            f"in your steps: {formatted}"
        )
    base = _SYSTEM_TEMPLATE.format(
        blueprint=blueprint,
        labels_block=labels_block,
        step_count=config["step_count"],
        blueprint_logic=config["logic"],
        equations_rule=equations_rule,
    )
    return base + get_few_shot_text_block(blueprint)
