"""Problem generation prompts — strategy mapping, few-shot bank, level blocks, system prompt."""

# ── Version ────────────────────────────────────────────────────────────────
# Must fit DB prompt_versions.version column (varchar 20)
PROMPT_VERSION = "v3-ped-strategies"

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

# ── Strategy prompt blocks ─────────────────────────────────────────────────
STRATEGY_BLOCKS: dict[str, str] = {
    "quantitative": """
STRATEGY: ALGEBRAIC PLUG-AND-CHUG (Tess Pattern)
1. Unknown: Identify the target variable (e.g., 'Find [A]t').
2. Knowns: Extract values with symbols and units (e.g., 'k = 0.2, t = 5').
3. Equation: Select the correct formula (e.g., '[A]t = [A]o - kt').
4. Substitute: Show the numbers plugged into the formula.
5. Calculate/Answer: Final result with units and significant figures.
""",
    "conceptual": """
STRATEGY: PARTICULATE & TREND REASONING
- Focus: Use Periodic Trends, IMFs, or Atomic Structure to explain 'Why'.
- Steps: (1) State Principle, (2) Compare species, (3) Predict, (4) Justify.
""",
    "analytical": """
STRATEGY: DATA & SPECTRA INTERPRETATION
- Focus: Interpret Mass Spec, PES, or Titration Curves.
- Steps: (1) Data observation, (2) Property correlation, (3) Identity inference.
""",
}


# ── Few-Shot Example Bank ──────────────────────────────────────────────────
# Keyed by (chapter_id, topic_index) → {difficulty: example_dict}
# Injected into the system prompt to anchor the LLM to the expected output
# style, step structure, and numeric precision.

FEW_SHOT_EXAMPLES: dict[tuple[str, int], dict[str, dict]] = {
    # ── AP Unit 5: Chemical Kinetics / Zero-Order (lesson_order 0) ────────────
    ("ap-unit-5", 0): {
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
    # ── AP Unit 5: Chemical Kinetics / First-Order (lesson_order 1) ──────────
    ("ap-unit-5", 1): {
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

    # ── STRATEGY: QUANTITATIVE (Tess Pattern) ───────────────────────────────
    ("unit-mole", 2): {
        "medium": {
            "title": "Two-Step Mole Conversion",
            "statement": "Find the mass in grams of 1.22 moles of sodium (Na). The molar mass of Na is 22.99 g/mol.",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "Mass of Na (g)"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "n = 1.22 mol, Molar Mass = 22.99 g/mol"},
                {"label": "Step 3 — Equation",  "type": "given", "content": "m = n × Molar Mass"},
                {"label": "Step 4 — Substitute", "type": "given", "content": "m = 1.22 mol × 22.99 g/mol"},
                {"label": "Step 5 — Calculate",  "type": "given", "content": "1.22 × 22.99 = 28.0478"},
                {"label": "Step 6 — Answer",     "type": "given", "content": "28.0 g (3 sig figs)"},
            ],
        },
    },
    ("unit-dimensional-analysis", 1): {
        "hard": {
            "title": "Multi-Step Metric Conversion",
            "statement": "How many kg are equal to 45,000 mg? (K: 45,000 mg, U: ? kg)",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "Mass in kg"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "Known = 45,000 mg. Factors: 1g=1000mg, 1kg=1000g"},
                {"label": "Step 3 — Setup",     "type": "given", "content": "45,000 mg × (1 g / 1000 mg) × (1 kg / 1000 g)"},
                {"label": "Step 4 — Calculate",  "type": "given", "content": "45,000 / 1,000,000 = 0.045"},
                {"label": "Step 5 — Answer",     "type": "given", "content": "0.045 kg"},
            ],
        },
    },

    # ── STRATEGY: CONCEPTUAL (Logic Pattern) ───────────────────────────────
    ("unit-nomenclature", 1): {
        "medium": {
            "title": "Writing Formula: Aluminum Sulfite",
            "statement": "Write the chemical formula for Aluminum sulfite. Use ion charges to ensure a neutral compound.",
            "steps": [
                {"label": "Step 1 — Identify Ions", "type": "given", "content": "Aluminum = Al³⁺, Sulfite = SO₃²⁻"},
                {"label": "Step 2 — Compare Charges", "type": "given", "content": "Al has +3 charge; SO₃ has -2 charge."},
                {"label": "Step 3 — Balance Logic",   "type": "given", "content": "To reach net zero: two Al³⁺ (+6) and three SO₃²⁻ (-6)."},
                {"label": "Step 4 — Final Formula",   "type": "given", "content": "Al₂(SO₃)₃"},
            ],
        },
    },

    # ── STRATEGY: ANALYTICAL (Data Pattern) ────────────────────────────────
    ("ap-unit-1", 8): {
        "medium": {
            "title": "Interpreting Mass Spectrometry Peaks",
            "statement": "A mass spectrum of an element shows two peaks: 35 amu (intensity 75%) and 37 amu (intensity 25%). Identify the element.",
            "steps": [
                {"label": "Step 1 — Observe Data", "type": "given", "content": "Two isotopes exist with mass 35 and 37."},
                {"label": "Step 2 — Estimate Mean", "type": "given", "content": "The peak at 35 is 3x more abundant; average will be closer to 35."},
                {"label": "Step 3 — Calculation",   "type": "given", "content": "(35 × 0.75) + (37 × 0.25) = 35.5 amu"},
                {"label": "Step 4 — Identify",      "type": "given", "content": "Atomic mass 35.5 on Periodic Table corresponds to Chlorine."},
                {"label": "Step 5 — Conclusion",    "type": "given", "content": "The element is Chlorine (Cl)."},
            ],
        },
    },

    # ── UNIT 11: STOICHIOMETRY (Quantitative) ──────────────────────────────
    ("unit-stoichiometry", 0): {
        "easy": {
            "title": "Mole-Mole Stoichiometry",
            "statement": "For the reaction 2K + 2H2O → 2KOH + H2, how many moles of H2 are produced from 3.86 moles of K?",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "Moles of H2"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "3.86 mol K, Mole Ratio (1 H2 : 2 K)"},
                {"label": "Step 3 — Equation",  "type": "given", "content": "mol Unknown = mol Known × (ratio)"},
                {"label": "Step 4 — Substitute", "type": "given", "content": "3.86 mol K × (1 mol H2 / 2 mol K)"},
                {"label": "Step 5 — Calculate",  "type": "given", "content": "3.86 / 2 = 1.93"},
                {"label": "Step 6 — Answer",     "type": "given", "content": "1.93 mol H2"},
            ],
        },
    },
    ("unit-stoichiometry", 1): {
        "hard": {
            "title": "Mass-Mass Stoichiometry",
            "statement": "What mass of AgCl will react with 15.0g of Al? Equation: Al + 3AgCl → 3Ag + AlCl3. (MM: Al=26.98, AgCl=143.32)",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "Mass of AgCl (g)"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "15.0g Al, Ratio (3 AgCl : 1 Al)"},
                {"label": "Step 3 — Convert to Moles", "type": "given", "content": "15.0g Al / 26.98 g/mol = 0.556 mol Al"},
                {"label": "Step 4 — Mole Ratio", "type": "given", "content": "0.556 mol Al × (3 AgCl / 1 Al) = 1.668 mol AgCl"},
                {"label": "Step 5 — Convert to Grams", "type": "given", "content": "1.668 mol AgCl × 143.32 g/mol = 239.057"},
                {"label": "Step 6 — Answer",     "type": "given", "content": "239g AgCl"},
            ],
        },
    },

    # ── UNIT 12: SOLUTIONS & ACIDS (Quantitative) ───────────────────────────
    ("unit-solutions", 1): {
        "medium": {
            "title": "Calculating Grams from Molarity",
            "statement": "How many grams of CaBr2 are dissolved in 0.455 L of a 0.39 M CaBr2 solution? (MM of CaBr2 = 199.88 g/mol)",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "Mass of CaBr2 (g)"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "M = 0.39 mol/L, V = 0.455 L, MM = 199.88 g/mol"},
                {"label": "Step 3 — Find Moles", "type": "given", "content": "mol = M × L = 0.39 × 0.455 = 0.17745 mol"},
                {"label": "Step 4 — Find Mass",  "type": "given", "content": "mass = 0.17745 mol × 199.88 g/mol"},
                {"label": "Step 5 — Calculate",  "type": "given", "content": "35.4687..."},
                {"label": "Step 6 — Answer",     "type": "given", "content": "35g CaBr2 (2 sig figs)"},
            ],
        },
    },
    ("unit-solutions", 3): {
        "easy": {
            "title": "Calculating pH from [H+]",
            "statement": "What is the pH of a solution that has a hydrogen ion concentration [H+] = 1.0 × 10⁻⁴ M?",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "pH"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "[H+] = 1.0 × 10⁻⁴ M"},
                {"label": "Step 3 — Equation",  "type": "given", "content": "pH = -log[H+]"},
                {"label": "Step 4 — Substitute", "type": "given", "content": "pH = -log(1.0 × 10⁻⁴)"},
                {"label": "Step 5 — Calculate",  "type": "given", "content": "4.0"},
                {"label": "Step 6 — Answer",     "type": "given", "content": "pH = 4.00"},
            ],
        },
    },

    # ── UNIT 13: THERMOCHEMISTRY (Quantitative) ────────────────────────────
    ("unit-thermochem", 1): {
        "medium": {
            "title": "Specific Heat Calculation",
            "statement": "How many calories of heat are required to raise the temperature of 525g of Aluminum from 13.0°C to 47.8°C? (c = 0.21 cal/g°C)",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "Heat (q) in calories"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "m = 525g, c = 0.21, ΔT = (47.8 - 13.0) = 34.8°C"},
                {"label": "Step 3 — Equation",  "type": "given", "content": "q = m × c × ΔT"},
                {"label": "Step 4 — Substitute", "type": "given", "content": "q = 525 × 0.21 × 34.8"},
                {"label": "Step 5 — Calculate",  "type": "given", "content": "3836.7"},
                {"label": "Step 6 — Answer",     "type": "given", "content": "3,840 cal"},
            ],
        },
    },

    # ── UNIT 15: GAS LAWS (Quantitative) ───────────────────────────────────
    ("unit-gas-laws", 2): {
        "hard": {
            "title": "Combined Gas Law (Unit Conversions)",
            "statement": "A gas occupies 3.78L at 529mmHg and 17.2°C. At what pressure (mmHg) would the volume be 4.54L if the temperature is 34.8°C?",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "Final Pressure (P2)"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "P1=529, V1=3.78, T1=290.2K, V2=4.54, T2=307.8K"},
                {"label": "Step 3 — Equation",  "type": "given", "content": "(P1V1)/T1 = (P2V2)/T2"},
                {"label": "Step 4 — Rearrange",  "type": "given", "content": "P2 = (P1V1T2) / (T1V2)"},
                {"label": "Step 5 — Substitute", "type": "given", "content": "P2 = (529 × 3.78 × 307.8) / (290.2 × 4.54)"},
                {"label": "Step 6 — Answer",     "type": "given", "content": "467 mmHg"},
            ],
        },
    },
    ("unit-gas-laws", 3): {
        "medium": {
            "title": "Ideal Gas Law Calculation",
            "statement": "At what pressure would 0.212 mol of a gas occupy 6.84L at 89°C? (R = 0.0821 L·atm/mol·K)",
            "steps": [
                {"label": "Step 1 — Unknown",   "type": "given", "content": "Pressure (P) in atm"},
                {"label": "Step 2 — Knowns",    "type": "given", "content": "n = 0.212, V = 6.84, T = 362K, R = 0.0821"},
                {"label": "Step 3 — Equation",  "type": "given", "content": "P = (nRT) / V"},
                {"label": "Step 4 — Substitute", "type": "given", "content": "P = (0.212 × 0.0821 × 362) / 6.84"},
                {"label": "Step 5 — Calculate",  "type": "given", "content": "0.921..."},
                {"label": "Step 6 — Answer",     "type": "given", "content": "0.921 atm"},
            ],
        },
    },
}

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


def get_few_shot_block(unit_id: str, topic_index: int, difficulty: str, level: int = 1) -> str:
    """Return a formatted few-shot block to append to the system prompt.

    Lookup order:
      1. DB store (few_shots.py in-memory cache) — used when loaded at startup.
      2. Hardcoded FEW_SHOT_EXAMPLES dict keyed by (unit_id, topic_index).
      3. DEFAULT_FEW_SHOT_EXAMPLES fallback.
    """
    example: dict | None = None

    # 1. DB-backed store (loaded at startup)
    try:
        from app.services.ai.problem_generation.few_shots import get_few_shot, is_loaded
        if is_loaded():
            example = get_few_shot(unit_id, topic_index, difficulty, level)
    except ImportError:
        pass

    # 2. Hardcoded fallback
    if not example:
        topic_bank = FEW_SHOT_EXAMPLES.get((unit_id, topic_index), {})
        example = topic_bank.get(difficulty) or DEFAULT_FEW_SHOT_EXAMPLES.get(difficulty)

    if not example:
        return ""

    steps_lines = "\n".join(
        f"  {s['label']} ({s['type']}): {s.get('instruction') or s.get('content', '')}"
        for s in example["steps"]
    )
    return (
        "\n\n--- FEW-SHOT REFERENCE (follow this structure exactly) ---\n"
        f"Title: {example['title']}\n"
        f"Statement: {example['statement']}\n"
        f"Steps:\n{steps_lines}\n"
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
    """Return step count 3–6 for the system prompt. Quantitative tends to use more steps."""
    if strategy == "quantitative":
        return {"easy": 4, "medium": 5, "hard": 6}.get(difficulty, 5)
    if strategy == "conceptual":
        return {"easy": 3, "medium": 4, "hard": 4}.get(difficulty, 4)
    # analytical
    return {"easy": 4, "medium": 5, "hard": 5}.get(difficulty, 5)


# ── Level blocks (parameterized by step_count) ──────────────────────────────
def get_level_block(level: int, step_count: int = 5) -> str:
    """Return step-type instructions for the given level and step count."""
    n = max(3, min(6, step_count))
    given_range = "1-2" if n >= 2 else "1"
    interactive_start = 3 if n >= 3 else 2
    interactive_range = f"{interactive_start}-{n}" if n >= interactive_start else str(n)
    return f"""
LEVEL {level} LOGIC:
- Level 1: Fully worked. All {n} steps are type="given".
- Level 2: Faded. Steps {given_range} are type="given"; steps {interactive_range} are type="interactive".
- Level 3: Unresolved. Step 1 is type="drag_drop", Step 2 is type="variable_id", steps 3-{n} are type="interactive".

Use exactly {n} steps. Step labels (e.g. Equation, Knowns, Substitute, Calculate, Answer) should match the strategy.
For Level 1: set "correctAnswer" on every step; leave "hint" empty.
For Level 2/3: set "correctAnswer" on interactive steps; hints must NOT reveal numeric values."""


# ── System prompt ──────────────────────────────────────────────────────────
GENERATE_PROBLEM_SYSTEM = """You are an expert Chemistry tutor generating a {difficulty} problem.

PEDAGOGICAL STRATEGY:
{strategy_block}

{level_block}

CONSTRAINTS:
- Use exactly {step_count} steps.
- Statement: embed all numeric values with symbols and units in the narrative.
- Sig Figs: easy=whole numbers, medium/hard=strict sig figs.
- Context: If student interests are provided, frame the narrative around {interest_slug}.
{focus_areas_block}
{problem_style_block}
{interest_block}
{grade_block}
{rag_block}

Topic: {topic_name}
Unit: {unit_id}"""
