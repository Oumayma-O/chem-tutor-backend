"""Curated few-shot examples for problem generation.

Tuple layout: (unit_id, lesson_index, difficulty, blueprint, problem_dict)
The `blueprint` field maps to Lesson.blueprint from the DB.
Field names in step dicts use camelCase to match LLM output; seed normalizes ``inputFields`` to ``input_fields``.
Multi-answer steps: type ``multi_input`` with ``inputFields`` (each item: ``label``, ``value``, ``unit``).

Rules enforced here:
- All math/chemistry uses LaTeX ($...$) with \\text{} for units.
- Exponents MUST use braces: 10^{22}, NOT 10^22.
- Chemical formulas in correctAnswer MUST use $\\mathrm{}$ formatting.
- Every step has an "explanation" field (<=20 words, one action-oriented sentence).
- "correctAnswer" is always a micro-input (never a sentence).
- No "hint" field (hints are generated on demand).
- "is_given" controls read-only state; set explicitly per step based on level.
- Level 1 (WORKED): all steps is_given=True.
- Level 2 (FADED): first 2 steps is_given=True, rest False.
- Level 3 (INDEPENDENT): all steps is_given=False; steps may be compressed (no separate Knowns step).
- "type" strictly controls the UI widget: "interactive", "multi_input", "drag_drop", "comparison".
"""

FEW_SHOT_DATA: list[tuple[str, int, str, str, dict]] = [

    # ── 1. Architect: balancing Al₂O₃ (Level 1 · Easy) ─────────────────────
    (
        "unit-chemical-reactions",
        1,
        "easy",
        "architect",
        {
            "title": "Balancing the Formation of Aluminum Oxide",
            "statement": (
                "In a general chemistry lab, aluminum metal reacts with oxygen gas to form aluminum oxide.\n\n"
                "Determine the smallest whole-number coefficients to balance: "
                "$\\mathrm{Al} + \\mathrm{O_2} \\rightarrow \\mathrm{Al_2O_3}$."
            ),
            "level": 1,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Inventory / Rules",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Write the unbalanced skeleton equation.",
                    "explanation": "Al is aluminum; $\\mathrm{O_2}$ is diatomic oxygen; product is $\\mathrm{Al_2O_3}$.",
                    "correctAnswer": "$\\mathrm{Al} + \\mathrm{O_2} \\rightarrow \\mathrm{Al_2O_3}$",
                    "skillUsed": "Identify chemical rules/inventory",
                },
                {
                    "step_number": 2,
                    "label": "Draft",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Find the LCM for oxygen atoms on both sides.",
                    "explanation": "LCM of $2$ ($\\mathrm{O_2}$) and $3$ ($\\mathrm{Al_2O_3}$) is $2 \\times 3 = 6$.",
                    "correctAnswer": "6",
                    "skillUsed": "Draft initial symbolic representation",
                },
                {
                    "step_number": 3,
                    "label": "Refine",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Place coefficients to reach 6 oxygen atoms.",
                    "explanation": "Put $3$ in front of $\\mathrm{O_2}$ and $2$ in front of $\\mathrm{Al_2O_3}$.",
                    "correctAnswer": "$\\mathrm{Al} + 3\\mathrm{O_2} \\rightarrow 2\\mathrm{Al_2O_3}$",
                    "skillUsed": "Refine structure/coefficients",
                },
                {
                    "step_number": 4,
                    "label": "Final Answer",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Balance aluminum and write the complete equation.",
                    "explanation": "Two $\\mathrm{Al_2O_3}$ molecules require $4$ Al atoms, so place $4$ in front of Al.",
                    "correctAnswer": "$4\\mathrm{Al} + 3\\mathrm{O_2} \\rightarrow 2\\mathrm{Al_2O_3}$",
                    "skillUsed": "Finalize symbolic answer",
                },
            ],
        },
    ),

    # ── 2. Architect: balancing Al₂O₃ (Level 2 · Medium) ───────────────────
    (
        "unit-chemical-reactions",
        1,
        "medium",
        "architect",
        {
            "title": "Balancing Iron(III) Oxide Formation",
            "statement": (
                "Iron metal reacts with oxygen gas in air to form iron(III) oxide (rust).\n\n"
                "Determine the smallest whole-number coefficients to balance: "
                "$\\mathrm{Fe} + \\mathrm{O_2} \\rightarrow \\mathrm{Fe_2O_3}$."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Inventory / Rules",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Write the unbalanced skeleton equation.",
                    "explanation": "$\\mathrm{Fe}$ is iron; $\\mathrm{O_2}$ is diatomic; product is $\\mathrm{Fe_2O_3}$.",
                    "correctAnswer": "$\\mathrm{Fe} + \\mathrm{O_2} \\rightarrow \\mathrm{Fe_2O_3}$",
                    "skillUsed": "Identify chemical rules/inventory",
                },
                {
                    "step_number": 2,
                    "label": "Draft",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Find the LCM for oxygen atoms on both sides.",
                    "explanation": "LCM of $2$ ($\\mathrm{O_2}$) and $3$ ($\\mathrm{Fe_2O_3}$) is $6$.",
                    "correctAnswer": "6",
                    "skillUsed": "Draft initial symbolic representation",
                },
                {
                    "step_number": 3,
                    "label": "Refine",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Place oxygen and iron oxide coefficients to reach 6 O atoms.",
                    "explanation": "Put $3$ in front of $\\mathrm{O_2}$ and $2$ in front of $\\mathrm{Fe_2O_3}$.",
                    "correctAnswer": "$\\mathrm{Fe} + 3\\mathrm{O_2} \\rightarrow 2\\mathrm{Fe_2O_3}$",
                    "skillUsed": "Refine structure/coefficients",
                },
                {
                    "step_number": 4,
                    "label": "Final Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Balance iron and write the complete equation.",
                    "explanation": "Two $\\mathrm{Fe_2O_3}$ need $4$ Fe atoms, so place $4$ in front of Fe.",
                    "correctAnswer": "$4\\mathrm{Fe} + 3\\mathrm{O_2} \\rightarrow 2\\mathrm{Fe_2O_3}$",
                    "skillUsed": "Finalize symbolic answer",
                },
            ],
        },
    ),

    # ── 3. Detective: isotopic abundance → element identity (Level 2 · Medium) ─
    (
        "unit-atomic-theory",
        2,
        "medium",
        "detective",
        {
            "title": "Identifying an Element from Isotopic Abundance",
            "statement": (
                "A sample contains an element with two naturally occurring isotopes detected by mass spectrometry:\n\n"
                "One has a mass of $63.0 \\text{ amu}$ (abundance $69.0\\%$), "
                "and the other has a mass of $65.0 \\text{ amu}$ (abundance $31.0\\%$). Identify the element."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Data Extraction",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the mass of the most abundant isotope.",
                    "explanation": "The highest percentage ($69.0\\%$) corresponds to the $63.0 \\text{ amu}$ isotope.",
                    "correctAnswer": "63.0",
                    "skillUsed": "Extract data from representation",
                },
                {
                    "step_number": 2,
                    "label": "Feature ID",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Convert the percentage abundances to decimals.",
                    "explanation": "Divide each percentage by $100$: $69.0 \\div 100 = 0.690$ and $31.0 \\div 100 = 0.310$.",
                    "inputFields": [
                        {"label": "Abundance 1", "value": "$0.690$", "unit": ""},
                        {"label": "Abundance 2", "value": "$0.310$", "unit": ""},
                    ],
                    "skillUsed": "Identify key feature or pattern",
                },
                {
                    "step_number": 3,
                    "label": "Apply Concept",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Calculate the weighted average atomic mass.",
                    "explanation": "$(63.0 \\times 0.690) + (65.0 \\times 0.310) = 43.47 + 20.15 = 63.62 \\text{ amu}$.",
                    "correctAnswer": "63.62",
                    "skillUsed": "Apply chemical concept to data",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Identify the element's chemical symbol.",
                    "explanation": "Atomic mass $63.62 \\text{ amu}$ matches Copper on the periodic table.",
                    "correctAnswer": "$\\mathrm{Cu}$",
                    "skillUsed": "Draw scientific conclusion",
                },
            ],
        },
    ),

    # ── 4. Recipe: limiting reactant → theoretical yield (Level 3 · Hard) ───
    (
        "unit-stoichiometry",
        2,
        "hard",
        "recipe",
        {
            "title": "Theoretical Yield from a Limiting Reactant",
            "statement": (
                "$10.0 \\text{ g}$ of $\\mathrm{H_2}$ reacts with $64.0 \\text{ g}$ of $\\mathrm{O_2}$ "
                "according to: $2\\mathrm{H_2} + \\mathrm{O_2} \\rightarrow 2\\mathrm{H_2O}$.\n\n"
                "Calculate the theoretical yield of $\\mathrm{H_2O}$ in grams. "
                "(Molar masses: $\\mathrm{H_2} = 2.02 \\text{ g/mol}$, "
                "$\\mathrm{O_2} = 32.00 \\text{ g/mol}$, $\\mathrm{H_2O} = 18.02 \\text{ g/mol}$)"
            ),
            "level": 3,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Calculate moles of $\\mathrm{H_2}$ available.",
                    "explanation": "$10.0 \\text{ g} \\div 2.02 \\text{ g/mol} = 4.95 \\text{ mol}$.",
                    "correctAnswer": "4.95",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "step_number": 2,
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Calculate moles of $\\mathrm{O_2}$ available.",
                    "explanation": "$64.0 \\text{ g} \\div 32.00 \\text{ g/mol} = 2.00 \\text{ mol}$.",
                    "correctAnswer": "2.00",
                    "skillUsed": "Select conversion factors",
                },
                {
                    "step_number": 3,
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Identify the limiting reactant.",
                    "explanation": "$2.00 \\text{ mol } \\mathrm{O_2}$ needs $4.00 \\text{ mol } \\mathrm{H_2}$; we have $4.95$, so $\\mathrm{O_2}$ limits.",
                    "correctAnswer": "$\\mathrm{O_2}$",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Find moles of $\\mathrm{H_2O}$ produced.",
                    "explanation": "$2.00 \\text{ mol } \\mathrm{O_2} \\times (2 \\text{ mol } \\mathrm{H_2O} / 1 \\text{ mol } \\mathrm{O_2}) = 4.00 \\text{ mol}$.",
                    "correctAnswer": "4.00",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Convert moles of $\\mathrm{H_2O}$ to grams.",
                    "explanation": "$4.00 \\text{ mol} \\times 18.02 \\text{ g/mol} = 72.1 \\text{ g}$ ($3$ sig figs).",
                    "correctAnswer": "72.1",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),

    # ── 5. Solver: zero-order kinetics (Level 2 · Medium) ────────────────────
    (
        "ap-unit-5",
        3,
        "medium",
        "solver",
        {
            "title": "Zero-Order Decay: Drug Elimination",
            "statement": (
                "A drug degrades in the bloodstream following zero-order kinetics. "
                "The initial concentration is $0.80 \\text{ M}$ and the rate constant "
                "$k = 0.020 \\text{ M/s}$.\n\n"
                "What is the concentration after $20 \\text{ s}$?"
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Equation",
                    "type": "drag_drop",
                    "is_given": True,
                    "instruction": "Form the zero-order integrated rate law.",
                    "explanation": "Zero-order decay is linear: concentration decreases by $kt$ from the initial value.",
                    "equationParts": ["[A]_t", "=", "[A]_0", "-", "k", "*", "t"],
                    "skillUsed": "Select correct equation",
                },
                {
                    "step_number": 2,
                    "label": "Knowns",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Extract the given values with units.",
                    "explanation": "List each given quantity with its label, numeric value, and unit.",
                    "inputFields": [
                        {"label": "$[A]_0$", "value": "$0.80$", "unit": "M"},
                        {"label": "$k$", "value": "$0.020$", "unit": "M/s"},
                        {"label": "$t$", "value": "$20$", "unit": "s"},
                    ],
                    "skillUsed": "Extract known values with units",
                },
                {
                    "step_number": 3,
                    "label": "Substitute",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Plug the known values into the rate law.",
                    "explanation": "Replace $[A]_0 = 0.80$, $k = 0.020$, and $t = 20$ into $[A]_t = [A]_0 - kt$.",
                    "correctAnswer": "0.80 - (0.020)(20)",
                    "skillUsed": "Substitute values into equation",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Compute the product $k \\times t$.",
                    "explanation": "$0.020 \\text{ M/s} \\times 20 \\text{ s} = 0.40 \\text{ M}$.",
                    "correctAnswer": "0.40",
                    "skillUsed": "Compute final answer with sig figs",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Calculate the final concentration.",
                    "explanation": "$0.80 \\text{ M} - 0.40 \\text{ M} = 0.40 \\text{ M}$.",
                    "correctAnswer": "$0.40 \\text{ M}$",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),

    # ── 6. Recipe: molar mass → mass conversion (Level 1 · Easy) ────────────
    (
        "unit-stoichiometry",
        1,
        "easy",
        "recipe",
        {
            "title": "Mass of Calcium Chloride from Moles",
            "statement": (
                "A sample contains $0.375 \\text{ mol}$ of $\\mathrm{CaCl_2}$. "
                "Calculate the mass of $\\mathrm{CaCl_2}$ in grams.\n\n"
                "Use atomic masses: $\\mathrm{Ca} = 40.08 \\text{ g/mol}$ and $\\mathrm{Cl} = 35.45 \\text{ g/mol}$."
            ),
            "level": 1,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the starting value and the target unit.",
                    "explanation": "You are converting $0.375 \\text{ mol}$ into grams using the molar mass.",
                    "correctAnswer": "0.375 mol to g",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "step_number": 2,
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Calculate the molar mass of calcium chloride.",
                    "explanation": "$\\mathrm{Ca} + 2(\\mathrm{Cl}) = 40.08 + 2(35.45) = 110.98 \\text{ g/mol}$.",
                    "correctAnswer": "$110.98 \\text{ g/mol}$",
                    "skillUsed": "Select conversion factors",
                },
                {
                    "step_number": 3,
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Set up the conversion to cancel moles.",
                    "explanation": "Multiply starting moles by molar mass so the $\\text{mol}$ units cancel out.",
                    "correctAnswer": "0.375 * 110.98",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Calculate the unrounded sample mass.",
                    "explanation": "$0.375 \\times 110.98 = 41.6175$.",
                    "correctAnswer": "41.6175",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Report the final mass with correct significant figures.",
                    "explanation": "Round to $3$ sig figs because $0.375 \\text{ mol}$ has $3$ sig figs.",
                    "correctAnswer": "$41.6 \\text{ g}$",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),

    # ── 7. Lawyer: periodic trend — atomic radius (Level 2 · Medium) ─────────
    (
        "unit-periodic-table",
        2,
        "medium",
        "lawyer",
        {
            "title": "Comparing Atomic Radius: Na vs Cl",
            "statement": (
                "Compare the atomic radii of Sodium ($\\mathrm{Na}$) and Chlorine ($\\mathrm{Cl}$).\n\n"
                "Which element has a larger atomic radius and why?"
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Concept ID",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the principle governing atomic radius across a period.",
                    "explanation": "Across a period, proton count increases while shielding is constant, raising effective nuclear charge.",
                    "correctAnswer": "Effective Nuclear Charge",
                    "skillUsed": "Identify governing concept",
                },
                {
                    "step_number": 2,
                    "label": "Relation",
                    "type": "comparison",
                    "is_given": True,
                    "instruction": "Compare the effective nuclear charge of Na and Cl.",
                    "explanation": "$\\mathrm{Na}$ has $11$ protons; $\\mathrm{Cl}$ has $17$ — $\\mathrm{Cl}$ exerts a stronger pull.",
                    "comparisonParts": ["Zeff of $\\mathrm{Na}$", "Zeff of $\\mathrm{Cl}$"],
                    "correctAnswer": "<",
                    "skillUsed": "State chemical relationship",
                },
                {
                    "step_number": 3,
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "How does higher Zeff affect the electron cloud?",
                    "explanation": "A stronger nuclear pull draws valence electrons inward, shrinking the atomic radius.",
                    "correctAnswer": "Pulls electrons closer",
                    "skillUsed": "Provide evidence/reasoning",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Which element has the larger atomic radius?",
                    "explanation": "$\\mathrm{Na}$ has weaker nuclear pull, so its electron cloud extends farther.",
                    "correctAnswer": "$\\mathrm{Na}$",
                    "skillUsed": "State final conclusion",
                },
            ],
        },
    ),

    # ── 8. Recipe: Faraday electrolysis (Level 3 · Hard) ─────────────────────
    (
        "ap-unit-9",
        6,
        "hard",
        "recipe",
        {
            "title": "Silver Plating from Electrolysis Time",
            "statement": (
                "A jeweler uses electrolysis to plate a pendant with silver. "
                "A constant current of $2.85 \\text{ A}$ is passed through $\\text{Ag}^+$ solution for $18.0 \\text{ min}$.\n\n"
                "Use $F = 96485 \\text{ C/mol}$, $M_{\\text{Ag}} = 107.87 \\text{ g/mol}$, and $n = 1$ electron per silver atom. "
                "Calculate the mass of silver deposited in grams."
            ),
            "level": 3,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Convert time from minutes to seconds.",
                    "explanation": "$18.0 \\text{ min} \\times 60 = 1080 \\text{ s}$.",
                    "correctAnswer": "1080",
                    "skillUsed": "Apply Faraday's constant (F = 96,485 C/mol)",
                },
                {
                    "step_number": 2,
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Calculate the total charge transferred.",
                    "explanation": "$Q = I \\times t = 2.85 \\times 1080 = 3078 \\text{ C}$.",
                    "correctAnswer": "3078",
                    "skillUsed": "Apply Faraday's constant (F = 96,485 C/mol)",
                },
                {
                    "step_number": 3,
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Set up the mass calculation expression.",
                    "explanation": "Apply $m = \\frac{M \\cdot Q}{n \\cdot F} = \\frac{107.87 \\times 3078}{1 \\times 96485}$.",
                    "correctAnswer": "(107.87 * 3078) / (1 * 96485)",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Compute the unrounded deposited mass.",
                    "explanation": "$\\frac{107.87 \\times 3078}{96485} = 3.441 \\text{ g}$.",
                    "correctAnswer": "3.441",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Report the final mass with correct sig figs.",
                    "explanation": "Both $2.85 \\text{ A}$ and $18.0 \\text{ min}$ have 3 significant figures.",
                    "correctAnswer": "3.44 g",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                },
            ],
        },
    ),

    # ── 9. Solver: Arrhenius two-point Ea (Level 2 · Medium) ─────────────────
    (
        "ap-unit-5",
        6,
        "medium",
        "solver",
        {
            "title": "Determining Activation Energy from Temperature Change",
            "statement": (
                "A chemical reaction has a rate constant of $k_1 = 1.20 \\times 10^{-4}\\,\\text{s}^{-1}$ at "
                "$285\\,\\text{K}$. When the temperature is increased to $305\\,\\text{K}$, "
                "the rate constant becomes $k_2 = 4.80 \\times 10^{-4}\\,\\text{s}^{-1}$.\n\n"
                "Given that $R = 8.314\\,\\text{J}\\,\\text{mol}^{-1}\\,\\text{K}^{-1}$, "
                "calculate the activation energy $E_a$ for this reaction."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Equation",
                    "type": "drag_drop",
                    "is_given": True,
                    "instruction": "Arrange the two-point Arrhenius equation.",
                    "explanation": "Use the logarithmic form to compare rate constants at two temperatures.",
                    "equationParts": [
                        "$\\ln\\left(\\frac{k_2}{k_1}\\right)$",
                        "=",
                        "$\\frac{E_a}{R}$",
                        "$\\left(\\frac{1}{T_1} - \\frac{1}{T_2}\\right)$",
                    ],
                    "skillUsed": "Apply the Arrhenius equation to relate rate constants and temperature",
                },
                {
                    "step_number": 2,
                    "label": "Knowns",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify the given values.",
                    "explanation": "List both rate constants, both temperatures, and the gas constant $R$.",
                    "inputFields": [
                        {"label": "$k_1$", "value": "$1.20 \\times 10^{-4}$", "unit": "$\\text{s}^{-1}$"},
                        {"label": "$k_2$", "value": "$4.80 \\times 10^{-4}$", "unit": "$\\text{s}^{-1}$"},
                        {"label": "$T_1$", "value": "$285$", "unit": "$\\text{K}$"},
                        {"label": "$T_2$", "value": "$305$", "unit": "$\\text{K}$"},
                        {"label": "$R$", "value": "$8.314$", "unit": "$\\text{J}\\,\\text{mol}^{-1}\\,\\text{K}^{-1}$"},
                    ],
                    "skillUsed": "Extract known values from a kinetics problem",
                },
                {
                    "step_number": 3,
                    "label": "Substitute",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Substitute the values into the equation.",
                    "explanation": "$\\ln\\left(\\frac{4.80 \\times 10^{-4}}{1.20 \\times 10^{-4}}\\right) = \\frac{E_a}{8.314}\\left(\\frac{1}{285}-\\frac{1}{305}\\right)$.",
                    "correctAnswer": "ln(4.80e-4 / 1.20e-4) = (Ea / 8.314) * (1/285 - 1/305)",
                    "skillUsed": "Substitute values into the Arrhenius equation",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Solve for $E_a$ in J/mol.",
                    "explanation": "$E_a = \\frac{8.314 \\times \\ln(4.00)}{(1/285 - 1/305)} \\approx 7.20 \\times 10^{4}\\,\\text{J/mol}$.",
                    "correctAnswer": "$7.20 \\times 10^{4}$",
                    "skillUsed": "Calculate activation energy using logarithms and algebra",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Express the activation energy in kJ/mol.",
                    "explanation": "Convert to kilojoules: $E_a = 72.0\\,\\text{kJ/mol}$ (3 significant figures).",
                    "correctAnswer": "$72.0\\,\\text{kJ/mol}$",
                    "skillUsed": "Convert units and report with correct significant figures",
                },
            ],
        },
    ),

    # ── 10. Detective: initial rates (Level 2 · Medium) ──────────────────────
    (
        "ap-unit-5",
        1,
        "medium",
        "detective",
        {
            "title": "Method of Initial Rates for a Two-Reactant Reaction",
            "statement": (
                "A reaction between aqueous reactants $\\text{X}$ and $\\text{Y}$ follows "
                "$\\text{X} + \\text{Y} \\rightarrow \\text{products}$. "
                "A student measures initial rates at the same temperature.\n\n"
                "Experiment 1: $[\\text{X}] = 0.15 \\text{ M}$, $[\\text{Y}] = 0.10 \\text{ M}$, "
                "rate $= 3.0 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 2: $[\\text{X}] = 0.30 \\text{ M}$, $[\\text{Y}] = 0.10 \\text{ M}$, "
                "rate $= 6.0 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 3: $[\\text{X}] = 0.15 \\text{ M}$, $[\\text{Y}] = 0.20 \\text{ M}$, "
                "rate $= 1.2 \\times 10^{-2} \\text{ M/s}$.\n\n"
                "Determine the order in each reactant, the overall order, and write the rate law."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Data Extraction",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Extract the three experiment values.",
                    "explanation": "Record each trial's concentrations and measured initial rate.",
                    "inputFields": [
                        {"label": "Experiment 1", "value": "$[\\text{X}]=0.15$, $[\\text{Y}]=0.10$, rate$=3.0\\times10^{-3}$", "unit": ""},
                        {"label": "Experiment 2", "value": "$[\\text{X}]=0.30$, $[\\text{Y}]=0.10$, rate$=6.0\\times10^{-3}$", "unit": ""},
                        {"label": "Experiment 3", "value": "$[\\text{X}]=0.15$, $[\\text{Y}]=0.20$, rate$=1.2\\times10^{-2}$", "unit": ""},
                    ],
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "step_number": 2,
                    "label": "Feature ID",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the order in $\\text{X}$.",
                    "explanation": "From Exp 1 to 2, $[\\text{X}]$ doubles and rate doubles, so exponent is $1$.",
                    "correctAnswer": "1",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "step_number": 3,
                    "label": "Apply Concept",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Identify the order in $\\text{Y}$.",
                    "explanation": "From Exp 1 to 3, $[\\text{Y}]$ doubles and rate quadruples, so exponent is $2$.",
                    "correctAnswer": "2",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "multi_input",
                    "is_given": False,
                    "instruction": "State the rate law and overall order.",
                    "explanation": "Add exponents: $1+2=3$. Report both the law and total order.",
                    "inputFields": [
                        {"label": "Rate Law", "value": "$k[\\text{X}][\\text{Y}]^{2}$", "unit": ""},
                        {"label": "Overall Order", "value": "3", "unit": ""},
                    ],
                    "skillUsed": "Determine overall reaction order",
                },
            ],
        },
    ),

    # ── 11. Detective: initial rates NO + H₂ (Level 2 · Medium) ─────────────
    (
        "ap-unit-5",
        1,
        "medium",
        "detective",
        {
            "title": "Initial Rates for Nitric Oxide and Hydrogen",
            "statement": (
                "The reaction $2\\text{NO} + 2\\text{H}_2 \\rightarrow \\text{N}_2 + 2\\text{H}_2\\text{O}$ "
                "is studied at constant temperature.\n\n"
                "Experiment 1: $[\\text{NO}] = 0.10 \\text{ M}$, $[\\text{H}_2] = 0.10 \\text{ M}$, "
                "rate $= 1.2 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 2: $[\\text{NO}] = 0.20 \\text{ M}$, $[\\text{H}_2] = 0.10 \\text{ M}$, "
                "rate $= 4.8 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 3: $[\\text{NO}] = 0.20 \\text{ M}$, $[\\text{H}_2] = 0.20 \\text{ M}$, "
                "rate $= 9.6 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Determine the rate law and the overall reaction order."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Data Extraction",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Extract the experiment values.",
                    "explanation": "Record each trial's concentrations and measured initial rate.",
                    "inputFields": [
                        {"label": "Experiment 1", "value": "$[\\text{NO}]=0.10$, $[\\text{H}_2]=0.10$, rate$=1.2\\times10^{-3}$", "unit": ""},
                        {"label": "Experiment 2", "value": "$[\\text{NO}]=0.20$, $[\\text{H}_2]=0.10$, rate$=4.8\\times10^{-3}$", "unit": ""},
                        {"label": "Experiment 3", "value": "$[\\text{NO}]=0.20$, $[\\text{H}_2]=0.20$, rate$=9.6\\times10^{-3}$", "unit": ""},
                    ],
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "step_number": 2,
                    "label": "Feature ID",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the order with respect to NO.",
                    "explanation": "From Exp 1 to 2, doubling $[\\text{NO}]$ quadruples rate, so exponent is $2$.",
                    "correctAnswer": "2",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "step_number": 3,
                    "label": "Apply Concept",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Identify the order with respect to $\\text{H}_2$.",
                    "explanation": "From Exp 2 to 3, doubling $[\\text{H}_2]$ doubles rate, so exponent is $1$.",
                    "correctAnswer": "1",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "multi_input",
                    "is_given": False,
                    "instruction": "State the rate law and overall order.",
                    "explanation": "Add exponents: $2+1=3$. Report the law and the total order.",
                    "inputFields": [
                        {"label": "Rate Law", "value": "$k[\\text{NO}]^{2}[\\text{H}_2]$", "unit": ""},
                        {"label": "Overall Order", "value": "3", "unit": ""},
                    ],
                    "skillUsed": "Determine overall reaction order",
                },
            ],
        },
    ),

    # ── 12. Solver: K from standard cell potential (Level 2 · Medium) ────────
    (
        "ap-unit-9",
        2,
        "medium",
        "solver",
        {
            "title": "Equilibrium Constant from Standard Cell Potential",
            "statement": (
                "A galvanic cell at $25.0^\\circ\\text{C}$ transfers $n = 2$ electrons "
                "with a standard cell potential $E^\\circ = 0.34 \\text{ V}$.\n\n"
                "Use $F = 96485 \\text{ C/mol}$, $R = 8.314 \\text{ J/(mol}\\cdot\\text{K)}$, "
                "and $T = 298 \\text{ K}$.\n\n"
                "Calculate $\\Delta G^\\circ$ and then find the equilibrium constant $K$."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Equation",
                    "type": "drag_drop",
                    "is_given": True,
                    "instruction": "Identify the equation linking $E^\\circ$ and $\\Delta G^\\circ$.",
                    "explanation": "Use $\\Delta G^\\circ = -nFE^\\circ$ and then $\\Delta G^\\circ = -RT\\ln K$.",
                    "equationParts": ["$\\Delta G^\\circ$", "=", "$-$", "$n$", "$F$", "$E^\\circ$"],
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
                {
                    "step_number": 2,
                    "label": "Knowns",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "List the given values.",
                    "explanation": "Identify all known variables before substitution.",
                    "inputFields": [
                        {"label": "Electrons transferred", "value": "$2$", "unit": ""},
                        {"label": "Standard cell potential", "value": "$0.34$", "unit": "V"},
                        {"label": "Faraday constant", "value": "$96485$", "unit": "$\\text{C/mol}$"},
                        {"label": "Gas constant", "value": "$8.314$", "unit": "$\\text{J/(mol}\\cdot\\text{K)}$"},
                        {"label": "Temperature", "value": "$298$", "unit": "K"},
                    ],
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
                {
                    "step_number": 3,
                    "label": "Substitute",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Substitute into the $\\Delta G^\\circ$ formula.",
                    "explanation": "Insert $n=2$, $F=96485$, $E^\\circ=0.34$ into $\\Delta G^\\circ = -nFE^\\circ$.",
                    "correctAnswer": "-2 * 96485 * 0.34",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Calculate $K$ from $\\Delta G^\\circ$.",
                    "explanation": "$\\Delta G^\\circ = -65610 \\text{ J/mol}$, then $\\ln K = 26.47$, so $K = e^{26.47}$.",
                    "correctAnswer": "$3.15 \\times 10^{11}$",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "multi_input",
                    "is_given": False,
                    "instruction": "State both final results.",
                    "explanation": "Positive $E^\\circ$ gives negative $\\Delta G^\\circ$ and large $K > 1$.",
                    "inputFields": [
                        {"label": "$\\Delta G^\\circ$", "value": "$-65.6 \\text{ kJ/mol}$", "unit": ""},
                        {"label": "$K$", "value": "$3.15 \\times 10^{11}$", "unit": ""},
                    ],
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
            ],
        },
    ),

    # ── 13. Solver: E° from K (Level 2 · Medium) ─────────────────────────────
    (
        "ap-unit-9",
        2,
        "medium",
        "solver",
        {
            "title": "Standard Cell Potential from Equilibrium Constant",
            "statement": (
                "A redox reaction at $25^\\circ\\text{C}$ has an equilibrium constant of "
                "$K = 4.5 \\times 10^{-6}$ and transfers $n = 1$ electron.\n\n"
                "Use $R = 8.314 \\text{ J/(mol}\\cdot\\text{K)}$, $T = 298 \\text{ K}$, "
                "and $F = 96485 \\text{ C/mol}$.\n\n"
                "Calculate the standard cell potential $E^\\circ$ and determine if the reaction is spontaneous."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Equation",
                    "type": "drag_drop",
                    "is_given": True,
                    "instruction": "Select the correct relationship linking $K$ and $E^\\circ$.",
                    "explanation": "Combine $\\Delta G^\\circ = -RT\\ln K$ and $\\Delta G^\\circ = -nFE^\\circ$ to get $E^\\circ = \\frac{RT}{nF}\\ln K$.",
                    "equationParts": ["$E^\\circ$", "=", "$\\frac{RT}{nF}$", "$\\ln K$"],
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
                {
                    "step_number": 2,
                    "label": "Knowns",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify all given values.",
                    "explanation": "Unlike typical problems, you are starting from $K$, not $E^\\circ$.",
                    "inputFields": [
                        {"label": "$K$", "value": "$4.5 \\times 10^{-6}$", "unit": ""},
                        {"label": "$n$", "value": "$1$", "unit": ""},
                        {"label": "$R$", "value": "$8.314$", "unit": "$\\text{J/(mol·K)}$"},
                        {"label": "$T$", "value": "$298$", "unit": "K"},
                        {"label": "$F$", "value": "$96485$", "unit": "$\\text{C/mol}$"},
                    ],
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
                {
                    "step_number": 3,
                    "label": "Transform",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Write the expression for $E^\\circ$.",
                    "explanation": "$E^\\circ = \\frac{8.314 \\times 298}{1 \\times 96485} \\times \\ln(4.5 \\times 10^{-6})$.",
                    "correctAnswer": "(8.314 * 298 / (1 * 96485)) * ln(4.5e-6)",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
                {
                    "step_number": 4,
                    "label": "Interpretation",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Predict the sign of $E^\\circ$ before calculating.",
                    "explanation": "Since $K < 1$, $\\ln K$ is negative, so $E^\\circ$ must be negative.",
                    "correctAnswer": "Negative",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "multi_input",
                    "is_given": False,
                    "instruction": "State the final result and spontaneity.",
                    "explanation": "A negative $E^\\circ$ means $\\Delta G^\\circ > 0$, so the reaction is non-spontaneous.",
                    "inputFields": [
                        {"label": "$E^\\circ$", "value": "$-0.32 \\text{ V}$", "unit": ""},
                        {"label": "Spontaneity", "value": "Non-spontaneous", "unit": ""},
                    ],
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                },
            ],
        },
    ),

    # ── 14. Recipe: electrolysis — hydrogen gas (Level 2 · Medium) ───────────
    (
        "ap-unit-9",
        6,
        "medium",
        "recipe",
        {
            "title": "Hydrogen Gas from Water Electrolysis",
            "statement": (
                "A student performs electrolysis of water to produce hydrogen gas at the cathode. "
                "A steady current of $1.60 \\text{ A}$ is applied for $25.0 \\text{ min}$.\n\n"
                "Half-reaction: $2\\text{H}_2\\text{O} + 2\\text{e}^- \\rightarrow \\text{H}_2 + 2\\text{OH}^-$\n\n"
                "Use $F = 96485 \\text{ C/mol}$, $M_{\\text{H}_2} = 2.016 \\text{ g/mol}$, "
                "and $n = 2$ electrons per mole of $\\text{H}_2$. Calculate the mass of hydrogen produced."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Goal / Setup",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify the electrolysis variables.",
                    "explanation": "You are solving for gas mass produced, not metal deposited — same Faraday structure applies.",
                    "inputFields": [
                        {"label": "$I$", "value": "1.60", "unit": "A"},
                        {"label": "$t$", "value": "25.0", "unit": "min"},
                        {"label": "$M$", "value": "2.016", "unit": "g/mol"},
                        {"label": "$n$", "value": "2", "unit": "e⁻"},
                    ],
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                },
                {
                    "step_number": 2,
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Convert time to seconds.",
                    "explanation": "Faraday's Law requires charge in coulombs, so convert minutes to seconds first.",
                    "correctAnswer": "1500 s",
                    "skillUsed": "Apply Faraday's constant (F = 96,485 C/mol)",
                },
                {
                    "step_number": 3,
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Construct the expression for mass of $\\text{H}_2$.",
                    "explanation": "Use $m = \\frac{M \\cdot I \\cdot t}{n \\cdot F}$ with $n=2$.",
                    "correctAnswer": "(2.016 * 1.60 * 1500) / (2 * 96485)",
                    "skillUsed": "Apply Faraday's constant (F = 96,485 C/mol)",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Compute the unrounded mass.",
                    "explanation": "Numerator: $2.016 \\times 1.60 \\times 1500 = 4838.4$. Denominator: $2 \\times 96485 = 192970$.",
                    "correctAnswer": "0.02508",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Report the final mass with correct sig figs.",
                    "explanation": "Round to 3 sig figs: $1.60 \\text{ A}$ and $25.0 \\text{ min}$ each have 3 sig figs.",
                    "correctAnswer": "0.0251 g",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                },
            ],
        },
    ),

    # ── 15. Recipe: moles → grams MgCl₂ (Level 1 · Easy) ────────────────────
    (
        "unit-mole",
        1,
        "easy",
        "recipe",
        {
            "title": "Molar Mass of Magnesium Chloride",
            "statement": (
                "A sample contains $2.50 \\text{ mol}$ of $\\mathrm{MgCl_2}$.\n\n"
                "Using atomic masses $\\mathrm{Mg} = 24.31 \\text{ g/mol}$ and $\\mathrm{Cl} = 35.45 \\text{ g/mol}$, "
                "what mass in grams does the sample have?"
            ),
            "level": 1,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given $2.50 \\text{ mol}$ into grams ($\\text{g}$).",
                    "correctAnswer": "2.50 mol to g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "step_number": 2,
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Find the molar mass of $\\mathrm{MgCl_2}$.",
                    "explanation": "$\\mathrm{Mg} + 2(\\mathrm{Cl}) = 24.31 + 2(35.45) = 95.21 \\text{ g/mol}$.",
                    "correctAnswer": "$95.21 \\text{ g/mol}$",
                    "skillUsed": "Calculate molar mass of elements",
                },
                {
                    "step_number": 3,
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Set up the math to convert moles to grams.",
                    "explanation": "Multiply the given moles by the molar mass so the units cancel.",
                    "correctAnswer": "2.50 * 95.21",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Calculate the unrounded mass.",
                    "explanation": "$2.50 \\times 95.21 = 238.025$.",
                    "correctAnswer": "238.025",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Report the final mass with correct significant figures.",
                    "explanation": "Round to $3$ sig figs because the given $2.50 \\text{ mol}$ has $3$ sig figs.",
                    "correctAnswer": "$238 \\text{ g}$",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
            ],
        },
    ),

    # ── 16. Recipe: mass → particles (Level 2 · Medium) ──────────────────────
    (
        "unit-mole",
        2,
        "medium",
        "recipe",
        {
            "title": "Particles from a Sample of Calcium Chloride",
            "statement": (
                "A student measures a sample of calcium chloride, $\\mathrm{CaCl_2}$.\n\n"
                "The sample has a mass of $11.1 \\text{ g}$. "
                "Use atomic masses $\\mathrm{Ca} = 40.08 \\text{ g/mol}$ and $\\mathrm{Cl} = 35.45 \\text{ g/mol}$. "
                "Avogadro's number is $6.022 \\times 10^{23}$.\n\n"
                "How many formula units of $\\mathrm{CaCl_2}$ are in the sample?"
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given mass ($11.1 \\text{ g}$) into formula units.",
                    "correctAnswer": "11.1 g to formula units",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "step_number": 2,
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Find the molar mass of $\\mathrm{CaCl_2}$.",
                    "explanation": "$\\mathrm{Ca} + 2(\\mathrm{Cl}) = 40.08 + 2(35.45) = 110.98 \\text{ g/mol}$.",
                    "correctAnswer": "110.98",
                    "skillUsed": "Calculate molar mass of compounds",
                },
                {
                    "step_number": 3,
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Set up the two-step conversion.",
                    "explanation": "Divide by molar mass to get moles, then multiply by $6.022 \\times 10^{23}$.",
                    "correctAnswer": "(11.1 / 110.98) * 6.022e23",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Calculate the number of formula units.",
                    "explanation": "$11.1 / 110.98 = 0.1000 \\text{ mol}$; $0.1000 \\times 6.022 \\times 10^{23} = 6.02 \\times 10^{22}$.",
                    "correctAnswer": "$6.02 \\times 10^{22}$",
                    "skillUsed": "Compute final answer with sig figs",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Report the final answer in scientific notation with units.",
                    "explanation": "Round to 3 significant figures because $11.1 \\text{ g}$ has 3 sig figs.",
                    "correctAnswer": "$6.02 \\times 10^{22}$ formula units",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),

    # ── 17. Recipe: particles to mass of O in Al₂O₃ (Level 2 · Medium) ───────
    (
        "unit-mole",
        2,
        "medium",
        "recipe",
        {
            "title": "Particles to Mass of Oxygen in Aluminum Oxide",
            "statement": (
                "A sample contains $1.204 \\times 10^{24}$ formula units of aluminum oxide, $\\mathrm{Al_2O_3}$.\n\n"
                "Using Avogadro's number, $6.022 \\times 10^{23}$ formula units per mole, "
                "calculate the mass of oxygen present in the sample.\n\n"
                "Molar masses: Al = $26.98 \\text{ g/mol}$, O = $16.00 \\text{ g/mol}$."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Goal / Setup",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify what is given and what is required.",
                    "explanation": "You are not finding total mass — only the oxygen portion.",
                    "inputFields": [
                        {"label": "Given", "value": "$1.204 \\times 10^{24}$", "unit": "formula units"},
                        {"label": "Target", "value": "mass of oxygen", "unit": "g"},
                        {"label": "Compound", "value": "$\\mathrm{Al_2O_3}$", "unit": ""},
                    ],
                    "skillUsed": "Convert between grams, moles, and particles in two steps",
                },
                {
                    "step_number": 2,
                    "label": "Conversion Plan",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Determine the conversion pathway.",
                    "explanation": "Particles → moles of compound → moles of oxygen → mass of oxygen.",
                    "correctAnswer": "formula units → mol Al2O3 → mol O → g O",
                    "skillUsed": "Stoichiometric relationships within compounds",
                },
                {
                    "step_number": 3,
                    "label": "Step 1: Particles → Moles",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Convert formula units to moles of $\\mathrm{Al_2O_3}$.",
                    "explanation": "Divide by Avogadro's number: $1.204 \\times 10^{24} / 6.022 \\times 10^{23} = 2.00 \\text{ mol}$.",
                    "correctAnswer": "2.00",
                    "skillUsed": "Convert between particles and moles",
                },
                {
                    "step_number": 4,
                    "label": "Step 2: Moles of Compound → Moles of O",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Find moles of oxygen atoms using the formula.",
                    "explanation": "Each $\\mathrm{Al_2O_3}$ contains 3 oxygen atoms: $2.00 \\times 3 = 6.00 \\text{ mol O}$.",
                    "correctAnswer": "6.00",
                    "skillUsed": "Use subscripts to determine mole ratios",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Convert moles of O to grams and report the final mass.",
                    "explanation": "$6.00 \\text{ mol} \\times 16.00 \\text{ g/mol} = 96.0 \\text{ g}$.",
                    "correctAnswer": "96.0 g",
                    "skillUsed": "Convert between moles and mass",
                },
            ],
        },
    ),

    # ── 18. Lawyer: thermochem — classifying heat flow (Level 1 · Easy) ───────
    (
        "unit-thermochem",
        0,
        "easy",
        "lawyer",
        {
            "title": "Classifying an Exothermic Acid-Base Reaction",
            "statement": (
                "A student mixes hydrochloric acid ($\\mathrm{HCl}$) and sodium hydroxide ($\\mathrm{NaOH}$) "
                "in a coffee-cup calorimeter. "
                "During the reaction, the temperature of the water rises from $22.4^\\circ\\text{C}$ to $28.9^\\circ\\text{C}$.\n\n"
                "Treat the reacting ions as the system. Is the reaction endothermic or exothermic, "
                "and what is the sign of $q_{\\text{system}}$?"
            ),
            "level": 1,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Concept ID",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify the system and surroundings.",
                    "explanation": "The chemical reaction is the system; the surrounding water in the cup is the surroundings.",
                    "inputFields": [
                        {"label": "System", "value": "$\\mathrm{HCl}$ and $\\mathrm{NaOH}$ reacting", "unit": ""},
                        {"label": "Surroundings", "value": "solution water in the cup", "unit": ""},
                    ],
                    "skillUsed": "Define system and surroundings",
                },
                {
                    "step_number": 2,
                    "label": "Relation",
                    "type": "comparison",
                    "is_given": True,
                    "instruction": "Compare final and initial temperatures of the surroundings.",
                    "explanation": "The final temperature ($28.9^\\circ\\text{C}$) is greater than the initial ($22.4^\\circ\\text{C}$).",
                    "comparisonParts": ["Final Temperature", "Initial Temperature"],
                    "correctAnswer": ">",
                    "skillUsed": "Identify direction of heat flow",
                },
                {
                    "step_number": 3,
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Classify the process by heat flow direction.",
                    "explanation": "Because the surroundings warmed up, the system must have released heat.",
                    "correctAnswer": "exothermic",
                    "skillUsed": "Distinguish endothermic from exothermic processes",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "State the sign of $q_{\\text{system}}$.",
                    "explanation": "Exothermic reactions lose heat to the surroundings, so $q_{\\text{system}}$ is negative.",
                    "correctAnswer": "negative",
                    "skillUsed": "Distinguish endothermic from exothermic processes",
                },
            ],
        },
    ),

    # ── 19. Lawyer: thermochem — heat flow with calculation (Level 2 · Medium) ─
    (
        "unit-thermochem",
        0,
        "medium",
        "lawyer",
        {
            "title": "Classifying Heat Flow in a Dissolving Process",
            "statement": (
                "In an AP Chemistry lab, a student dissolves $\\mathrm{NH_4NO_3}$ in water inside "
                "a coffee-cup calorimeter. "
                "The temperature of the solution drops from $25.0^\\circ\\text{C}$ to $19.5^\\circ\\text{C}$.\n\n"
                "Treat the dissolving chemicals as the system and the water as the surroundings. "
                "Identify the system and surroundings, compare their heat flow signs, "
                "and determine if the process is endothermic or exothermic."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Concept ID",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "List the system and surroundings.",
                    "explanation": "The chemicals dissolving are the system; water and calorimeter are surroundings.",
                    "inputFields": [
                        {"label": "System", "value": "$\\mathrm{NH_4NO_3}$ dissolving", "unit": ""},
                        {"label": "Surroundings", "value": "water and calorimeter", "unit": ""},
                    ],
                    "skillUsed": "Define system and surroundings",
                },
                {
                    "step_number": 2,
                    "label": "Relation",
                    "type": "comparison",
                    "is_given": True,
                    "instruction": "Compare $q_{\\text{system}}$ and $-q_{\\text{surr}}$.",
                    "explanation": "Heat lost by surroundings equals heat gained by system; signs are opposite but magnitudes equal.",
                    "comparisonParts": ["$q_{\\text{system}}$", "$-q_{\\text{surr}}$"],
                    "correctAnswer": "=",
                    "skillUsed": "Apply conservation of energy",
                },
                {
                    "step_number": 3,
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Determine the sign of $q_{\\text{system}}$.",
                    "explanation": "Because the surroundings cooled, heat moved into the system, making $q_{\\text{system}}$ positive.",
                    "correctAnswer": "positive",
                    "skillUsed": "Identify direction of heat flow",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Classify the dissolving process.",
                    "explanation": "Processes that absorb heat (positive $q$) are endothermic.",
                    "correctAnswer": "endothermic",
                    "skillUsed": "Distinguish endothermic from exothermic processes",
                },
            ],
        },
    ),

    # ── 20. Lawyer: periodic trend (Level 1 · Easy) ──────────────────���────────
    (
        "unit-periodic-table",
        2,
        "easy",
        "lawyer",
        {
            "title": "Atomic Radius Trend Across Period 3",
            "statement": (
                "Compare the atomic radii of Sodium ($\\mathrm{Na}$) and Chlorine ($\\mathrm{Cl}$).\n\n"
                "Which element has a larger atomic radius and why?"
            ),
            "level": 1,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Concept ID",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the principle governing atomic radius across a period.",
                    "explanation": "Across a period, proton count increases while shielding is constant, raising effective nuclear charge.",
                    "correctAnswer": "Effective Nuclear Charge",
                    "skillUsed": "Identify governing concept",
                },
                {
                    "step_number": 2,
                    "label": "Relation",
                    "type": "comparison",
                    "is_given": True,
                    "instruction": "Compare the effective nuclear charge of Na and Cl.",
                    "explanation": "$\\mathrm{Na}$ has $11$ protons; $\\mathrm{Cl}$ has $17$ — $\\mathrm{Cl}$ exerts a stronger pull.",
                    "comparisonParts": ["Zeff of $\\mathrm{Na}$", "Zeff of $\\mathrm{Cl}$"],
                    "correctAnswer": "<",
                    "skillUsed": "State chemical relationship",
                },
                {
                    "step_number": 3,
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "How does higher Zeff affect the electron cloud?",
                    "explanation": "A stronger nuclear pull draws valence electrons inward, shrinking the atomic radius.",
                    "correctAnswer": "Pulls electrons closer",
                    "skillUsed": "Provide evidence/reasoning",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Which element has the larger atomic radius?",
                    "explanation": "$\\mathrm{Na}$ has weaker nuclear pull, so its electron cloud extends farther.",
                    "correctAnswer": "$\\mathrm{Na}$",
                    "skillUsed": "State final conclusion",
                },
            ],
        },
    ),

    # ── 21. Lawyer: lab safety — PPE (Level 1 · Easy) ────────────────────────
    (
        "unit-intro-chem",
        0,
        "easy",
        "lawyer",
        {
            "title": "Proper Use of Personal Protective Equipment",
            "statement": (
                "During a lab, a student is pouring concentrated sodium hydroxide, $\\mathrm{NaOH}$, "
                "into a graduated cylinder. Because their goggles are fogging up, "
                "the student pushes them up to rest on their forehead.\n\n"
                "The $\\mathrm{NaOH}$ bottle shows a corrosive hazard symbol. "
                "Identify the hazard and the broken rule, explain why the behavior is dangerous, "
                "and state the correct action."
            ),
            "level": 1,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Concept ID",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify the primary hazard and the broken rule.",
                    "explanation": "Extract the chemical danger and the unsafe behavior from the scenario.",
                    "inputFields": [
                        {"label": "Hazard", "value": "corrosive base", "unit": ""},
                        {"label": "Broken Rule", "value": "goggles on forehead", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "step_number": 2,
                    "label": "Relation",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "State the safety rule being violated.",
                    "explanation": "Safety equipment must be worn correctly at all times to provide actual protection.",
                    "correctAnswer": "always wear safety goggles over the eyes",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "step_number": 3,
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "State the risk of this unsafe behavior.",
                    "explanation": "A splash from a corrosive base can cause permanent eye damage if unprotected.",
                    "correctAnswer": "chemical splash to the eyes",
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Give the safest immediate action.",
                    "explanation": "The student must secure their protective equipment before continuing.",
                    "correctAnswer": "stop pouring and put goggles over eyes",
                    "skillUsed": "Identify common lab safety rules",
                },
            ],
        },
    ),

    # ── 22. Lawyer: lab safety — chemical waste (Level 2 · Medium) ───────────
    (
        "unit-intro-chem",
        0,
        "medium",
        "lawyer",
        {
            "title": "Safe Chemical Disposal Procedures",
            "statement": (
                "A student completes a precipitation lab involving lead(II) nitrate, $\\mathrm{Pb(NO_3)_2}$. "
                "To clean up quickly, the student prepares to pour the remaining solution down the sink.\n\n"
                "The lab instructions state that heavy metals are environmental hazards. "
                "Identify the hazard and broken rule, state the correct disposal method, "
                "and conclude the immediate safe action."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Concept ID",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify the hazard and the broken rule.",
                    "explanation": "Extract the specific chemical danger and the unsafe action from the scenario.",
                    "inputFields": [
                        {"label": "Hazard", "value": "toxic heavy metals", "unit": ""},
                        {"label": "Broken Rule", "value": "pouring chemicals down the sink", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "step_number": 2,
                    "label": "Relation",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "State the safety rule regarding chemical waste.",
                    "explanation": "Chemicals cannot be discarded in standard drains unless explicitly permitted.",
                    "correctAnswer": "dispose of chemicals according to lab instructions",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "step_number": 3,
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Where should this specific waste go?",
                    "explanation": "Heavy metals require a specialized, marked hazardous waste container.",
                    "correctAnswer": "designated hazardous waste container",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "What should the student do right now?",
                    "explanation": "If unsure of the disposal location, the student must halt and consult the instructor.",
                    "correctAnswer": "stop and ask the teacher",
                    "skillUsed": "Identify common lab safety rules",
                },
            ],
        },
    ),

    # ── 23. Lawyer: lab safety — food contamination (Level 3 · Hard) ─────────
    (
        "unit-intro-chem",
        0,
        "hard",
        "lawyer",
        {
            "title": "Preventing Cross-Contamination",
            "statement": (
                "During a crystal-growing experiment with copper(II) sulfate, $\\mathrm{CuSO_4}$, "
                "a student becomes thirsty. They place a water bottle on the lab bench next to their "
                "chemical powders and take a drink.\n\n"
                "Copper(II) sulfate is harmful if swallowed. "
                "Identify the hazard and broken rule, explain the unseen risk, "
                "and state the safest immediate action."
            ),
            "level": 3,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Concept ID",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Name the primary hazard from the scenario.",
                    "explanation": "$\\mathrm{CuSO_4}$ is harmful if swallowed — the hazard is ingestion of a toxic compound.",
                    "correctAnswer": "harmful if swallowed",
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "step_number": 2,
                    "label": "Relation",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "State the lab rule being violated.",
                    "explanation": "Labs strictly prohibit eating or drinking to prevent accidental poisoning.",
                    "correctAnswer": "never eat or drink in the laboratory",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "step_number": 3,
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "State the hidden risk of having the bottle on the bench.",
                    "explanation": "Chemical dust or splashes can easily contaminate open food or drink containers nearby.",
                    "correctAnswer": "chemical contamination of the bottle",
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "step_number": 4,
                    "label": "Conclusion",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Give the safest immediate action.",
                    "explanation": "The food or drink item must be removed from the hazardous environment immediately.",
                    "correctAnswer": "move the bottle outside the lab and wash hands",
                    "skillUsed": "Identify common lab safety rules",
                },
            ],
        },
    ),

    # ── 24. Architect: electron configuration of P (Level 2 · Medium) ────────
    (
        "unit-electrons",
        2,
        "medium",
        "architect",
        {
            "title": "Electron Configuration of Phosphorus",
            "statement": (
                "A neutral phosphorus ($\\mathrm{P}$) atom has an atomic number of $15$.\n\n"
                "Determine the occupied subshells, assemble the full electron configuration, "
                "and apply Hund's rule to the valence electrons."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Inventory / Rules",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Distribute the 15 electrons into the correct subshells.",
                    "explanation": "Following Aufbau: $1s$, $2s$, $2p$, $3s$ fill completely; 3 remain for $3p$.",
                    "inputFields": [
                        {"label": "1s", "value": "2", "unit": "$e^-$"},
                        {"label": "2s", "value": "2", "unit": "$e^-$"},
                        {"label": "2p", "value": "6", "unit": "$e^-$"},
                        {"label": "3s", "value": "2", "unit": "$e^-$"},
                        {"label": "3p", "value": "3", "unit": "$e^-$"},
                    ],
                    "skillUsed": "Write basic electron configurations",
                },
                {
                    "step_number": 2,
                    "label": "Draft",
                    "type": "drag_drop",
                    "is_given": True,
                    "instruction": "Arrange the subshells in correct Aufbau order.",
                    "explanation": "Fill lowest to highest energy: $1s \\rightarrow 2s \\rightarrow 2p \\rightarrow 3s \\rightarrow 3p$.",
                    "equationParts": ["$1s^2$", "$2s^2$", "$2p^6$", "$3s^2$", "$3p^3$"],
                    "skillUsed": "Write full electron configurations",
                },
                {
                    "step_number": 3,
                    "label": "Refine",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "How many unpaired electrons are in the 3p subshell?",
                    "explanation": "By Hund's rule, three $3p$ electrons each occupy a separate orbital singly.",
                    "correctAnswer": "3",
                    "skillUsed": "Draw orbital notation diagrams",
                },
                {
                    "step_number": 4,
                    "label": "Final Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "State the complete electron configuration.",
                    "explanation": "Combine the ordered subshells into a single notation string.",
                    "correctAnswer": "1s2 2s2 2p6 3s2 3p3",
                    "skillUsed": "Write full electron configurations",
                },
            ],
        },
    ),

    # ── 25. Architect: noble gas config for Se (Level 1 · Easy) ─────────────
    (
        "unit-electrons",
        3,
        "easy",
        "architect",
        {
            "title": "Noble Gas Configuration and Valence Electrons for Selenium",
            "statement": (
                "Selenium, $\\mathrm{Se}$, has atomic number $34$. "
                "The preceding noble gas is argon, $\\mathrm{Ar}$, with atomic number $18$. "
                "After $[\\mathrm{Ar}]$, the remaining electrons fill as $4s^{2}\\,3d^{10}\\,4p^{4}$.\n\n"
                "Write the noble gas abbreviated electron configuration for selenium "
                "and determine how many valence electrons selenium has."
            ),
            "level": 1,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Inventory / Rules",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify the core and outer subshells.",
                    "explanation": "Use the preceding noble gas as the core, then list filled subshells after it.",
                    "inputFields": [
                        {"label": "Noble gas core", "value": "$[\\mathrm{Ar}]$", "unit": ""},
                        {"label": "Outer subshells after core", "value": "$4s^{2}\\,3d^{10}\\,4p^{4}$", "unit": ""},
                    ],
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                },
                {
                    "step_number": 2,
                    "label": "Draft",
                    "type": "drag_drop",
                    "is_given": True,
                    "instruction": "Assemble the abbreviated configuration.",
                    "explanation": "Place the noble gas core first, then filled outer subshells in Aufbau order.",
                    "equationParts": ["$[\\mathrm{Ar}]$", "$4s^{2}$", "$3d^{10}$", "$4p^{4}$"],
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                },
                {
                    "step_number": 3,
                    "label": "Refine",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Count the valence electrons.",
                    "explanation": "Highest principal level $n=4$: $4s^{2}$ and $4p^{4}$ contribute $2+4=6$.",
                    "correctAnswer": "6",
                    "skillUsed": "Identify valence electrons from configurations",
                },
                {
                    "step_number": 4,
                    "label": "Final Answer",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "State both final results.",
                    "explanation": "Combine the abbreviated configuration and the valence electron count.",
                    "inputFields": [
                        {"label": "Abbreviated configuration", "value": "[Ar] 4s2 3d10 4p4", "unit": ""},
                        {"label": "Valence electrons", "value": "6", "unit": ""},
                    ],
                    "skillUsed": "Identify valence electrons from configurations",
                },
            ],
        },
    ),

    # ── 26. Architect: noble gas config for Ca (Level 2 · Medium) ────────────
    (
        "unit-electrons",
        3,
        "medium",
        "architect",
        {
            "title": "Noble Gas Configuration for Calcium",
            "statement": (
                "Calcium, $\\mathrm{Ca}$, has atomic number $20$. "
                "The previous noble gas is argon, $\\mathrm{Ar}$, with $18$ electrons.\n\n"
                "Write the noble gas abbreviated electron configuration for calcium "
                "and determine its number of valence electrons."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Inventory / Rules",
                    "type": "interactive",
                    "is_given": True,
                    "instruction": "Identify the core noble gas and remaining electrons.",
                    "explanation": "Subtract core electrons: $20 - 18 = 2$ electrons beyond $\\mathrm{Ar}$.",
                    "correctAnswer": "Core: [Ar], Remaining: 2",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                },
                {
                    "step_number": 2,
                    "label": "Draft",
                    "type": "drag_drop",
                    "is_given": True,
                    "instruction": "Assemble the subshell filling after the core.",
                    "explanation": "After $[\\mathrm{Ar}]$, the next $2$ electrons fill the $4s$ subshell.",
                    "equationParts": ["$[\\mathrm{Ar}]$", "$4s^2$"],
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                },
                {
                    "step_number": 3,
                    "label": "Refine",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Enter the abbreviated electron configuration.",
                    "explanation": "Combine the noble gas core with the filled outer subshells.",
                    "correctAnswer": "[Ar] 4s2",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                },
                {
                    "step_number": 4,
                    "label": "Final Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "State the number of valence electrons.",
                    "explanation": "Highest principal level is $n=4$: $4s^2$ contributes $2$ valence electrons.",
                    "correctAnswer": "2",
                    "skillUsed": "Identify valence electrons from configurations",
                },
            ],
        },
    ),

    # ── 27. Solver: Arrhenius — variant numbers (Level 2 · Medium) ───────────
    (
        "ap-unit-5",
        6,
        "medium",
        "solver",
        {
            "title": "Activation Energy from Two Rate Constants",
            "statement": (
                "A student measures the rate constant of a decomposition reaction at two temperatures.\n\n"
                "At $298\\,\\text{K}$: $k_1 = 2.50 \\times 10^{-3}\\,\\text{s}^{-1}$. "
                "At $315\\,\\text{K}$: $k_2 = 8.20 \\times 10^{-3}\\,\\text{s}^{-1}$.\n\n"
                "Given $R = 8.314\\,\\text{J}\\,\\text{mol}^{-1}\\,\\text{K}^{-1}$, "
                "calculate the activation energy $E_a$."
            ),
            "level": 2,
            "steps": [
                {
                    "step_number": 1,
                    "label": "Equation",
                    "type": "drag_drop",
                    "is_given": True,
                    "instruction": "Arrange the two-point Arrhenius equation.",
                    "explanation": "Use the logarithmic form to relate two rate constants at different temperatures.",
                    "equationParts": [
                        "$\\ln\\left(\\frac{k_2}{k_1}\\right)$",
                        "=",
                        "$\\frac{E_a}{R}$",
                        "$\\left(\\frac{1}{T_1} - \\frac{1}{T_2}\\right)$",
                    ],
                    "skillUsed": "Apply the Arrhenius equation to relate rate constants and temperature",
                },
                {
                    "step_number": 2,
                    "label": "Knowns",
                    "type": "multi_input",
                    "is_given": True,
                    "instruction": "Identify the given values.",
                    "explanation": "List both rate constants, both temperatures, and the gas constant.",
                    "inputFields": [
                        {"label": "$k_1$", "value": "$2.50 \\times 10^{-3}$", "unit": "$\\text{s}^{-1}$"},
                        {"label": "$k_2$", "value": "$8.20 \\times 10^{-3}$", "unit": "$\\text{s}^{-1}$"},
                        {"label": "$T_1$", "value": "$298$", "unit": "$\\text{K}$"},
                        {"label": "$T_2$", "value": "$315$", "unit": "$\\text{K}$"},
                        {"label": "$R$", "value": "$8.314$", "unit": "$\\text{J}\\,\\text{mol}^{-1}\\,\\text{K}^{-1}$"},
                    ],
                    "skillUsed": "Extract known values from a kinetics problem",
                },
                {
                    "step_number": 3,
                    "label": "Substitute",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Substitute values into the equation.",
                    "explanation": "$\\ln\\left(\\frac{8.20 \\times 10^{-3}}{2.50 \\times 10^{-3}}\\right) = \\frac{E_a}{8.314}\\left(\\frac{1}{298}-\\frac{1}{315}\\right)$.",
                    "correctAnswer": "ln(8.20e-3 / 2.50e-3) = (Ea / 8.314) * (1/298 - 1/315)",
                    "skillUsed": "Substitute values into the Arrhenius equation",
                },
                {
                    "step_number": 4,
                    "label": "Calculate",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Solve for $E_a$ in J/mol.",
                    "explanation": "$\\ln(3.28) \\approx 1.187$; denominator $\\approx 1.81 \\times 10^{-4}$; $E_a \\approx 5.46 \\times 10^{4}\\,\\text{J/mol}$.",
                    "correctAnswer": "$5.46 \\times 10^{4}$",
                    "skillUsed": "Calculate activation energy using logarithms and algebra",
                },
                {
                    "step_number": 5,
                    "label": "Answer",
                    "type": "interactive",
                    "is_given": False,
                    "instruction": "Express the activation energy in kJ/mol.",
                    "explanation": "Convert: $E_a = 54.6\\,\\text{kJ/mol}$ (3 significant figures).",
                    "correctAnswer": "$54.6\\,\\text{kJ/mol}$",
                    "skillUsed": "Convert units and report with correct significant figures",
                },
            ],
        },
    ),

]
