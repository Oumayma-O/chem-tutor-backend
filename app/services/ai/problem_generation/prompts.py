"""
Problem generation prompts — level blocks and system prompt.

Blueprint config, skills, and step counts live in app/services/ai/shared/blueprints.py
so that problem generation and reference card generation share one source of truth.
Single source of truth for lesson metadata: scripts/seed_data/lessons.py
"""

# ── Version ────────────────────────────────────────────────────────────────
PROMPT_VERSION = "v17-physical-quantity-registry"

from app.domain.physical_quantity_registry import build_generator_registry_prompt_block  # noqa: E402
from app.services.ai.shared.latex_rules import SHARED_LATEX_RULES  # noqa: E402

# Re-export shared blueprint symbols so callers can keep importing from here
from app.services.ai.shared.blueprints import (  # noqa: E402, F401
    BlueprintName,
    Tool,
    BLUEPRINT_CONFIG,
    DEFAULT_SKILLS_BY_BLUEPRINT,
    get_step_count_for_prompt,
    collect_skills_from_lesson_objectives,
    build_skills_block,
)


def _format_one_example(example: dict, index: int) -> str:
    """Format a single few-shot example dict into a labelled reference block."""
    step_lines = []
    for s in example["steps"]:
        label = s.get("label", "Step")
        instruction = s.get("instruction", "")
        explanation = s.get("explanation", "")
        if s.get("equationParts"):
            answer = " | ".join(s["equationParts"])
        elif s.get("inputFields") or s.get("labeledValues"):
            fields = s.get("inputFields") or s.get("labeledValues")
            answer = "; ".join(
                f'{v.get("label") or v.get("variable")}={v.get("value", "")} {v.get("unit", "")}'
                for v in fields
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
        f"\n\n--- FEW-SHOT EXAMPLE {index} (follow this structure exactly) ---\n"
        f"Title: {example['title']}\n"
        f"Statement: {example['statement']}\n"
        f"Steps:\n{steps_text}\n"
        f"--- END EXAMPLE {index} ---"
    )


def get_few_shot_block(db_examples: list[dict]) -> str:
    """Return formatted few-shot block(s) to append to the system prompt.

    Accepts 0, 1, or 2 examples. With 2 examples the LLM sees varied
    structure and LaTeX style, reducing copy-paste from any single example.
    """
    if not db_examples:
        return ""
    blocks = [_format_one_example(ex, i + 1) for i, ex in enumerate(db_examples)]
    footer = (
        "\n\nDo NOT reuse any example above. "
        "Use this exact context to ensure the student gets a brand new problem "
        "with DIFFERENT values, scenario, and numbers."
    )
    return "".join(blocks) + footer


# ── Level blocks ────────────────────────────────────────────────────────────
def get_level_block(level: int, step_count: int = 5) -> str:
    """Return step-type and widget-selection instructions for the given level."""
    n = max(3, min(6, step_count))
    registry_block = build_generator_registry_prompt_block()
    return f"""
Use exactly {n} steps. For every step, include "skillUsed" exactly matching the SKILL LIST.
Current Mode: LEVEL {level} ({'WORKED' if level == 1 else 'FADED' if level == 2 else 'INDEPENDENT'})

### STEP TYPES & WIDGET SELECTION ###
You MUST choose the `type` for each step based on what the student is doing:

1. type="multi_input"
   - WHEN: A step requires identifying or entering MULTIPLE labeled values
     (e.g. extracting several Knowns, two abundances, multiple masses).
   - ALSO USE for ANY single numeric answer that requires a unit (see UNIT RULE below).
   - Populate "inputFields" (array of {{label, value, unit}}). Leave "correctAnswer" null.
   - "label" MUST be a plain readable label (no $ or LaTeX) — the UI renders it at normal size.
     "value" and "unit" may contain math wrapped in $...$:
     CORRECT: variable="Initial Concentration", value="$0.80$", unit="M"
     CORRECT: variable="Formula", value="$\\mathrm{{C_6H_{{12}}O_6}}$", unit=""
     WRONG:   variable="$[A]_0$" (LaTeX in variable causes oversized KaTeX rendering)
     WRONG:   variable="[A]0", value="\\mathrm{{C_6H_{{12}}O_6}}" (bare LaTeX without $)
   - NEVER collapse multiple inputs into a comma-separated or semicolon-separated "correctAnswer" string
     (e.g. WRONG: correctAnswer="32.00, 2.02"; CORRECT: inputFields with label/value/unit per item).
   - When a step asks for multiple distinct answers (e.g., "rate law AND overall order"), you MUST use type="multi_input".
   - UNIT RULE: Follow the PHYSICAL QUANTITY REGISTRY below. Each `inputFields` row must use a unit whose **dimensions**
     match the quantity (e.g. $E_a$ → molar energy → only J/mol or kJ/mol). Do not use vague lists like "Energy: J, kJ".
{registry_block}

2. type="comparison"
   - WHEN: A step asks the student to MATHEMATICALLY compare two numeric quantities or expressions
     using <, >, or = ONLY (e.g. "compare the KE of two containers", "compare 39.95 amu to 35.45 amu").
   - QUALITATIVE comparisons (stronger/weaker/higher/lower/more soluble/less reactive/faster/slower):
     use type="interactive" instead. The student types the qualitative term as a plain text answer.
     WRONG: type="comparison", comparisonParts=["acid A","acid B"], correctAnswer="stronger"
     CORRECT: type="interactive", instruction="Which acid is stronger?", correctAnswer="acid A"
   - Populate "comparisonParts" with EXACTLY 2 NON-EMPTY descriptive strings that identify what is
     being compared. Both strings MUST contain meaningful content.
     CORRECT: comparisonParts=["KE in Container A", "KE in Container B"], correctAnswer=">"
     CORRECT: comparisonParts=["molar mass of $\\mathrm{{Ar}}$", "molar mass of $\\mathrm{{Cl}}$"], correctAnswer="<"
     WRONG:   comparisonParts=["", ""] or comparisonParts=["value 1", "value 2"] (empty or generic)
   - Set "correctAnswer" to exactly one of: "<", ">", "=".

3. type="drag_drop"
   - WHEN: A step requires assembling a full SYMBOLIC equation/formula OR arranging an ordered
     sequence of symbolic tokens (e.g. electron configuration subshells, orbital order).
     Examples: ["P_1", "V_1", "=", "P_2", "V_2"] | ["$1s^2$", "$2s^2$", "$2p^6$", "$3s^2$", "$3p^3$"]
   - CRITICAL: NEVER use `drag_drop` if ANY token in the equation is a specific number (like 0.56,
     18, 35.0, etc.). It MUST ONLY be used for purely symbolic formulas (like `[A]_t`, `k`, `t`) or
     electron configurations. If the step is labeled "Substitute" or involves plugging numbers into a
     formula, you MUST use type="interactive".
   - Populate "equationParts" with tokens in the CORRECT order. Leave "correctAnswer" null.

4. type="interactive"
   - WHEN: A standard single-value micro-input step (none of the above apply).
   - Use ONLY for: pure text answers ("endothermic"), unitless numbers (pH=7.2, K=0.042),
     or symbolic expressions ("2H₂ + O₂ → 2H₂O").
   - Must include a brief "correctAnswer" (number, symbol, or short word).
   - UNIT RULE: If the answer requires a NUMERIC VALUE + UNIT, do NOT use type="interactive".
     Use type="multi_input" with a single inputField row instead.
     WRONG: type="interactive", correctAnswer="96.0 g"
     CORRECT: type="multi_input", inputFields=[{{label:"Mass", value:"$96.0$", unit:"g"}}]
     WRONG: type="interactive", correctAnswer="3.6e-4 s^-1"
     CORRECT: type="multi_input", inputFields=[{{label:"k", value:"$3.6 \\times 10^{{-4}}$", unit:"s^-1"}}]
   - FORBIDDEN: If a step asks the student to find TWO OR MORE distinct physical quantities
     (e.g., "find neutrons AND electrons", "find protons AND charge"), you MUST use type="multi_input".
     WRONG: type="interactive", correctAnswer="18 neutrons, 18 electrons"
     CORRECT: type="multi_input", inputFields=[{{label:"Neutrons",value:"$18$",...}},{{label:"Electrons",...}}]

### IS_GIVEN (SCAFFOLDING FLAG) — YOU MUST SET THIS ###
Set "is_given" on every step based on the current level:
  Level 1 (WORKED): ALL steps → "is_given": true  (student sees full solution)
  Level 2 (FADED):  Steps 1–2 → "is_given": true; remaining → "is_given": false
  Level 3 (INDEPENDENT): ALL steps → "is_given": false  (student solves independently)
DO NOT omit "is_given". The server uses your value directly.
"""


# ── System prompt ──────────────────────────────────────────────────────────
GENERATE_PROBLEM_SYSTEM = (
    """\
You are an expert Chemistry tutor generating a {difficulty} problem.

Generate a {difficulty} problem for {lesson_name}.

**STEP UNIQUENESS**: Each step must differ in purpose and instruction. For 5-step blueprints, steps 4 and 5 MUST have visually different `correctAnswer` values — step 4 asks for an intermediate result (sub-product or raw unrounded decimal), step 5 requires a final cognitive leap (sig figs + units, unit conversion, or final derivation from step 4). Never let steps 4 and 5 share the same number; if your chosen values produce identical answers, change the problem values.

BLUEPRINT for {blueprint}:
- Step Labels (use EXACTLY one per step, in order): {labels_block}
- Total Steps: {step_count}
- Logic: {blueprint_logic}

{level_block}

### LABEL RULE ###
For each step, set "label" to exactly ONE of the blueprint labels above, in order: step 1 = first label, step 2 = second, etc. Do NOT combine labels, add alternatives, or extra text. Example: "Concept ID" not "Concept ID | Claim | ...".
"""
    + SHARED_LATEX_RULES
    + """

### PROBLEM-SPECIFIC FORMATTING ###
1. Specific variables: $q_{{\\text{{system}}}}$, $q_{{\\text{{surr}}}}$. 
2. Temperatures: $25.0^\\circ\\text{{C}}$. Percentages: $69.17\\%$. Reactions: $\\rightarrow$.
3. MIXED TEXT: Keep plain English OUTSIDE math. Put only symbols/formulas/numbers inside $...$.
   CORRECT: $\\mathrm{{HCl}}$ and $\\mathrm{{NaOH}}$ mixture | water and calorimeter
   WRONG: $\\mathrm{{HCl}} + \\mathrm{{NaOH}} \\text{{ mixture}}$ or $\\text{{water + calorimeter}}$
   If a value is purely an English phrase (e.g. "water", "beaker and room air"), do NOT wrap it in LaTeX.
4. inputFields: "label" = plain string (e.g. "System", "Surroundings"). "value" = mix only when needed: "$\\mathrm{{X}}$ in water" not "$\\mathrm{{X}} \\text{{ in water}}$".
5. Isotopes: $^{{32}}_{{16}}\\mathrm{{S}}^{{2-}}$. Scientific notation: ALWAYS $6.022 \\times 10^{{23}}$ (never "e" or "E" notation in statement, instruction, or explanation).
   Substitute / equation lines: NEVER dump calculator text ($*$ , 8.10e-3, bare ln()). Put the full substituted expression in ONE $...$ using $\\times$, $10^{{-n}}$, $\\ln(...)$, and subscripts ($E_a$ not Ea).
6. NEVER output ANSI escape codes, unicode control characters (e.g. \\u001b), or unescaped tabs.
7. The "correctAnswer" field MUST be plain text or easily typed on a keyboard (e.g. "q_system = -q_surr", "-2299 J"). Do NOT use LaTeX in "correctAnswer".

### CRITICAL UI CONSTRAINTS: INSTRUCTIONS AND MICRO-INPUTS ###
You are generating interactive steps for a compact student UI. Each step has THREE distinct fields:

1. "instruction" (MAX 15 WORDS): Direct, punchy, actionable command only.
   DO NOT include explanations, formulas, or verbose reasoning here.
   - Good: "Find the target number of O atoms to balance."
   - Bad:  "Look at the equation. Oxygen appears as O2 and O3. What is the LCM?"
   If the step expects a calculated number, APPEND the expected precision in parentheses:
   - Good: "Calculate the rate constant. (3 sig figs)"  "Find the mass in grams. (1 decimal place)"

2. "correctAnswer" (MICRO-INPUT ONLY): Brief single-value student input.
   - Valid: "63.62", "Cu", "4Al + 3O2 -> 2Al2O3", "<", "O2"
   - NEVER put explanations or sentences here.
   - If type="multi_input" or "drag_drop" → "correctAnswer" MUST be null.
   - If type="comparison" → "correctAnswer" MUST be exactly "<", ">", or "=".
   - Calculation setup steps (e.g. "Dimensional Setup"): correctAnswer MUST use plain keyboard math
     only — no LaTeX, no fractions, no \\text{{}} inside the answer box.
     CORRECT: "2.50 * 95.21"   WRONG: "$2.50 \\times \\frac{{95.21 \\text{{ g}}}}{{1 \\text{{ mol}}}}$"
   - Quantitative final answers MUST include the unit: "238 g", "63.62 amu", "72.1 g" (not bare "238").

3. "explanation" (MAX 20 WORDS, or null): One action-oriented sentence showing the math/logic trace.
   Use LaTeX where applicable. This is the "show your work" trace shown to students.
   - Populate when the step involves calculation, applying a rule, or non-obvious reasoning.
     Good: "The atomic number Z = 16 directly equals the number of protons."
     Good: "$(63.0 \\times 0.690) + (65.0 \\times 0.310) = 43.47 + 20.15 = 63.62 \\text{{ amu}}$."
   - Set to null when the step is trivial data extraction (e.g. student just reads a value off a label).
   - Set to null when the explanation would just restate the correctAnswer with no added value.
     Bad (no value): correctAnswer="238.025", explanation="2.50 \\times 95.21 = 238.025." ← echoes the answer.
     Good: correctAnswer="238.025", explanation="Multiply moles by molar mass: $2.50 \\times 95.21$." ← shows the setup.
   - Bad (too long): "In order to find the neutrons you need to look at the periodic table and..."

4. Do NOT include a "hint" field in any step. Hints are generated later on demand.

CONSTRAINTS:
- Multi_input units: obey the PHYSICAL QUANTITY REGISTRY in the level instructions (molar energy ≠ bare joules).
- Statement: embed all numeric values with symbols and units in the narrative.
- Statement paragraphs: ALWAYS use \\n\\n to separate logical sections. NEVER write the statement as one block.
  Structure → ¶1: scenario/context. ¶2: given data/constants. ¶3: the question.
- Statement field format: MUST be plain prose with inline $...$ for math. NEVER wrap the entire statement in one $...$  block — \\n\\n inside $...$ breaks KaTeX rendering.
  WRONG: "$A \\text{{ sample of copper...}}\\n\\n\\text{{ What is the mass?}}$"
  CORRECT: "A sample of $^{{63}}\\mathrm{{Cu}}$ has an isotopic mass of $62.93 \\text{{ amu}}$.\\n\\nWhat is the average atomic mass?"
  Rule: English words stay OUTSIDE $...$. Only symbols, numbers, formulas, and units go INSIDE $...$.
- NO IMAGES/GRAPHS: Do NOT reference visual graphs, charts, spectral diagrams, or mass spectra images.
  All data must be provided as text/numbers within the statement. The UI cannot render images.
- Sig figs must be handled correctly in the final step answer.
- If student interests are provided, frame the narrative around {interest_slug}.
{focus_areas_block}
{problem_style_block}
{interest_block}
{grade_block}
{skills_block}
{lesson_guidance_block}

Unit: {unit_id}"""
)


# ── Prompt assembly ──────────────────────────────────────────────────────────

from app.services.ai.shared.lesson_guidance import build_lesson_guidance_block  # noqa: E402


def build_system_prompt(
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
    config = BLUEPRINT_CONFIG.get(resolved_blueprint, BLUEPRINT_CONFIG["solver"])
    labels_block = " | ".join(config["labels"])
    blueprint_logic = config["logic"]
    interest_slug = (interests[0] if interests else "general chemistry").strip() or "general chemistry"
    skill_list = collect_skills_from_lesson_objectives(lesson_context, resolved_blueprint)

    return GENERATE_PROBLEM_SYSTEM.format(
        blueprint=resolved_blueprint,
        labels_block=labels_block,
        blueprint_logic=blueprint_logic,
        level_block=get_level_block(level, step_count),
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
        skills_block=build_skills_block(skill_list),
        lesson_guidance_block=build_lesson_guidance_block(lesson_context),
    ) + get_few_shot_block(db_examples)

