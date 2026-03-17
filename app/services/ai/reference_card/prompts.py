"""
Reference card generation prompts — blueprint-aware.

Blueprint config is imported from app/services/ai/shared/blueprints.py
so step labels and logic stay in sync with problem generation automatically.
"""

from app.services.ai.shared.blueprints import BLUEPRINT_CONFIG
from app.services.ai.reference_card.few_shots import get_few_shots_for_blueprint  # noqa: F401

__all__ = [
    "build_reference_card_system",
    "get_few_shots_for_blueprint",
]

_SYSTEM_TEMPLATE = """\
You are an expert chemistry teacher writing a concise "fiche de cours" (study reference card) \
for a single lesson. This card will be shown to students alongside a practice problem to guide them.

BLUEPRINT for {blueprint} lessons:
- Step Labels (use EXACTLY these, in order): {labels_block}
- Total Steps: {step_count}
- Logic: {blueprint_logic}

FORMATTING & LATEX RULES (strictly follow all of them):
1. Show the GENERAL METHOD only. NO concrete numeric values (e.g. use $m$ instead of $5.0 \\text{{ g}}$).
2. All math, variables, and formulas MUST be wrapped in $...$.
3. Chemical formulas must use $\\mathrm{{}}$: e.g., $\\mathrm{{H_2O}}$.
4. Units must be inside $\\text{{ }}$: e.g., $\\text{{g/mol}}$.
5. Exponents must use braces: $10^{{23}}$, not $10^23$.
6. NEVER use $$...$$ (display math) — use only $...$ (inline math).
7. JSON ESCAPING (critical): your output is parsed as JSON. You MUST double-escape every LaTeX backslash.
   CORRECT: \\\\text{{g/mol}}, \\\\frac{{m}}{{M}}, \\\\mathrm{{H_2O}}, \\\\times, \\\\rightarrow
   WRONG:   \\text{{g/mol}}, \\frac{{m}}{{M}} — a single backslash in JSON eats the command name.

CONTENT RULES:
1. Produce exactly {step_count} steps labelled: {labels_block}.
2. Each "content" field MUST be a SHORT, punchy phrase (max 10 words). Bullet-style logic only.
3. Write the "hint" as a single encouraging sentence telling the student how to begin.
4. Output valid JSON matching the schema.{equations_rule}"""


def build_reference_card_system(
    blueprint: str,
    key_equations: list[str] | None = None,
) -> str:
    """Return a blueprint-specific system prompt for reference card generation."""
    config = BLUEPRINT_CONFIG.get(blueprint, BLUEPRINT_CONFIG["solver"])
    labels_block = " | ".join(config["labels"])
    equations_rule = ""
    if key_equations:
        formatted = " | ".join(key_equations)
        equations_rule = (
            f"\n\nCRITICAL EQUATIONS: You must include these exact equations somewhere "
            f"in your steps: {formatted}"
        )
    return _SYSTEM_TEMPLATE.format(
        blueprint=blueprint,
        labels_block=labels_block,
        step_count=config["step_count"],
        blueprint_logic=config["logic"],
        equations_rule=equations_rule,
    )
