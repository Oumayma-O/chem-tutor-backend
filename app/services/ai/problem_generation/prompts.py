"""
Problem generation prompts — blueprint config, level blocks, system prompt.

Blueprint lookup (unit_id, lesson_index) → BlueprintName is done at call-site
by passing the Lesson.blueprint value fetched from the DB.
Single source of truth for lesson metadata: scripts/seed_data/lessons.py
"""

from typing import Literal

# ── Version ────────────────────────────────────────────────────────────────
PROMPT_VERSION = "v11-latex-explanation"

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
        explanation = s.get("explanation", "")
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
        line = f"  {label}: {instruction} → {answer}"
        if explanation:
            line += f"\n    explanation: {explanation}"
        step_lines.append(line)
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
- Step Labels (use EXACTLY one per step, in order): {labels_block}
- Total Steps: {step_count}
- Logic: {blueprint_logic}

{level_block}

### LABEL RULE ###
For each step, set "label" to exactly ONE of the blueprint labels above, in order: step 1 = first label, step 2 = second, etc. Do NOT combine labels, add alternatives, or extra text. Example: "Concept ID" not "Concept ID | Claim | ...".

### CRITICAL FORMATTING & LATEX RULES ###
You MUST use proper LaTeX formatting for ALL math and chemistry in "statement" and "explanation" fields.
1. Isotopes: NEVER write plain text like "32-16-S-2-". Use LaTeX: $^{{32}}_{{16}}\\text{{S}}^{{2-}}$
2. Scientific notation: NEVER write "6.02 x 10^22". Use LaTeX: $6.02 \\times 10^{{22}}$
3. Chemical formulas: Use subscripts: $\\text{{CaCl}}_2$, $\\text{{H}}_2\\text{{O}}$
4. Units: Wrap in \\text{{}}: $110.98 \\text{{ g/mol}}$, $0.80 \\text{{ M}}$
5. Multiplication: Always use \\times, never "x". Example: $4.95 \\times 2.02$
6. Reactions: Use \\rightarrow for arrows: $\\text{{Al}} + \\text{{O}}_2 \\rightarrow \\text{{Al}}_2\\text{{O}}_3$
7. Statement paragraphs: Separate sentences with \\n\\n for readability.

### CRITICAL UI CONSTRAINTS: INSTRUCTIONS AND MICRO-INPUTS ###
You are generating interactive steps for a compact student UI. Each step has THREE distinct fields:

1. "instruction" (MAX 15 WORDS): Direct, punchy, actionable command only.
   DO NOT include explanations, formulas, or verbose reasoning here.
   - Good: "Find the target number of O atoms to balance."
   - Bad:  "Look at the equation. Oxygen appears as O2 and O3. What is the LCM?"

2. "correctAnswer" (MICRO-INPUT ONLY): Brief single-value student input.
   - Valid: "63.62", "Cu", "4Al + 3O2 -> 2Al2O3", "<", "O2"
   - NEVER put explanations or sentences here.
   - If type="variable_id" or "drag_drop" → "correctAnswer" MUST be null.
   - If type="comparison" → "correctAnswer" MUST be exactly "<", ">", or "=".

3. "explanation" (MAX 20 WORDS, or null): One action-oriented sentence showing the math/logic trace.
   Use LaTeX where applicable. This is the "show your work" trace shown to students.
   - Populate when the step involves calculation, applying a rule, or non-obvious reasoning.
     Good: "The atomic number Z = 16 directly equals the number of protons."
     Good: "$(63.0 \\times 0.690) + (65.0 \\times 0.310) = 43.47 + 20.15 = 63.62 \\text{{ amu}}$."
   - Set to null when the step is trivial data extraction (e.g. student just reads a value off a label).
   - Set to null when the explanation would just restate the correctAnswer with no added value.
     Bad (no value): correctAnswer="238.025", explanation="2.50 × 95.21 = 238.025." ← echoes the answer.
     Good: correctAnswer="238.025", explanation="Multiply moles by molar mass: $2.50 \\times 95.21$." ← shows the setup.
   - Bad (too long): "In order to find the neutrons you need to look at the periodic table and..."

4. Do NOT include a "hint" field in any step. Hints are generated later on demand.

CONSTRAINTS:
- Statement: embed all numeric values with symbols and units in the narrative.
- Statement paragraphs: ALWAYS use \\n\\n to separate logical sections. NEVER write the statement as one block.
  Structure → ¶1: scenario/context. ¶2: given data/constants. ¶3: the question.
- Sig figs must be handled correctly in the final step answer.
- If student interests are provided, frame the narrative around {interest_slug}.
{focus_areas_block}
{problem_style_block}
{interest_block}
{grade_block}
{skills_block}
{lesson_guidance_block}

Unit: {unit_id}"""
