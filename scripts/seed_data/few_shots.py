"""Curated few-shot examples for problem generation.

Tuple layout: (unit_id, lesson_index, difficulty, blueprint, problem_dict)
The `blueprint` field maps to Lesson.blueprint from the DB.
Field names in step dicts use camelCase (API/JSON convention) to match LLM output exactly.

Rules enforced here:
- All math/chemistry uses LaTeX ($...$) with \\text{} for units.
- Every step has an "explanation" field (<=20 words, one action-oriented sentence).
- "correctAnswer" is always a micro-input (never a sentence).
- No "hint" field (hints are generated on demand).
"""

FEW_SHOT_DATA: list[tuple[str, int, str, str, dict]] = [
    # ── 1. Architect: balancing a chemical equation ─────────────────────────
    (
        "unit-chemical-reactions",
        1,
        "medium",
        "architect",
        {
            "title": "Balancing the Formation of Aluminum Oxide",
            "statement": (
                "In a general chemistry lab, aluminum metal reacts with oxygen gas to form aluminum oxide.\n\n"
                "Determine the smallest whole-number coefficients to balance: "
                "$\\text{Al} + \\text{O}_2 \\rightarrow \\text{Al}_2\\text{O}_3$."
            ),
            "steps": [
                {
                    "label": "Inventory / Rules",
                    "type": "given",
                    "instruction": "Write the unbalanced skeleton equation.",
                    "explanation": "Al is aluminum; $\\text{O}_2$ is diatomic oxygen; product is $\\text{Al}_2\\text{O}_3$.",
                    "correctAnswer": "Al + O2 -> Al2O3",
                    "skillUsed": "Identify chemical rules/inventory",
                },
                {
                    "label": "Draft",
                    "type": "given",
                    "instruction": "Find the LCM for oxygen atoms on both sides.",
                    "explanation": "LCM of 2 ($\\text{O}_2$) and 3 ($\\text{Al}_2\\text{O}_3$) is $2 \\times 3 = 6$.",
                    "correctAnswer": "6",
                    "skillUsed": "Draft initial symbolic representation",
                },
                {
                    "label": "Refine",
                    "type": "given",
                    "instruction": "Place coefficients to reach 6 oxygen atoms.",
                    "explanation": "Put 3 in front of $\\text{O}_2$ and 2 in front of $\\text{Al}_2\\text{O}_3$.",
                    "correctAnswer": "Al + 3O2 -> 2Al2O3",
                    "skillUsed": "Refine structure/coefficients",
                },
                {
                    "label": "Final Answer",
                    "type": "given",
                    "instruction": "Balance aluminum and write the complete equation.",
                    "explanation": "2 × $\\text{Al}_2\\text{O}_3$ requires 4 Al atoms, so place 4 in front of Al.",
                    "correctAnswer": "4Al + 3O2 -> 2Al2O3",
                    "skillUsed": "Finalize symbolic answer",
                },
            ],
        },
    ),
    # ── 2. Detective: isotopic abundance → element identity ─────────────────
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
            "steps": [
                {
                    "label": "Data Extraction",
                    "type": "given",
                    "instruction": "Identify the mass of the most abundant isotope.",
                    "explanation": "The highest percentage ($69.0\\%$) corresponds to the $63.0 \\text{ amu}$ isotope.",
                    "correctAnswer": "63.0",
                    "skillUsed": "Extract data from representation",
                },
                {
                    "label": "Feature ID",
                    "type": "variable_id",
                    "instruction": "Convert the percentage abundances to decimals.",
                    "explanation": "Divide each percentage by 100: $69.0 \\div 100 = 0.690$ and $31.0 \\div 100 = 0.310$.",
                    "labeledValues": [
                        {"variable": "Abundance 1", "value": "0.690", "unit": ""},
                        {"variable": "Abundance 2", "value": "0.310", "unit": ""},
                    ],
                    "skillUsed": "Identify key feature or pattern",
                },
                {
                    "label": "Apply Concept",
                    "type": "interactive",
                    "instruction": "Calculate the weighted average atomic mass.",
                    "explanation": "$(63.0 \\times 0.690) + (65.0 \\times 0.310) = 43.47 + 20.15 = 63.62 \\text{ amu}$.",
                    "correctAnswer": "63.62",
                    "skillUsed": "Apply chemical concept to data",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Identify the element's chemical symbol.",
                    "explanation": "Atomic mass $63.62 \\text{ amu}$ matches Copper on the periodic table.",
                    "correctAnswer": "Cu",
                    "skillUsed": "Draw scientific conclusion",
                },
            ],
        },
    ),
    # ── 3. Recipe: limiting reactant → theoretical yield ────────────────────
    (
        "unit-stoichiometry",
        2,
        "medium",
        "recipe",
        {
            "title": "Theoretical Yield from a Limiting Reactant",
            "statement": (
                "$10.0 \\text{ g}$ of $\\text{H}_2$ reacts with $64.0 \\text{ g}$ of $\\text{O}_2$ "
                "according to: $2\\text{H}_2 + \\text{O}_2 \\rightarrow 2\\text{H}_2\\text{O}$.\n\n"
                "Calculate the theoretical yield of $\\text{H}_2\\text{O}$ in grams. "
                "(Molar masses: $\\text{H}_2 = 2.02 \\text{ g/mol}$, "
                "$\\text{O}_2 = 32.00 \\text{ g/mol}$, $\\text{H}_2\\text{O} = 18.02 \\text{ g/mol}$)"
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "given",
                    "instruction": "Calculate moles of $\\text{H}_2$ available.",
                    "explanation": "$10.0 \\text{ g} \\div 2.02 \\text{ g/mol} = 4.95 \\text{ mol}$.",
                    "correctAnswer": "4.95",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "label": "Conversion Factors",
                    "type": "given",
                    "instruction": "Calculate moles of $\\text{O}_2$ available.",
                    "explanation": "$64.0 \\text{ g} \\div 32.00 \\text{ g/mol} = 2.00 \\text{ mol}$.",
                    "correctAnswer": "2.00",
                    "skillUsed": "Select conversion factors",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Identify the limiting reactant.",
                    "explanation": "$2.00 \\text{ mol O}_2$ needs $4.00 \\text{ mol H}_2$; we have $4.95$, so $\\text{O}_2$ limits.",
                    "correctAnswer": "O2",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Find moles of $\\text{H}_2\\text{O}$ produced.",
                    "explanation": "$2.00 \\text{ mol O}_2 \\times (2 \\text{ mol H}_2\\text{O} / 1 \\text{ mol O}_2) = 4.00 \\text{ mol}$.",
                    "correctAnswer": "4.00",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Convert moles of $\\text{H}_2\\text{O}$ to grams.",
                    "explanation": "$4.00 \\text{ mol} \\times 18.02 \\text{ g/mol} = 72.1 \\text{ g}$ (3 sig figs).",
                    "correctAnswer": "72.1",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),
    # ── 4. Solver: zero-order kinetics ───────────────────────────────────────
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
            "steps": [
                {
                    "label": "Equation",
                    "type": "drag_drop",
                    "instruction": "Form the zero-order integrated rate law.",
                    "explanation": "Zero-order decay is linear: final concentration equals initial minus rate times time.",
                    "equationParts": ["[A]t", "=", "[A]0", "-", "k", "*", "t"],
                    "skillUsed": "Select correct equation",
                },
                {
                    "label": "Knowns",
                    "type": "variable_id",
                    "instruction": "Extract the given values with units.",
                    "explanation": None,
                    "labeledValues": [
                        {"variable": "[A]0", "value": "0.80", "unit": "M"},
                        {"variable": "k", "value": "0.020", "unit": "M/s"},
                        {"variable": "t", "value": "20", "unit": "s"},
                    ],
                    "skillUsed": "Extract known values with units",
                },
                {
                    "label": "Substitute",
                    "type": "interactive",
                    "instruction": "Plug the known values into the rate law.",
                    "explanation": "Replace $[A]_0 = 0.80$, $k = 0.020$, and $t = 20$ into $[A]_t = [A]_0 - kt$.",
                    "correctAnswer": "0.80 - (0.020)(20)",
                    "skillUsed": "Substitute values into equation",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Compute the product $k \\times t$.",
                    "explanation": "$0.020 \\text{ M/s} \\times 20 \\text{ s} = 0.40 \\text{ M}$.",
                    "correctAnswer": "0.40",
                    "skillUsed": "Compute final answer with sig figs",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Calculate the final concentration.",
                    "explanation": "$0.80 \\text{ M} - 0.40 \\text{ M} = 0.40 \\text{ M}$.",
                    "correctAnswer": "0.40",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),
    # ── 5. Recipe: molar mass → mass conversion (1-step) ────────────────────
    (
        "unit-stoichiometry",
        1,
        "medium",
        "recipe",
        {
            "title": "Mass of Calcium Chloride from Moles",
            "statement": (
                "A sample contains $0.375 \\text{ mol}$ of $\\text{CaCl}_2$. "
                "Calculate the mass of $\\text{CaCl}_2$ in grams.\n\n"
                "Use atomic masses: $\\text{Ca} = 40.08 \\text{ g/mol}$ and $\\text{Cl} = 35.45 \\text{ g/mol}$."
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "given",
                    "instruction": "Identify the starting value and the target unit.",
                    "explanation": "You are converting $0.375 \\text{ mol}$ into grams using the molar mass.",
                    "correctAnswer": "0.375 mol to g",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "label": "Conversion Factors",
                    "type": "given",
                    "instruction": "Calculate the molar mass of calcium chloride.",
                    "explanation": "$\\text{Ca} + 2(\\text{Cl}) = 40.08 + 2(35.45) = 110.98 \\text{ g/mol}$.",
                    "correctAnswer": "110.98 g/mol",
                    "skillUsed": "Select conversion factors",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "given",
                    "instruction": "Set up the conversion to cancel moles.",
                    "explanation": "Multiply starting moles by molar mass so the mol units cancel out.",
                    "correctAnswer": "0.375 * 110.98",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Calculate",
                    "type": "given",
                    "instruction": "Calculate the unrounded sample mass.",
                    "explanation": "$0.375 \\times 110.98 = 41.6175$.",
                    "correctAnswer": "41.6175",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Answer",
                    "type": "given",
                    "instruction": "Report the final mass with correct significant figures.",
                    "explanation": "Round to 3 sig figs because $0.375 \\text{ mol}$ has 3 sig figs.",
                    "correctAnswer": "41.6 g",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),
    # ── 6. Recipe: moles → grams via MgCl₂ molar mass (Level 1 all given) ───
    (
        "unit-mole",
        1,
        "medium",
        "recipe",
        {
            "title": "Molar Mass of Magnesium Chloride",
            "statement": (
                "A sample contains $2.50 \\text{ mol}$ of $\\text{MgCl}_2$.\n\n"
                "Using atomic masses $\\text{Mg} = 24.31 \\text{ g/mol}$ and $\\text{Cl} = 35.45 \\text{ g/mol}$, "
                "what mass in grams does the sample have?"
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "given",
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given $2.50 \\text{ mol}$ into grams (g).",
                    "correctAnswer": "2.50 mol to g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Conversion Factors",
                    "type": "given",
                    "instruction": "Find the molar mass of MgCl2.",
                    "explanation": "$\\text{Mg} + 2(\\text{Cl}) = 24.31 + 2(35.45) = 95.21 \\text{ g/mol}$.",
                    "correctAnswer": "95.21 g/mol",
                    "skillUsed": "Calculate molar mass of elements",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "given",
                    "instruction": "Set up the math to convert moles to grams.",
                    "explanation": "Multiply the given moles by the molar mass so the units cancel.",
                    "correctAnswer": "2.50 * 95.21",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Calculate",
                    "type": "given",
                    "instruction": "Calculate the unrounded mass.",
                    "explanation": None,
                    "correctAnswer": "238.025",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Answer",
                    "type": "given",
                    "instruction": "Report the final mass with correct significant figures and unit.",
                    "explanation": "Round to 3 significant figures because the given $2.50 \\text{ mol}$ has 3 sig figs.",
                    "correctAnswer": "238 g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
            ],
        },
    ),
    # ── 7. Recipe: moles → grams (single known molar mass, Level 2 faded) ───
    (
        "unit-mole",
        2,
        "medium",
        "recipe",
        {
            "title": "Finding the Mass of Copper Needed",
            "statement": (
                "In a general chemistry lab, you need to measure out copper metal for a reaction.\n\n"
                "You need $2.35 \\text{ mol}$ of $\\text{Cu}$. The molar mass of copper is $63.55 \\text{ g/mol}$.\n\n"
                "What mass of copper, in grams, is needed?"
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "given",
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given $2.35 \\text{ mol}$ into grams (g).",
                    "correctAnswer": "2.35 mol to g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Conversion Factors",
                    "type": "given",
                    "instruction": "Identify the molar mass of copper.",
                    "explanation": "The molar mass is given directly in the problem text.",
                    "correctAnswer": "63.55 g/mol",
                    "skillUsed": "Calculate molar mass of elements",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Set up the multiplication to convert to grams.",
                    "explanation": "Multiply the moles by the molar mass: $2.35 \\times 63.55$.",
                    "correctAnswer": "2.35 * 63.55",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Calculate the unrounded mass.",
                    "explanation": None,
                    "correctAnswer": "149.3425",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Report the final mass with correct significant figures and unit.",
                    "explanation": "Round to 3 significant figures based on the $2.35 \\text{ mol}$ input.",
                    "correctAnswer": "149 g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
            ],
        },
    ),
    # ── 8. Lawyer: periodic trend — atomic radius ────────────────────────────
    (
        "unit-periodic-table",
        2,
        "easy",
        "lawyer",
        {
            "title": "Comparing Atomic Radius: Na vs Cl",
            "statement": (
                "Compare the atomic radii of Sodium ($\\text{Na}$) and Chlorine ($\\text{Cl}$).\n\n"
                "Which element has a larger atomic radius and why?"
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "given",
                    "instruction": "Identify the principle governing atomic radius across a period.",
                    "explanation": "Across a period, proton count increases while shielding is constant, raising effective nuclear charge.",
                    "correctAnswer": "Effective Nuclear Charge",
                    "skillUsed": "Identify governing concept",
                },
                {
                    "label": "Relation",
                    "type": "comparison",
                    "instruction": "Compare the effective nuclear charge of Na and Cl.",
                    "explanation": "Na has 11 protons; Cl has 17 — Cl exerts a stronger pull on its valence electrons.",
                    "comparisonParts": ["Zeff of Na", "Zeff of Cl"],
                    "correctAnswer": "<",
                    "skillUsed": "State chemical relationship",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "How does higher Zeff affect the electron cloud?",
                    "explanation": "A stronger nuclear pull draws valence electrons inward, shrinking the atomic radius.",
                    "correctAnswer": "Pulls electrons closer",
                    "skillUsed": "Provide evidence/reasoning",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Which element has the larger atomic radius?",
                    "explanation": "Na has weaker nuclear pull, so its electron cloud extends farther from the nucleus.",
                    "correctAnswer": "Na",
                    "skillUsed": "State final conclusion",
                },
            ],
        },
    ),
]
