"""
Problem generation prompts — blueprint config, level blocks, system prompt.

Blueprint lookup (unit_id, lesson_index) → BlueprintName is done at call-site
by passing the Lesson.blueprint value fetched from the DB.
Single source of truth for lesson metadata: scripts/seed_data/lessons.py
"""

from typing import Literal

# ── Version ────────────────────────────────────────────────────────────────
PROMPT_VERSION = "v10-advanced-widgets"

BlueprintName = Literal["solver", "recipe", "architect", "detective", "lawyer"]
Tool = Literal["calculator", "periodic_table"]

# ── 5 Cognitive Blueprints ─────────────────────────────────────────────────
BLUEPRINT_CONFIG: dict[str, dict] = {
    "solver": {
        "step_count": 5,
        "labels": ["Equation", "Knowns", "Substitute", "Calculate", "Answer"],
        "logic": "Input variables -> Formula -> Result.",
    },
    "recipe": {
        "step_count": 5,
        "labels": ["Goal / Setup", "Conversion Factors", "Dimensional Setup", "Calculate", "Answer"],
        "logic": "Series of conversions where the output of A is the input of B.",
    },
    "architect": {
        "step_count": 4,
        "labels": ["Inventory / Rules", "Draft", "Refine", "Final Answer"],
        "logic": "Building a symbolic representation based on rules.",
    },
    "detective": {
        "step_count": 4,
        "labels": ["Data Extraction", "Feature ID", "Apply Concept", "Conclusion"],
        "logic": "Extracting truth from a visual representation or raw data.",
    },
    "lawyer": {
        "step_count": 4,
        "labels": ["Concept ID", "Relation", "Evidence / Claim", "Conclusion"],
        "logic": "Claim -> Evidence -> Reasoning (CER).",
    },
}

DEFAULT_SKILLS_BY_BLUEPRINT: dict[str, list[str]] = {
    "solver": [
        "Select correct equation",
        "Extract known values with units",
        "Substitute values into equation",
        "Compute final answer with sig figs",
    ],
    "recipe": [
        "Identify conversion goal",
        "Select conversion factors",
        "Set up dimensional analysis",
        "Compute final answer with sig figs",
    ],
    "architect": [
        "Identify chemical rules/inventory",
        "Draft initial symbolic representation",
        "Refine structure/coefficients",
        "Finalize symbolic answer",
    ],
    "detective": [
        "Extract data from representation",
        "Identify key feature or pattern",
        "Apply chemical concept to data",
        "Draw scientific conclusion",
    ],
    "lawyer": [
        "Identify governing concept",
        "State chemical relationship",
        "Provide evidence/reasoning",
        "State final conclusion",
    ],
}


def get_step_count_for_prompt(blueprint: str) -> int:
    return int(BLUEPRINT_CONFIG.get(blueprint, BLUEPRINT_CONFIG["solver"])["step_count"])


def collect_skills_from_lesson_objectives(lesson_context: dict | None, blueprint: str) -> list[str]:
    """Use lesson objectives as canonical per-step skills, with blueprint fallback."""
    if lesson_context and (objectives := lesson_context.get("objectives")):
        cleaned = [str(x).strip() for x in objectives if str(x).strip()]
        if cleaned:
            return list(dict.fromkeys(cleaned))
    return DEFAULT_SKILLS_BY_BLUEPRINT.get(blueprint, DEFAULT_SKILLS_BY_BLUEPRINT["solver"])


def build_skills_block(skills: list[str]) -> str:
    if not skills:
        return ""
    return (
        "SKILL LIST (use EXACT values for skillUsed): "
        + "; ".join(skills)
        + '\nFor each step include "skillUsed" and choose one item from this list only.'
    )


def get_few_shot_block(db_example: dict | None) -> str:
    """Return a formatted few-shot block to append to the system prompt."""
    if not db_example:
        return ""
    step_lines = []
    for s in db_example["steps"]:
        label = s.get("label", "Step")
        instruction = s.get("instruction", "")
        if s.get("equationParts"):
            answer = " | ".join(s["equationParts"])
        elif s.get("labeledValues"):
            answer = "; ".join(
                f'{v["variable"]}={v["value"]} {v["unit"]}' for v in s["labeledValues"]
            )
        elif s.get("comparisonParts"):
            answer = f'{s["comparisonParts"][0]} {s.get("correctAnswer", "?")} {s["comparisonParts"][1]}'
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


# ── Level blocks ────────────────────────────────────────────────────────────
def get_level_block(level: int, step_count: int = 5) -> str:
    """Return step-type and widget-selection instructions for the given level."""
    n = max(3, min(6, step_count))
    return f"""
Use exactly {n} steps. For every step, include "skillUsed" exactly matching the SKILL LIST.
Current Mode: LEVEL {level} ({'WORKED' if level == 1 else 'FADED' if level == 2 else 'INDEPENDENT'})

### STEP TYPES & WIDGET SELECTION ###
You MUST choose the `type` for each step based on what the student is doing:

1. type="variable_id"
   - WHEN: A step requires identifying or entering MULTIPLE labeled values
     (e.g. extracting several Knowns, two abundances, multiple masses).
   - Populate "labeledValues" (array of {{variable, value, unit}}). Leave "correctAnswer" null.

2. type="comparison"
   - WHEN: A step asks the student to compare two quantities or properties.
   - Populate "comparisonParts" with EXACTLY 2 strings. Set "correctAnswer" to "<", ">", or "=".

3. type="drag_drop"
   - WHEN: A step requires assembling a full equation or formula (primarily Level 3).
   - Populate "equationParts". Leave "correctAnswer" null.

4. type="given" or type="interactive"
   - WHEN: A standard single-value micro-input step (none of the above apply).
   - Level rules:
     * Level 1: ALL standard steps → "given".
     * Level 2: Step 1 and 2 → "given". Remaining → "interactive".
     * Level 3: ALL standard steps → "interactive".
   - If the step is given or interactive but no special type (drag and drop or comparison or labeledValues) → Must include a brief "correctAnswer" (number, symbol, or short word).
"""


# ── System prompt ──────────────────────────────────────────────────────────
GENERATE_PROBLEM_SYSTEM = """\
You are an expert Chemistry tutor generating a {difficulty} problem.

Generate a {difficulty} problem for {topic_name}.

BLUEPRINT for {blueprint}:
- Step Labels: {labels_block}
- Total Steps: {step_count}
- Logic: {blueprint_logic}

{level_block}

### CRITICAL UI CONSTRAINTS: INSTRUCTIONS, HINTS, AND MICRO-INPUTS ###
You are generating interactive steps for a compact student UI. Strictly separate:

1. "instruction" (MAX 15 WORDS): Direct, punchy, actionable command only.
   DO NOT include explanations, formulas, or verbose reasoning here.
   - Good: "Find the target number of O atoms to balance."
   - Bad:  "Look at the equation. Oxygen appears as O2 and O3. What is the LCM?"


2. "correctAnswer" (MICRO-INPUT ONLY): Brief single-value student input.
   - Valid: "63.62", "Cu", "4Al + 3O2 -> 2Al2O3", "<", "Limiting reactant"
   - NEVER output paragraphs.
   - If type="variable_id" or "drag_drop" → "correctAnswer" MUST be null.
   - If type="comparison" → "correctAnswer" MUST be exactly "<", ">", or "=".

CONSTRAINTS:
- Statement: embed all numeric values with symbols and units in the narrative.
- Sig figs must be handled correctly in the final step answer.
- If student interests are provided, frame the narrative around {interest_slug}.
{focus_areas_block}
{problem_style_block}
{interest_block}
{grade_block}
{skills_block}
{lesson_guidance_block}

Unit: {unit_id}"""
