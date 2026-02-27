"""
All prompt templates in one place.
Keeping prompts here makes them easy to audit, version, and A/B test.

Each service (ProblemGenerationService, StepValidationService, etc.)
imports only the prompts it needs.
"""

# ── Few-Shot Example Bank ──────────────────────────────────────
#
# Keyed by (chapter_id, topic_index) → {difficulty: example_dict}
# Injected into the system prompt to anchor the LLM to the expected
# output style, step structure, and numeric precision.
#
# DEFAULT_FEW_SHOT is used when no topic-specific example matches.

_Step = dict  # {"label", "type", "content", "correctAnswer"?}

FEW_SHOT_EXAMPLES: dict[tuple[str, int], dict[str, dict]] = {
    # ── Chemical Kinetics, Topic 0 — Zero-Order Kinetics ────────
    ("chemical-kinetics", 0): {
        "easy": {
            "title": "Zero-Order Decay: Drug Elimination",
            "statement": (
                "A drug degrades in the bloodstream following zero-order kinetics. "
                "The initial concentration is 0.80 M and the rate constant k = 0.20 M/s. "
                "What is the concentration after 3 seconds?"
            ),
            "steps": [
                {"label": "Step 1 — Equation",   "type": "given", "content": "[A]t = [A]₀ − k·t"},
                {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 0.80 M,  k = 0.20 M/s,  t = 3 s"},
                {"label": "Step 3 — Substitute", "type": "given", "content": "[A]t = 0.80 − (0.20)(3)"},
                {"label": "Step 4 — Calculate",  "type": "given", "content": "[A]t = 0.80 − 0.60 = 0.20"},
                {"label": "Step 5 — Answer",     "type": "given", "content": "[A]t = 0.20 M"},
            ],
        },
        "medium": {
            "title": "Zero-Order Concentration Over Time",
            "statement": (
                "An enzyme-catalyzed reaction proceeds by zero-order kinetics. "
                "Given [A]₀ = 1.25 M and k = 0.035 M/s, calculate the concentration after 12 seconds."
            ),
            "steps": [
                {"label": "Step 1 — Equation",   "type": "given", "content": "[A]t = [A]₀ − k·t"},
                {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 1.25 M,  k = 0.035 M/s,  t = 12 s"},
                {"label": "Step 3 — Substitute", "type": "given", "content": "[A]t = 1.25 − (0.035)(12)"},
                {"label": "Step 4 — Calculate",  "type": "given", "content": "[A]t = 1.25 − 0.42 = 0.83"},
                {"label": "Step 5 — Answer",     "type": "given", "content": "[A]t = 0.83 M"},
            ],
        },
        "hard": {
            "title": "Zero-Order Kinetics with Scientific Notation",
            "statement": (
                "A photochemical decomposition follows zero-order kinetics. "
                "Given [A]₀ = 0.500 M, k = 2.50×10⁻³ M/s, and t = 80 s, find [A]t."
            ),
            "steps": [
                {"label": "Step 1 — Equation",   "type": "given", "content": "[A]t = [A]₀ − k·t"},
                {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 0.500 M,  k = 2.50×10⁻³ M/s,  t = 80 s"},
                {"label": "Step 3 — Substitute", "type": "given", "content": "[A]t = 0.500 − (2.50×10⁻³)(80)"},
                {"label": "Step 4 — Calculate",  "type": "given", "content": "[A]t = 0.500 − 0.200 = 0.300"},
                {"label": "Step 5 — Answer",     "type": "given", "content": "[A]t = 0.300 M"},
            ],
        },
    },
    # ── Chemical Kinetics, Topic 1 — First-Order Kinetics ───────
    ("chemical-kinetics", 1): {
        "easy": {
            "title": "First-Order Radioactive Decay",
            "statement": (
                "A radioactive isotope decays by first-order kinetics with k = 0.10 s⁻¹. "
                "If [A]₀ = 2.00 M, what is [A] after 10 seconds?"
            ),
            "steps": [
                {"label": "Step 1 — Equation",   "type": "given", "content": "ln[A]t = ln[A]₀ − k·t"},
                {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 2.00 M,  k = 0.10 s⁻¹,  t = 10 s"},
                {"label": "Step 3 — Substitute", "type": "given", "content": "ln[A]t = ln(2.00) − (0.10)(10) = 0.693 − 1.00 = −0.307"},
                {"label": "Step 4 — Calculate",  "type": "given", "content": "[A]t = e^(−0.307) = 0.74"},
                {"label": "Step 5 — Answer",     "type": "given", "content": "[A]t = 0.74 M"},
            ],
        },
        "medium": {
            "title": "First-Order Half-Life",
            "statement": (
                "A first-order reaction has k = 0.0231 min⁻¹. "
                "Calculate the concentration after 60 minutes if [A]₀ = 0.500 M."
            ),
            "steps": [
                {"label": "Step 1 — Equation",   "type": "given", "content": "ln[A]t = ln[A]₀ − k·t"},
                {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 0.500 M,  k = 0.0231 min⁻¹,  t = 60 min"},
                {"label": "Step 3 — Substitute", "type": "given", "content": "ln[A]t = ln(0.500) − (0.0231)(60) = −0.693 − 1.386 = −2.079"},
                {"label": "Step 4 — Calculate",  "type": "given", "content": "[A]t = e^(−2.079) = 0.125"},
                {"label": "Step 5 — Answer",     "type": "given", "content": "[A]t = 0.125 M"},
            ],
        },
        "hard": {
            "title": "First-Order Kinetics: Finding Rate Constant",
            "statement": (
                "The concentration of a drug drops from 0.480 M to 0.120 M over 30.0 minutes "
                "following first-order kinetics. Calculate the rate constant k."
            ),
            "steps": [
                {"label": "Step 1 — Equation",   "type": "given", "content": "k = ln([A]₀/[A]t) / t"},
                {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 0.480 M,  [A]t = 0.120 M,  t = 30.0 min"},
                {"label": "Step 3 — Substitute", "type": "given", "content": "k = ln(0.480/0.120) / 30.0 = ln(4.00) / 30.0"},
                {"label": "Step 4 — Calculate",  "type": "given", "content": "k = 1.386 / 30.0 = 0.0462"},
                {"label": "Step 5 — Answer",     "type": "given", "content": "k = 0.0462 min⁻¹"},
            ],
        },
    },
}

# Default examples — always injected even when no topic-specific match.
# These model the 5-step structure and output style the LLM must follow.
DEFAULT_FEW_SHOT_EXAMPLES: dict[str, dict] = {
    "easy": {
        "title": "Simple Rate Calculation",
        "statement": (
            "A substance decomposes following zero-order kinetics. "
            "Starting at [A]₀ = 1.00 M with k = 0.25 M/s, find [A] after 2 seconds."
        ),
        "steps": [
            {"label": "Step 1 — Equation",   "type": "given", "content": "[A]t = [A]₀ − k·t"},
            {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 1.00 M,  k = 0.25 M/s,  t = 2 s"},
            {"label": "Step 3 — Substitute", "type": "given", "content": "[A]t = 1.00 − (0.25)(2)"},
            {"label": "Step 4 — Calculate",  "type": "given", "content": "[A]t = 1.00 − 0.50 = 0.50"},
            {"label": "Step 5 — Answer",     "type": "given", "content": "[A]t = 0.50 M"},
        ],
    },
    "medium": {
        "title": "Intermediate Kinetics Problem",
        "statement": (
            "A reaction follows zero-order kinetics with [A]₀ = 0.840 M and k = 0.028 M/s. "
            "What is [A] after 15 seconds?"
        ),
        "steps": [
            {"label": "Step 1 — Equation",   "type": "given", "content": "[A]t = [A]₀ − k·t"},
            {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 0.840 M,  k = 0.028 M/s,  t = 15 s"},
            {"label": "Step 3 — Substitute", "type": "given", "content": "[A]t = 0.840 − (0.028)(15)"},
            {"label": "Step 4 — Calculate",  "type": "given", "content": "[A]t = 0.840 − 0.420 = 0.420"},
            {"label": "Step 5 — Answer",     "type": "given", "content": "[A]t = 0.420 M"},
        ],
    },
    "hard": {
        "title": "Advanced Kinetics with Sig Figs",
        "statement": (
            "A catalyst-saturated reaction proceeds by zero-order kinetics. "
            "With [A]₀ = 0.750 M, k = 1.50×10⁻³ M/s, t = 200 s — determine [A]t."
        ),
        "steps": [
            {"label": "Step 1 — Equation",   "type": "given", "content": "[A]t = [A]₀ − k·t"},
            {"label": "Step 2 — Knowns",     "type": "given", "content": "[A]₀ = 0.750 M,  k = 1.50×10⁻³ M/s,  t = 200 s"},
            {"label": "Step 3 — Substitute", "type": "given", "content": "[A]t = 0.750 − (1.50×10⁻³)(200)"},
            {"label": "Step 4 — Calculate",  "type": "given", "content": "[A]t = 0.750 − 0.300 = 0.450"},
            {"label": "Step 5 — Answer",     "type": "given", "content": "[A]t = 0.450 M"},
        ],
    },
}


def get_few_shot_block(chapter_id: str, topic_index: int, difficulty: str) -> str:
    """
    Return a formatted few-shot example string to append to the system prompt.

    Lookup order:
      1. Topic-specific example  → FEW_SHOT_EXAMPLES[(chapter_id, topic_index)][difficulty]
      2. Default fallback        → DEFAULT_FEW_SHOT_EXAMPLES[difficulty]
      3. Nothing found           → empty string (no injection)
    """
    topic_bank = FEW_SHOT_EXAMPLES.get((chapter_id, topic_index), {})
    example = topic_bank.get(difficulty) or DEFAULT_FEW_SHOT_EXAMPLES.get(difficulty)
    if not example:
        return ""

    steps_lines = "\n".join(
        f"  {s['label']} ({s['type']}): {s['content']}"
        for s in example["steps"]
    )
    return (
        "\n\n--- FEW-SHOT REFERENCE (follow this structure exactly) ---\n"
        f"Title: {example['title']}\n"
        f"Statement: {example['statement']}\n"
        f"Steps:\n{steps_lines}\n"
        "--- END REFERENCE — generate a NEW problem with DIFFERENT values ---"
    )


# ── Problem Generation ─────────────────────────────────────────

# Bump this string whenever the prompt template changes.
# Stored alongside every generation log for A/B comparison.
PROMPT_VERSION = "v1"

# Per-level step descriptions injected into the unified template.
# These are plain strings (not format strings) — no escaping needed.
_LEVEL_BLOCKS: dict[int, str] = {
    1: """
LEVEL 1 — FULLY WORKED EXAMPLE
All 5 steps must use type="given". The student reads but never answers.
  Step 1 — Equation   : type=given  → write the rate law/formula in "content"
  Step 2 — Knowns     : type=given  → list variables extracted from statement in "content"
  Step 3 — Substitute : type=given  → show full substitution in "content"
  Step 4 — Calculate  : type=given  → show arithmetic in "content"
  Step 5 — Answer     : type=given  → state final answer with units in "content"
Set "correctAnswer" on every step (reference only). Leave "hint" empty for all steps.""",

    2: """
LEVEL 2 — FADED EXAMPLE
Steps 1-2 are type="given" (shown); steps 3-5 are type="interactive" (student fills in).
  Step 1 — Equation   : type=given       → fill "content" with the rate law
  Step 2 — Knowns     : type=given       → fill "content" with extracted variables
  Step 3 — Substitute : type=interactive → set "correctAnswer" (student substitutes values)
  Step 4 — Calculate  : type=interactive → set "correctAnswer" (student computes result)
  Step 5 — Answer     : type=interactive → set "correctAnswer" with correct units
For steps 3-5: write a "hint" that guides thinking WITHOUT revealing the answer or any value.""",

    3: """
LEVEL 3 — FULLY UNRESOLVED
All 5 steps require student input — use the specific types below:
  Step 1 — Equation   : type=drag_drop
    → set "equationParts" as ordered token list, e.g. ["[A]t","=","[A]0","−","k","·","t"]
    → set "correctAnswer" to the full equation string, e.g. "[A]t = [A]0 − k·t"
  Step 2 — Knowns     : type=variable_id
    → set "knownVariables" as [{"variable":"[A]0","value":"0.75","unit":"M"}, ...]
      (student reads statement and drags each variable to match it)
    → set "correctAnswer" as comma-separated pairs, e.g. "[A]0=0.75M,k=0.025M/s,t=8s"
  Step 3 — Substitute : type=interactive → set "correctAnswer" (student substitutes)
  Step 4 — Calculate  : type=interactive → set "correctAnswer" (student computes)
  Step 5 — Answer     : type=interactive → set "correctAnswer" with correct units
Hints must NEVER reveal numeric values. Randomise values so students cannot copy L1/L2 answers.""",
}


def get_level_block(level: int) -> str:
    """Return the step-type description for the given level (1, 2, or 3)."""
    return _LEVEL_BLOCKS.get(level, _LEVEL_BLOCKS[2])


GENERATE_PROBLEM_SYSTEM = """You are an expert chemistry problem generator.

OUTPUT FIELDS:
- "statement": A full narrative paragraph presenting the scenario.
  EXPLICITLY embed ALL given values with their symbol and unit in the text.
  Example: "A sports drink manufacturer tests a preservative that degrades by zero-order
  kinetics. The initial concentration is [A]₀ = 0.80 M and the rate constant is k = 0.20 M/s.
  Find the concentration after t = 3 s."
- "title": Short descriptive title (5-8 words)
{level_block}

RULES (all levels):
- "statement" must contain ALL numeric values naturally embedded in the narrative
- Step 2 Knowns: list ONLY values that appear in the statement as "symbol = value unit"
- Use simple chemistry numbers; final answer computable with basic arithmetic
- Difficulty "{difficulty}": easy=whole numbers, medium=2-3 sig figs, hard=3 sig figs + unit conversions
- context_tag must be set to the interest slug if interests are provided
{focus_areas_block}
{problem_style_block}
{interest_block}
{grade_block}
{rag_block}

Topic: {topic_name}
Chapter: {chapter_id}"""


# ── Step Validation ────────────────────────────────────────────

VALIDATE_ANSWER_SYSTEM = """You are a chemistry answer checker. Determine if the student answer is
mathematically/chemically equivalent to the correct answer.

Consider equivalent:
  - Different notation: 0.2 vs 0.20
  - Multiplication symbols: * vs × vs ·
  - Scientific notation variants: 1.5e-3 vs 1.5*10^-3 vs 1.5×10⁻³
  - Expressions that evaluate to the same number: 0.025*8 vs 0.20

Do NOT consider equivalent:
  - Wrong units (M vs M/s)
  - Wrong numeric value (even by 5%+)

Step: {step_label}
Problem: {problem_context}"""


# ── Hint Generation ────────────────────────────────────────────

GENERATE_HINT_SYSTEM = """You are a chemistry tutor generating a scaffolded hint.

CRITICAL RULES — NEVER:
  - Reveal the answer, any correct value, or intermediate numeric result
  - Say "the answer is…" or "you should get…"
  - Give the actual calculation result

DO:
  - Prompt thinking and guide reasoning
  - Reference relevant concepts, formulas, or units
  - Keep hints brief (2-3 sentences max)

HINT LEVELS:
  1: Gentle conceptual nudge — remind them what concept applies
  2: Specific procedural guidance — point to the exact operation to try
  3: Target the specific misconception directly (no numbers)

Current level: {hint_level}
{misconception_block}
{interest_block}
{grade_block}
{rag_block}"""


# ── Thinking & Error Analysis ──────────────────────────────────

CLASSIFY_ERROR_SYSTEM = """You are an expert chemistry tutor and cognitive scientist.
Analyse student errors to classify them and generate teaching insights.

IMPORTANT:
- ONLY provide chemistry-related educational feedback
- NEVER include correct answers in your response
- Focus on identifying the TYPE of error, not correcting the answer
- Populate thinkingEntries for EVERY step (not just incorrect ones)

Error categories:
  conceptual    — wrong formula, misunderstood principle
  procedural    — right concept, wrong setup or sequence
  computational — arithmetic error, rounding, unit conversion
  representation — graph interpretation, symbolic notation

Severity:
  blocking — fundamental misunderstanding, prevents progress
  slowing  — causes delays, doesn't block
  minor    — small slip

reasoningPattern for thinkingEntries:
  Procedural | Conceptual | Units | Arithmetic | Substitution | Symbolic

Intervention types:
  worked_example | faded_example | full_problem | micro_hint | concept_refresher | arithmetic_drill | unit_drill"""


# ── Exit Ticket ────────────────────────────────────────────────

GENERATE_EXIT_TICKET_SYSTEM = """You are an expert chemistry assessment designer.

Generate exactly {question_count} exit ticket questions.

RULES:
- For QCM (multiple choice): each WRONG option must target a specific misconception
  (provide misconception_tag for each wrong option)
- For structured: provide an equation and a final answer with units
- Use simple numbers (max 3 sig figs)
- Difficulty "{difficulty}": easy=basic recall, medium=application, hard=multi-step

Topic: {topic_name}
Chapter: {chapter_id}"""


# ── Class Insights ─────────────────────────────────────────────

GENERATE_CLASS_INSIGHTS_SYSTEM = """You are an educational data analyst.
Given aggregated class misconception and error data, produce 3-5 actionable,
natural-language insight sentences for the teacher.

RULES:
- Be specific and data-driven (reference percentages and error categories)
- Focus on actionable teaching recommendations
- Keep each insight to 1-2 sentences
- Never mention individual student names"""
