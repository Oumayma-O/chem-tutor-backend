"""Problem generation prompts — strategy mapping, level blocks, system prompt."""

from typing import Literal

# ── Version ────────────────────────────────────────────────────────────────
# Must fit DB prompt_versions.version column (varchar 20)
PROMPT_VERSION = "v8-collapsed-logic"

# ── Strategy mapping: Unit ID → pedagogical "brain" ────────────────────────
UNIT_STRATEGIES: dict[str, list[str]] = {
    "conceptual": [
        "unit-intro-chem", "unit-atomic-theory", "unit-electrons",
        "unit-periodic-table", "unit-bonding", "unit-nomenclature",
        "unit-chemical-reactions", "unit-kinetic-theory", "ap-unit-2",
    ],
    "quantitative": [
        "unit-dimensional-analysis", "unit-mole", "unit-stoichiometry",
        "unit-solutions", "unit-gas-laws", "unit-thermochem",
        "ap-unit-4", "ap-unit-5", "ap-unit-6", "ap-unit-7", "ap-unit-9",
    ],
    "analytical": [
        "unit-nuclear-chem", "ap-unit-1", "ap-unit-3", "ap-unit-8",
    ],
}

StrategyName = Literal["quantitative", "conceptual", "analytical"]


STRATEGY_CONFIG: dict[StrategyName, dict] = {
    "quantitative": {
        "step_count": 4,
        "labels": [
            "Knowns",
            "Equation",
            "Substitute",
            "Answer",
        ],
        "logic": "1. Pull numbers from text. 2. Pick formula. 3. Plug in numbers. 4. Calculate and provide value + unit.",
    },
    "conceptual": {
        "step_count": 3,
        "labels": [
            "Governing Principle",
            "Concept Application",
            "Final Justification",
        ],
        "logic": "1. State the law/trend. 2. Apply it to the specific atoms/molecules. 3. Final conclusion.",
    },
    "analytical": {
        "step_count": 3,
        "labels": [
            "Data Observation",
            "Feature Correlation",
            "Scientific Inference",
        ],
        "logic": "1. Identify peak/slope/color. 2. Link data to chemical property. 3. Identify the unknown.",
    },
}


def get_few_shot_block(db_example: dict | None) -> str:
    """Return a formatted few-shot block to append to the system prompt.

    Requires db_example fetched from DB by service.generate().
    Returns empty string when no example is available.
    """
    if not db_example:
        return ""

    step_lines = []
    for s in db_example["steps"]:
        label = s.get("label", "Step")
        instruction = s.get("instruction", "")
        if s.get("equationParts"):
            answer = " | ".join(s["equationParts"])
        elif s.get("knownVariables"):
            answer = "; ".join(
                f'{v["variable"]}={v["value"]} {v["unit"]}' for v in s["knownVariables"]
            )
        else:
            answer = s.get("correctAnswer", "")
        step_lines.append(f"  {label}: {instruction} → {answer}")

    steps_text = "\n".join(step_lines)
    return (
        "\n\n--- FEW-SHOT REFERENCE (follow this structure exactly) ---\n"
        f"Title: {db_example['title']}\n"
        f"Statement: {db_example['statement']}\n"
        f"Steps:\n{steps_text}\n"
        "--- END REFERENCE — generate a NEW problem with DIFFERENT values ---"
    )


# ── Strategy lookup: unit_id → strategy name ─────────────────────────────────
def get_strategy_for_unit(unit_id: str) -> str:
    """Return 'conceptual', 'quantitative', or 'analytical'. Default 'quantitative'."""
    for strategy, unit_ids in UNIT_STRATEGIES.items():
        if unit_id in unit_ids:
            return strategy
    return "quantitative"


def get_step_count_for_prompt(strategy: str, difficulty: str) -> int:
    """Collapsed workflow: 4 steps for quantitative, 3 otherwise."""
    del difficulty
    return int(STRATEGY_CONFIG.get(strategy, STRATEGY_CONFIG["quantitative"])["step_count"])


DEFAULT_SKILLS_BY_STRATEGY: dict[StrategyName, list[str]] = {
    "quantitative": [
        "Identify unknown variable and unit",
        "Extract known values with units",
        "Select correct equation",
        "Substitute values into equation",
        "Compute with sig figs",
        "State final answer with unit",
    ],
    "conceptual": [
        "Identify governing principle",
        "Compare relevant species/properties",
        "Apply trend or concept",
        "Justify claim with chemistry reasoning",
    ],
    "analytical": [
        "Read data representation",
        "Relate pattern to chemistry property",
        "Infer identity/conclusion from evidence",
        "State evidence-based conclusion",
    ],
}



def build_skills_block(skills: list[str]) -> str:
    """Return strict skill list instructions for problem-step output."""
    if not skills:
        return ""
    skills_joined = "; ".join(skills)
    return (
        "SKILL LIST (use EXACT values for skillUsed): "
        f"{skills_joined}\n"
        'For each step include "skillUsed" and choose one item from this list only.'
    )


def collect_skills_from_lesson_objectives(lesson_context: dict | None, strategy: str) -> list[str]:
    """Use lesson objectives as canonical per-step skills, with strategy fallback."""
    if lesson_context and (objectives := lesson_context.get("objectives")):
        cleaned = [str(x).strip() for x in objectives if str(x).strip()]
        if cleaned:
            # Preserve order while deduplicating
            return list(dict.fromkeys(cleaned))
    return DEFAULT_SKILLS_BY_STRATEGY.get(strategy, DEFAULT_SKILLS_BY_STRATEGY["quantitative"])


def build_lesson_guidance_block(lesson_context: dict | None) -> str:
    """Return lesson guidance lines for prompt injection."""
    if not lesson_context:
        return ""
    lines = []
    if equations := lesson_context.get("equations"):
        lines.append(f"KEY EQUATIONS: {'; '.join(equations)}")
    if key_rules := lesson_context.get("key_rules"):
        lines.append(f"KEY RULES: {'; '.join(key_rules)}")
    if misconceptions := lesson_context.get("misconceptions"):
        lines.append(f"COMMON MISCONCEPTIONS TO AVOID: {'; '.join(misconceptions)}")
    return "\n".join(lines)


# ── Level blocks (parameterized by step_count) ──────────────────────────────
def get_level_block(level: int, step_count: int = 5, unit_id: str = "") -> str:
    """Return step-type instructions for the given level and step count."""
    n = max(3, min(6, step_count))
    common_rules = (
        f"Use exactly {n} steps.\n"
        'For every step: include "skillUsed" and it must match one value from SKILL LIST exactly.\n'
        'Do NOT include a "hint" field in any step.'
    )
    if level == 1:
        return f"""
MODE: WORKED (LEVEL 1)
- All {n} steps must be type="given".
- Set "correctAnswer" on every step.
- Do NOT include "equationParts" or "knownVariables" on any step.

{common_rules}"""
    if level == 2:
        return f"""
MODE: FADED (LEVEL 2)
- Step 1 is type="given".
- Steps 2-{n} are type="interactive".
- Set "correctAnswer" on ALL steps (both given and interactive).
- Do NOT include "equationParts" or "knownVariables" on any step.

{common_rules}
"""
    else:
        return f"""
MODE: INDEPENDENT (LEVEL 3)
Use the SAME step template as Level 1/2.

 '- Keep the SAME step labels/template as other levels.\n'
        '- In Level 3 only: if a step label is equation-related, set type="drag_drop".\n'
        '- In Level 3 only: if a step label is knowns/variable-extraction-related, set type="variable_id".\n'
        '- All other steps are type="interactive".'

- Set "correctAnswer" on interactive steps.
- For type="drag_drop": include non-empty "equationParts"; do NOT include "knownVariables".
- For type="variable_id": include non-empty "knownVariables"; do NOT include "equationParts".
- For type="interactive": do NOT include "equationParts" or "knownVariables".

{common_rules}"""


# ── System prompt ──────────────────────────────────────────────────────────
GENERATE_PROBLEM_SYSTEM = """You are an expert Chemistry tutor generating a {difficulty} problem.

Generate a {difficulty} problem for {topic_name}.

BLUEPRINT for {strategy}:
- Step Labels: {labels_block}
- Total Steps: {step_count}
- Logic: {strategy_logic}

{level_block}

CONSTRAINTS:
- Statement: embed all numeric values with symbols and units in the narrative.
- The "Solve & Result" step must include both numerical work and final units (for quantitative strategy).
- Sig figs must be handled in the final step answer.
- Context: If student interests are provided, frame the narrative around {interest_slug}.
{focus_areas_block}
{problem_style_block}
{interest_block}
{grade_block}
{skills_block}
{lesson_guidance_block}

Unit: {unit_id}"""
