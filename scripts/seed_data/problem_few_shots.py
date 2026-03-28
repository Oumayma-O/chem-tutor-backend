"""Curated few-shot examples for problem generation.

Tuple layout: (unit_id, lesson_index, difficulty, blueprint, problem_dict)
The `blueprint` field maps to Lesson.blueprint from the DB.
Field names in step dicts use camelCase to match LLM output; seed normalizes ``inputFields`` to ``input_fields``.
Multi-answer steps: type ``multi_input`` with ``inputFields`` (each item: ``label``, ``value``, ``unit``).

Rules enforced here:
- All math/chemistry uses LaTeX ($...$) with \\text{} for units.
- Exponents MUST use braces: 10^{22}, NOT 10^22.
- Chemical formulas in correct_answer MUST use $\\mathrm{}$ formatting.
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
                "$\\mathrm{Al} + \\mathrm{O_2} \\rightarrow \\mathrm{Al_2O_3}$."
            ),
            "steps": [
                {
                    "label": "Inventory / Rules",
                    "type": "interactive",
                    "instruction": "Write the unbalanced skeleton equation.",
                    "explanation": "Al is aluminum; $\\mathrm{O_2}$ is diatomic oxygen; product is $\\mathrm{Al_2O_3}$.",
                    "correctAnswer": "$\\mathrm{Al} + \\mathrm{O_2} \\rightarrow \\mathrm{Al_2O_3}$",
                    "skillUsed": "Identify chemical rules/inventory",
                },
                {
                    "label": "Draft",
                    "type": "interactive",
                    "instruction": "Find the LCM for oxygen atoms on both sides.",
                    "explanation": "LCM of $2$ ($\\mathrm{O_2}$) and $3$ ($\\mathrm{Al_2O_3}$) is $2 \\times 3 = 6$.",
                    "correctAnswer": "6",
                    "skillUsed": "Draft initial symbolic representation",
                },
                {
                    "label": "Refine",
                    "type": "interactive",
                    "instruction": "Place coefficients to reach 6 oxygen atoms.",
                    "explanation": "Put $3$ in front of $\\mathrm{O_2}$ and $2$ in front of $\\mathrm{Al_2O_3}$.",
                    "correctAnswer": "$\\mathrm{Al} + 3\\mathrm{O_2} \\rightarrow 2\\mathrm{Al_2O_3}$",
                    "skillUsed": "Refine structure/coefficients",
                },
                {
                    "label": "Final Answer",
                    "type": "interactive",
                    "instruction": "Balance aluminum and write the complete equation.",
                    "explanation": "Two $\\mathrm{Al_2O_3}$ molecules require $4$ Al atoms, so place $4$ in front of Al.",
                    "correctAnswer": "$4\\mathrm{Al} + 3\\mathrm{O_2} \\rightarrow 2\\mathrm{Al_2O_3}$",
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
                    "type": "interactive",
                    "instruction": "Identify the mass of the most abundant isotope.",
                    "explanation": "The highest percentage ($69.0\\%$) corresponds to the $63.0 \\text{ amu}$ isotope.",
                    "correctAnswer": "63.0",
                    "skillUsed": "Extract data from representation",
                },
                {
                    "label": "Feature ID",
                    "type": "multi_input",
                    "instruction": "Convert the percentage abundances to decimals.",
                    "explanation": "Divide each percentage by $100$: $69.0 \\div 100 = 0.690$ and $31.0 \\div 100 = 0.310$.",
                    "inputFields": [
                        {"label": "Abundance 1", "value": "$0.690$", "unit": ""},
                        {"label": "Abundance 2", "value": "$0.310$", "unit": ""},
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
                    "correctAnswer": "$\\mathrm{Cu}$",
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
                "$10.0 \\text{ g}$ of $\\mathrm{H_2}$ reacts with $64.0 \\text{ g}$ of $\\mathrm{O_2}$ "
                "according to: $2\\mathrm{H_2} + \\mathrm{O_2} \\rightarrow 2\\mathrm{H_2O}$.\n\n"
                "Calculate the theoretical yield of $\\mathrm{H_2O}$ in grams. "
                "(Molar masses: $\\mathrm{H_2} = 2.02 \\text{ g/mol}$, "
                "$\\mathrm{O_2} = 32.00 \\text{ g/mol}$, $\\mathrm{H_2O} = 18.02 \\text{ g/mol}$)"
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "instruction": "Calculate moles of $\\mathrm{H_2}$ available.",
                    "explanation": "$10.0 \\text{ g} \\div 2.02 \\text{ g/mol} = 4.95 \\text{ mol}$.",
                    "correctAnswer": "4.95",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "instruction": "Calculate moles of $\\mathrm{O_2}$ available.",
                    "explanation": "$64.0 \\text{ g} \\div 32.00 \\text{ g/mol} = 2.00 \\text{ mol}$.",
                    "correctAnswer": "2.00",
                    "skillUsed": "Select conversion factors",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Identify the limiting reactant.",
                    "explanation": "$2.00 \\text{ mol } \\mathrm{O_2}$ needs $4.00 \\text{ mol } \\mathrm{H_2}$; we have $4.95 \\text{ mol}$, so $\\mathrm{O_2}$ limits.",
                    "correctAnswer": "$\\mathrm{O_2}$",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Find moles of $\\mathrm{H_2O}$ produced.",
                    "explanation": "$2.00 \\text{ mol } \\mathrm{O_2} \\times (2 \\text{ mol } \\mathrm{H_2O} / 1 \\text{ mol } \\mathrm{O_2}) = 4.00 \\text{ mol}$.",
                    "correctAnswer": "4.00",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Convert moles of $\\mathrm{H_2O}$ to grams.",
                    "explanation": "$4.00 \\text{ mol} \\times 18.02 \\text{ g/mol} = 72.1 \\text{ g}$ ($3$ sig figs).",
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
                    "equationParts": ["[A]_t", "=", "[A]_0", "-", "k", "*", "t"],
                    "skillUsed": "Select correct equation",
                },
                {
                    "label": "Knowns",
                    "type": "multi_input",
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
                    "correctAnswer": "$0.40 \\text{ M}$",
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
                "A sample contains $0.375 \\text{ mol}$ of $\\mathrm{CaCl_2}$. "
                "Calculate the mass of $\\mathrm{CaCl_2}$ in grams.\n\n"
                "Use atomic masses: $\\mathrm{Ca} = 40.08 \\text{ g/mol}$ and $\\mathrm{Cl} = 35.45 \\text{ g/mol}$."
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "instruction": "Identify the starting value and the target unit.",
                    "explanation": "You are converting $0.375 \\text{ mol}$ into grams using the molar mass.",
                    "correctAnswer": "0.375 mol to g",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "instruction": "Calculate the molar mass of calcium chloride.",
                    "explanation": "$\\mathrm{Ca} + 2(\\mathrm{Cl}) = 40.08 + 2(35.45) = 110.98 \\text{ g/mol}$.",
                    "correctAnswer": "$110.98 \\text{ g/mol}$",
                    "skillUsed": "Select conversion factors",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Set up the conversion to cancel moles.",
                    "explanation": "Multiply starting moles by molar mass so the $\\text{mol}$ units cancel out.",
                    "correctAnswer": "0.375 * 110.98",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Calculate the unrounded sample mass.",
                    "explanation": "$0.375 \\times 110.98 = 41.6175$.",
                    "correctAnswer": "41.6175",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Report the final mass with correct significant figures.",
                    "explanation": "Round to $3$ sig figs because $0.375 \\text{ mol}$ has $3$ sig figs.",
                    "correctAnswer": "$41.6 \\text{ g}$",
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
                "A sample contains $2.50 \\text{ mol}$ of $\\mathrm{MgCl_2}$.\n\n"
                "Using atomic masses $\\mathrm{Mg} = 24.31 \\text{ g/mol}$ and $\\mathrm{Cl} = 35.45 \\text{ g/mol}$, "
                "what mass in grams does the sample have?"
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given $2.50 \\text{ mol}$ into grams ($\\text{g}$).",
                    "correctAnswer": "2.50 mol to g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "instruction": "Find the molar mass of $\\mathrm{MgCl_2}$.",
                    "explanation": "$\\mathrm{Mg} + 2(\\mathrm{Cl}) = 24.31 + 2(35.45) = 95.21 \\text{ g/mol}$.",
                    "correctAnswer": "$95.21 \\text{ g/mol}$",
                    "skillUsed": "Calculate molar mass of elements",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Set up the math to convert moles to grams.",
                    "explanation": "Multiply the given moles by the molar mass so the units cancel.",
                    "correctAnswer": "2.50 * 95.21",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Calculate the unrounded mass.",
                    "explanation": "Compute the product: $2.50 \\times 95.21 = 238.025$.",
                    "correctAnswer": "238.025",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Report the final mass with correct significant figures and unit.",
                    "explanation": "Round to $3$ significant figures because the given $2.50 \\text{ mol}$ has $3$ sig figs.",
                    "correctAnswer": "$238 \\text{ g}$",
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
                "You need $2.35 \\text{ mol}$ of $\\mathrm{Cu}$. The molar mass of copper is $63.55 \\text{ g/mol}$.\n\n"
                "What mass of copper, in grams, is needed?"
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given $2.35 \\text{ mol}$ into grams ($\\text{g}$).",
                    "correctAnswer": "2.35 mol to g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "instruction": "Identify the molar mass of copper.",
                    "explanation": "The molar mass is given directly in the problem text as $63.55 \\text{ g/mol}$.",
                    "correctAnswer": "$63.55 \\text{ g/mol}$",
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
                    "explanation": "Compute the product: $2.35 \\times 63.55 = 149.3425$.",
                    "correctAnswer": "149.3425",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Report the final mass with correct significant figures and unit.",
                    "explanation": "Round to $3$ significant figures based on the $2.35 \\text{ mol}$ input.",
                    "correctAnswer": "$149 \\text{ g}$",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
            ],
        },
    ),
    # ── 8. Lawyer: thermochem — system, surroundings, heat flow ─────────────
    (
        "unit-thermochem",
        1,
        "medium",
        "lawyer",
        {
            "title": "System, Surroundings, and Heat Flow",
            "statement": (
                "A sample of water in a coffee-cup calorimeter cools from $25.0^\\circ\\text{C}$ to "
                "$18.0^\\circ\\text{C}$ after solid ammonium nitrate, $\\mathrm{NH_4NO_3}$, dissolves.\n\n"
                "Treat the dissolving $\\mathrm{NH_4NO_3}$ as the system and the water as the surroundings. "
                "Determine whether the process is endothermic or exothermic, identify the direction of heat flow, "
                "and compare the relationship between $q_{\\text{system}}$ and $q_{\\text{surr}}$."
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "interactive",
                    "instruction": "Identify the system and the surroundings.",
                    "explanation": "The chemical process of the salt dissolving is the system; the solvent (water) is the surroundings.",
                    "correctAnswer": "System: $\\mathrm{NH_4NO_3}$, Surr: Water",
                    "skillUsed": "Identify governing concept",
                },
                {
                    "label": "Relation",
                    "type": "interactive",
                    "instruction": "Determine the direction of heat flow.",
                    "explanation": "Water temperature decreases, so thermal energy leaves the water and enters the dissolving salt.",
                    "correctAnswer": "From water to $\\mathrm{NH_4NO_3}$",
                    "skillUsed": "State chemical relationship",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "Classify the process as endothermic or exothermic.",
                    "explanation": "Processes that absorb heat from their surroundings are classified as endothermic.",
                    "correctAnswer": "Endothermic",
                    "skillUsed": "Provide evidence/reasoning",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Compare $q_{\\text{system}}$ and $q_{\\text{surr}}$.",
                    "explanation": "Conservation of energy: heat gained by the system equals heat lost by the surroundings.",
                    "correctAnswer": "$q_{\\text{system}} = -q_{\\text{surr}}$",
                    "skillUsed": "State final conclusion",
                },
            ],
        },
    ),
    # ── 9. Lawyer: periodic trend — atomic radius ────────────────────────────
    (
        "unit-periodic-table",
        2,
        "easy",
        "lawyer",
        {
            "title": "Comparing Atomic Radius: Na vs Cl",
            "statement": (
                "Compare the atomic radii of Sodium ($\\mathrm{Na}$) and Chlorine ($\\mathrm{Cl}$).\n\n"
                "Which element has a larger atomic radius and why?"
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "interactive",
                    "instruction": "Identify the principle governing atomic radius across a period.",
                    "explanation": "Across a period, proton count increases while shielding is constant, raising effective nuclear charge.",
                    "correctAnswer": "Effective Nuclear Charge",
                    "skillUsed": "Identify governing concept",
                },
                {
                    "label": "Relation",
                    "type": "comparison",
                    "instruction": "Compare the effective nuclear charge of Na and Cl.",
                    "explanation": "$\\mathrm{Na}$ has $11$ protons; $\\mathrm{Cl}$ has $17$ — $\\mathrm{Cl}$ exerts a stronger pull on its valence electrons.",
                    "comparisonParts": ["Zeff of $\\mathrm{Na}$", "Zeff of $\\mathrm{Cl}$"],
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
                    "explanation": "$\\mathrm{Na}$ has weaker nuclear pull, so its electron cloud extends farther from the nucleus.",
                    "correctAnswer": "$\\mathrm{Na}$",
                    "skillUsed": "State final conclusion",
                },
            ],
        },
    ),
    # ── 10. Lawyer: thermochem — calculating q_surr and q_system ─────────────
    (
        "unit-thermochem",
        1,
        "medium",
        "lawyer",
        {
            "title": "Heat Flow in Dissolving Ammonium Nitrate",
            "statement": (
                "A student dissolves $8.00 \\text{ g}$ of $\\mathrm{NH_4NO_3}$ in water inside a coffee-cup calorimeter. "
                "The solution temperature drops from $25.0^\\circ\\text{C}$ to $19.5^\\circ\\text{C}$.\n\n"
                "Assume the solution has a mass of $100.0 \\text{ g}$ and a specific heat capacity of $4.18 \\text{ J/(g }^\\circ\\text{C)}$. "
                "Determine whether the dissolving is endothermic or exothermic, and calculate $q_{\\text{system}}$ in $\\text{kJ}$."
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "interactive",
                    "instruction": "Identify the system and surroundings.",
                    "explanation": "The dissolving salt is the system; the solution (water) acts as the surroundings.",
                    "correctAnswer": "System: NH4NO3, Surr: Water",
                    "skillUsed": "Define system and surroundings",
                },
                {
                    "label": "Relation",
                    "type": "interactive",
                    "instruction": "Compare initial and final temperatures.",
                    "explanation": "Since $19.5^\\circ\\text{C} < 25.0^\\circ\\text{C}$, the surroundings cooled down.",
                    "correctAnswer": "19.5 < 25.0",
                    "skillUsed": "Identify direction of heat flow",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "Calculate $q_{\\text{surr}}$ in joules.",
                    "explanation": "Using $q = mc\\Delta T$: $(100.0)(4.18)(19.5 - 25.0) = -2299 \\text{ J}$.",
                    "correctAnswer": "-2299",
                    "skillUsed": "Perform calorimetry calculations",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "State the process type and find $q_{\\text{system}}$ in kJ.",
                    "explanation": "$q_{\\text{system}} = -q_{\\text{surr}} = +2299 \\text{ J}$, which is $2.30 \\text{ kJ}$. Positive means endothermic.",
                    "correctAnswer": "endothermic, 2.30",
                    "skillUsed": "Distinguish endothermic and exothermic",
                },
            ],
        },
    ),
    # ── 11. Lawyer: thermochem — classifying heat flow (NH4NO3) ───────────────
    (
        "unit-thermochem",
        0,
        "medium",
        "lawyer",
        {
            "title": "Classifying Heat Flow in a Dissolving Process",
            "statement": (
                "In an AP Chemistry lab, a student dissolves $\\mathrm{NH_4NO_3}$ in water inside a coffee-cup calorimeter. "
                "During the process, the temperature of the solution drops from $25.0^\\circ\\text{C}$ to $19.5^\\circ\\text{C}$.\n\n"
                "Treat the dissolving chemicals as the system and the water plus calorimeter as the surroundings. "
                "Identify the system and surroundings, compare their heat flow signs, and determine if the process is endothermic or exothermic."
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "multi_input",
                    "instruction": "List the system and surroundings.",
                    "explanation": "The chemicals dissolving are the system; water and calorimeter are surroundings.",
                    "inputFields": [
                        {"label": "System", "value": "$\\mathrm{NH_4NO_3}$ dissolving in water", "unit": ""},
                        {"label": "Surroundings", "value": "water and calorimeter", "unit": ""},
                    ],
                    "skillUsed": "Define system and surroundings",
                },
                {
                    "label": "Relation",
                    "type": "comparison",
                    "instruction": "Compare $q_{\\text{system}}$ and $q_{\\text{surr}}$.",
                    "explanation": "Heat lost by the surroundings equals heat gained by the system, so their signs are opposite but magnitudes are equal.",
                    "comparisonParts": [
                        "$q_{\\text{system}}$",
                        "$-q_{\\text{surr}}$",
                    ],
                    "correctAnswer": "=",
                    "skillUsed": "Apply conservation of energy",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "Determine the sign of $q_{\\text{system}}$.",
                    "explanation": "Because the surroundings got colder, heat moved into the system, making $q_{\\text{system}}$ positive.",
                    "correctAnswer": "positive",
                    "skillUsed": "Identify direction of heat flow",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Classify the dissolving process.",
                    "explanation": "Processes that absorb heat (positive $q$) are endothermic.",
                    "correctAnswer": "endothermic",
                    "skillUsed": "Distinguish endothermic from exothermic processes",
                },
            ],
        },
    ),
    # ── 12. Lawyer: thermochem — exothermic acid-base (HCl + NaOH) ───────────
    (
        "unit-thermochem",
        0,
        "medium",
        "lawyer",
        {
            "title": "Exothermic Acid-Base Neutralization",
            "statement": (
                "A student mixes hydrochloric acid ($\\mathrm{HCl}$) and sodium hydroxide ($\\mathrm{NaOH}$) in a coffee-cup calorimeter. "
                "During the reaction, the temperature of the water rises from $22.4^\\circ\\text{C}$ to $28.9^\\circ\\text{C}$.\n\n"
                "Treat the reacting ions as the system. Is the reaction endothermic or exothermic, and what is the sign of $q_{\\text{system}}$?"
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "multi_input",
                    "instruction": "Identify the system and surroundings.",
                    "explanation": "The chemical reaction is the system; the surrounding water in the cup is the surroundings.",
                    "inputFields": [
                        {"label": "System", "value": "$\\mathrm{HCl}$ and $\\mathrm{NaOH}$ reacting", "unit": ""},
                        {"label": "Surroundings", "value": "solution water in the cup", "unit": ""},
                    ],
                    "skillUsed": "Define system and surroundings",
                },
                {
                    "label": "Relation",
                    "type": "comparison",
                    "instruction": "Compare final and initial surroundings temperatures.",
                    "explanation": "The final temperature ($28.9^\\circ\\text{C}$) is greater than the initial temperature ($22.4^\\circ\\text{C}$).",
                    "comparisonParts": [
                        "Final Temperature",
                        "Initial Temperature",
                    ],
                    "correctAnswer": ">",
                    "skillUsed": "Identify direction of heat flow",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "Classify the process by heat flow.",
                    "explanation": "Because the surroundings warmed up, the system must have released heat.",
                    "correctAnswer": "exothermic",
                    "skillUsed": "Distinguish endothermic from exothermic processes",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "State the sign of $q_{\\text{system}}$.",
                    "explanation": "Exothermic reactions lose heat to the surroundings, meaning $q_{\\text{system}}$ is negative.",
                    "correctAnswer": "negative",
                    "skillUsed": "Distinguish endothermic from exothermic processes",
                },
            ],
        },
    ),
    # ── 13. Recipe: mole — mass to formula units (CaCl2), sci notation ───────
    (
        "unit-mole",
        2,
        "medium",
        "recipe",
        {
            "title": "Particles from a Sample of Calcium Chloride",
            "statement": (
                "In a chemistry lab, a student measures a sample of calcium chloride, $\\mathrm{CaCl_2}$.\n\n"
                "The sample has a mass of $11.1 \\text{ g}$. Use atomic masses $\\mathrm{Ca} = 40.08 \\text{ g/mol}$ and "
                "$\\mathrm{Cl} = 35.45 \\text{ g/mol}$. Avogadro's number is $6.022 \\times 10^{23}$.\n\n"
                "How many formula units (individual particles) of $\\mathrm{CaCl_2}$ are in the sample?"
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "interactive",
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given mass ($11.1 \\text{ g}$) into particles, called formula units.",
                    "correctAnswer": "11.1 g to formula units",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "instruction": "Find the molar mass of calcium chloride.",
                    "explanation": "$\\mathrm{Ca} + 2(\\mathrm{Cl}) = 40.08 + 2(35.45) = 110.98 \\text{ g/mol}$.",
                    "correctAnswer": "110.98",
                    "skillUsed": "Calculate molar mass of compounds",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Set up the two-step conversion.",
                    "explanation": "Divide by molar mass to get moles, then multiply by Avogadro's number ($6.022 \\times 10^{23}$).",
                    "correctAnswer": "(11.1 / 110.98) × 6.022×10²³",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Calculate the unrounded number of formula units.",
                    "explanation": "Divide mass by molar mass to get moles, then multiply by Avogadro's number.",
                    "correctAnswer": "6.0238 × 10²²",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Report the final answer in scientific notation.",
                    "explanation": "Round to 3 significant figures because the starting mass ($11.1 \\text{ g}$) has 3 sig figs.",
                    "correctAnswer": "6.02 × 10²²",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),
    # ── 14. Detective: kinetics — initial rates → rate law ────────────────────
    (
        "ap-unit-5",
        1,
        "medium",
        "detective",
        {
            "title": "Method of Initial Rates for a Two-Reactant Reaction",
            "statement": (
                "A reaction between aqueous reactants $\\mathrm{X}$ and $\\mathrm{Y}$ forms products. "
                "A student measures initial rates at the same temperature for several trials.\n\n"
                "Experiment 1: $[\\mathrm{X}] = 0.15 \\text{ M}$, $[\\mathrm{Y}] = 0.10 \\text{ M}$, "
                "rate $= 3.0 \\times 10^{-4} \\text{ M/s}$.\n\n"
                "Experiment 2: $[\\mathrm{X}] = 0.30 \\text{ M}$, $[\\mathrm{Y}] = 0.10 \\text{ M}$, "
                "rate $= 1.2 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 3: $[\\mathrm{X}] = 0.15 \\text{ M}$, $[\\mathrm{Y}] = 0.20 \\text{ M}$, "
                "rate $= 6.0 \\times 10^{-4} \\text{ M/s}$.\n\n"
                "Use the data to determine the order in $\\mathrm{X}$, the order in $\\mathrm{Y}$, "
                "the overall reaction order, and the rate law."
            ),
            "steps": [
                {
                    "label": "Data Extraction",
                    "type": "multi_input",
                    "instruction": "Extract the three experiment values.",
                    "explanation": "Compare trials where one reactant concentration stays constant.",
                    "inputFields": [
                        {"label": "Experiment 1 rate", "value": "$3.0 \\times 10^{-4}$", "unit": "M/s"},
                        {"label": "Experiment 2 X concentration", "value": "$0.30$", "unit": "M"},
                        {"label": "Experiment 3 Y concentration", "value": "$0.20$", "unit": "M"},
                    ],
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Feature ID",
                    "type": "interactive",
                    "instruction": "Identify the order in $\\mathrm{X}$.",
                    "explanation": "From Experiments 1 and 2, doubling $[\\mathrm{X}]$ quadruples the rate, so order is $2$.",
                    "correctAnswer": "2",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Apply Concept",
                    "type": "interactive",
                    "instruction": "Identify the order in $\\mathrm{Y}$.",
                    "explanation": "From Experiments 1 and 3, doubling $[\\mathrm{Y}]$ doubles the rate, so order is $1$.",
                    "correctAnswer": "1",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Conclusion",
                    "type": "multi_input",
                    "instruction": "State the rate law and overall order.",
                    "explanation": "Add exponents: $2 + 1 = 3$, so the reaction is third order overall.",
                    "inputFields": [
                        {"label": "Rate law", "value": "$k[\\mathrm{X}]^{2}[\\mathrm{Y}]$", "unit": ""},
                        {"label": "Overall reaction order", "value": "3rd order", "unit": ""},
                    ],
                    "skillUsed": "Determine overall reaction order",
                },
            ],
        },
    ),
    # ── 15. Recipe: molar mass (Level 3 — interactive for numeric steps, no drag_drop) ──
    (
        "unit-mole",
        1,
        "easy",
        "recipe",
        {
            "title": "Finding the Molar Mass of Oxygen Gas",
            "statement": (
                "A sample of oxygen gas is written as $\\mathrm{O_2}$.\n\n"
                "Use the atomic mass of oxygen as $16.00 \\text{ g/mol}$. "
                "What is the molar mass of $\\mathrm{O_2}$?"
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "multi_input",
                    "instruction": "Identify the formula and atomic mass values.",
                    "explanation": "Extract the chemical formula and the mass from the text.",
                    "inputFields": [
                        {"label": "formula", "value": "$\\mathrm{O_2}$", "unit": ""},
                        {"label": "O atomic mass", "value": "$16.00$", "unit": "g/mol"},
                    ],
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "instruction": "State the number of oxygen atoms present.",
                    "explanation": "The subscript 2 means two oxygen atoms are in $\\mathrm{O_2}$.",
                    "correctAnswer": "2",
                    "skillUsed": "Select conversion factors",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Write the arithmetic expression for the molar mass.",
                    "explanation": "Multiply the number of atoms by the atomic mass.",
                    "correctAnswer": "2 * 16.00",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Compute the molar mass.",
                    "explanation": "Multiply atoms by atomic mass to get total molar mass.",
                    "correctAnswer": "32.00",
                    "skillUsed": "Compute final answer with sig figs",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Report the final molar mass with units.",
                    "explanation": "Keep two decimal places from the given atomic mass.",
                    "correctAnswer": "32.00 g/mol",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),
    # ── 16. Lawyer: safety — lab equipment and procedures ────────────────────
    (
        "unit-intro-chem",
        0,
        "medium",
        "lawyer",
        {
            "title": "Safe Response to a Chemical Splash",
            "statement": (
                "During a chemistry lab, a student accidentally drops a beaker of dilute $\\mathrm{HCl}$. "
                "A small splash hits their face, near their eyes. The hazard label on the acid bottle shows the corrosive symbol.\n\n"
                "The student is wearing their safety goggles on their forehead instead of over their eyes. "
                "Identify the hazard, determine the necessary safety equipment, state the required procedure, and conclude the final action."
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "multi_input",
                    "instruction": "Identify the primary hazard and the broken rule.",
                    "explanation": "Extract the specific danger and the safety violation from the scenario.",
                    "inputFields": [
                        {"label": "Hazard", "value": "corrosive acid", "unit": ""},
                        {"label": "Broken Rule", "value": "goggles on forehead", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Relation",
                    "type": "interactive",
                    "instruction": "Name the specific safety equipment required for this exposure.",
                    "explanation": "Chemical contact near or in the eyes requires immediate flushing with a specialized station.",
                    "correctAnswer": "eyewash station",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "State the standard procedure for using this equipment.",
                    "explanation": "Standard lab protocol requires flushing the affected area continuously to fully dilute the corrosive chemical.",
                    "correctAnswer": "rinse for 15 minutes",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "What is the very next action after using the equipment?",
                    "explanation": "The instructor must be notified immediately after any accident or exposure occurs.",
                    "correctAnswer": "notify the teacher",
                    "skillUsed": "Identify common lab safety rules",
                },
            ],
        },
    ),
    # ── 17. Lawyer: safety — Level 1 (Worked) — Personal Protective Equipment ──
    (
        "unit-intro-chem",
        0,
        "easy",
        "lawyer",
        {
            "title": "Proper Use of Personal Protective Equipment",
            "statement": (
                "During a lab, a student is pouring a concentrated solution of sodium hydroxide, $\\mathrm{NaOH}$, into a graduated cylinder. "
                "Because their safety goggles are fogging up, the student pushes the goggles up to rest on their forehead.\n\n"
                "The bottle of $\\mathrm{NaOH}$ has a corrosive hazard symbol. "
                "Identify the hazard and the broken rule, explain why the behavior is dangerous, and state the correct action."
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "multi_input",
                    "instruction": "Identify the primary hazard and the broken rule.",
                    "explanation": "Extract the chemical danger and the unsafe behavior from the scenario.",
                    "inputFields": [
                        {"label": "Hazard", "value": "corrosive base", "unit": ""},
                        {"label": "Broken Rule", "value": "goggles on forehead", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Relation",
                    "type": "interactive",
                    "instruction": "State the safety rule being violated.",
                    "explanation": "Safety equipment must be worn correctly to provide actual protection.",
                    "correctAnswer": "always wear safety goggles over the eyes",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "State the risk of this unsafe behavior.",
                    "explanation": "A splash from a corrosive base can cause permanent eye damage if unprotected.",
                    "correctAnswer": "chemical splash to the eyes",
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Give the safest immediate action.",
                    "explanation": "The student must secure their protective equipment before continuing the experiment.",
                    "correctAnswer": "stop pouring and put goggles over eyes",
                    "skillUsed": "Identify common lab safety rules",
                },
            ],
        },
    ),
    # ── 18. Lawyer: safety — Level 2 (Faded) — Chemical Waste Disposal ────────
    (
        "unit-intro-chem",
        0,
        "medium",
        "lawyer",
        {
            "title": "Safe Chemical Disposal Procedures",
            "statement": (
                "A student completes a precipitation lab involving toxic heavy metals, including a solution of lead(II) nitrate, $\\mathrm{Pb(NO_3)_2}$. "
                "To clean up quickly, the student carries the remaining solution to the sink and prepares to pour it down the drain.\n\n"
                "The lab instructions explicitly state that heavy metals are environmental hazards. "
                "Identify the hazard and the broken rule, state the correct disposal method, and conclude the immediate safe action."
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "multi_input",
                    "instruction": "Identify the hazard and the broken rule.",
                    "explanation": "Extract the specific chemical danger and the unsafe action from the scenario.",
                    "inputFields": [
                        {"label": "Hazard", "value": "toxic heavy metals", "unit": ""},
                        {"label": "Broken Rule", "value": "pouring chemicals down the sink", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Relation",
                    "type": "interactive",
                    "instruction": "State the safety rule regarding chemical waste.",
                    "explanation": "Chemicals cannot be discarded in standard drains unless explicitly permitted.",
                    "correctAnswer": "dispose of chemicals according to lab instructions",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "Where should this specific waste go?",
                    "explanation": "Heavy metals require a specialized, marked hazardous waste container.",
                    "correctAnswer": "designated hazardous waste container",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "What should the student do right now?",
                    "explanation": "If unsure of the disposal location, the student must halt and consult the instructor.",
                    "correctAnswer": "stop and ask the teacher",
                    "skillUsed": "Identify common lab safety rules",
                },
            ],
        },
    ),
    # ── 19. Lawyer: safety — Level 3 (Practice) — Food and Drink Contamination ─
    (
        "unit-intro-chem",
        0,
        "hard",
        "lawyer",
        {
            "title": "Preventing Cross-Contamination",
            "statement": (
                "During a crystal-growing experiment with copper(II) sulfate, $\\mathrm{CuSO_4}$, a student becomes thirsty. "
                "They pull a water bottle from their backpack, place it on the lab bench next to their chemical powders, and take a drink.\n\n"
                "Copper(II) sulfate is harmful if swallowed. "
                "Identify the hazard and the broken rule, explain the unseen risk, and state the safest immediate action."
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "multi_input",
                    "instruction": "Identify the hazard and the broken rule.",
                    "explanation": "Extract the chemical danger and the prohibited behavior.",
                    "inputFields": [
                        {"label": "Hazard", "value": "harmful if swallowed", "unit": ""},
                        {"label": "Broken Rule", "value": "drinking in the lab", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Relation",
                    "type": "interactive",
                    "instruction": "State the safety rule being violated.",
                    "explanation": "Labs strictly prohibit ingestion to prevent accidental poisoning.",
                    "correctAnswer": "never eat or drink in the laboratory",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "State the hidden risk of having the bottle on the bench.",
                    "explanation": "Chemical dust or splashes can easily contaminate food or drink containers nearby.",
                    "correctAnswer": "chemical contamination of the bottle",
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Give the safest immediate action.",
                    "explanation": "The food or drink item must be removed from the hazardous environment immediately.",
                    "correctAnswer": "move the bottle outside the lab and wash hands",
                    "skillUsed": "Identify common lab safety rules",
                },
            ],
        },
    ),
    # ── 20. Architect: electron configuration (drag_drop for ordered sequence) ─
    (
        "unit-electrons",
        2,
        "medium",
        "architect",
        {
            "title": "Electron Configuration of Phosphorus",
            "statement": (
                "An AP Chemistry student is reviewing atomic structure. "
                "A neutral phosphorus ($\\mathrm{P}$) atom has an atomic number of $15$.\n\n"
                "Determine the occupied subshells, assemble the full electron configuration, "
                "and apply Hund's rule to the valence electrons."
            ),
            "steps": [
                {
                    "label": "Inventory / Rules",
                    "type": "multi_input",
                    "instruction": "Distribute the 15 electrons into the correct subshells.",
                    "explanation": "Following the Aufbau principle: $1s$, $2s$, $2p$, $3s$ fill completely; 3 remain for $3p$.",
                    "skillUsed": "Write basic electron configurations",
                    "inputFields": [
                        {"label": "1s", "value": "2", "unit": "$e^-$"},
                        {"label": "2s", "value": "2", "unit": "$e^-$"},
                        {"label": "2p", "value": "6", "unit": "$e^-$"},
                        {"label": "3s", "value": "2", "unit": "$e^-$"},
                        {"label": "3p", "value": "3", "unit": "$e^-$"},
                    ],
                },
                {
                    "label": "Draft",
                    "type": "drag_drop",
                    "instruction": "Arrange the subshells in the correct Aufbau order.",
                    "explanation": "Fill lowest to highest energy: $1s \\rightarrow 2s \\rightarrow 2p \\rightarrow 3s \\rightarrow 3p$.",
                    "skillUsed": "Write full electron configurations",
                    "equationParts": ["$1s^2$", "$2s^2$", "$2p^6$", "$3s^2$", "$3p^3$"],
                },
                {
                    "label": "Refine",
                    "type": "interactive",
                    "instruction": "How many unpaired electrons are in the 3p subshell?",
                    "explanation": "By Hund's rule, the three $3p$ electrons each occupy a separate orbital singly.",
                    "skillUsed": "Draw orbital notation diagrams",
                    "correctAnswer": "3",
                },
                {
                    "label": "Final Answer",
                    "type": "interactive",
                    "instruction": "State the complete electron configuration.",
                    "explanation": "Combine the ordered subshells into a single notation string.",
                    "skillUsed": "Write full electron configurations",
                    "correctAnswer": "1s2 2s2 2p6 3s2 3p3",
                },
            ],
        },
    ),
    # ── 21. Architect: noble gas config — Level 1 (full worked example) ────────
    (
        "unit-electrons",
        3,
        "medium",
        "architect",
        {
            "title": "Noble Gas Configuration and Valence Electrons for Selenium",
            "statement": (
                "A student in AP Chemistry is reviewing electron configurations for main-group elements "
                "and wants to write a noble gas abbreviation for selenium, $\\mathrm{Se}$.\n\n"
                "Selenium has atomic number $34$. The preceding noble gas is argon, $\\mathrm{Ar}$, "
                "with atomic number $18$. After $[\\mathrm{Ar}]$, the remaining electrons fill as "
                "$4s^{2} 3d^{10} 4p^{4}$.\n\n"
                "Write the noble gas abbreviated electron configuration for selenium and determine "
                "how many valence electrons selenium has."
            ),
            "steps": [
                {
                    "label": "Inventory / Rules",
                    "type": "multi_input",
                    "instruction": "Identify the core and outer subshells.",
                    "explanation": "Use the preceding noble gas as the core, then list filled subshells after it.",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                    "inputFields": [
                        {"label": "Noble gas core", "value": "$[\\mathrm{Ar}]$", "unit": ""},
                        {"label": "Outer subshells after core", "value": "$4s^{2} 3d^{10} 4p^{4}$", "unit": ""},
                    ],
                },
                {
                    "label": "Draft",
                    "type": "drag_drop",
                    "instruction": "Assemble the abbreviated configuration.",
                    "explanation": "Place the noble gas core first, followed by the remaining filled subshells in Aufbau order.",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                    "equationParts": [
                        "$[\\mathrm{Ar}]$",
                        "$4s^{2}$",
                        "$3d^{10}$",
                        "$4p^{4}$",
                    ],
                },
                {
                    "label": "Refine",
                    "type": "interactive",
                    "instruction": "Count the valence electrons.",
                    "explanation": "Valence electrons occupy the highest principal level $n=4$: $4s^{2}$ and $4p^{4}$ contribute $2+4=6$.",
                    "skillUsed": "Identify valence electrons from configurations",
                    "correctAnswer": "6",
                },
                {
                    "label": "Final Answer",
                    "type": "multi_input",
                    "instruction": "State both final results.",
                    "explanation": "Combine the abbreviated configuration and the valence electron count.",
                    "skillUsed": "Identify valence electrons from configurations",
                    "inputFields": [
                        {"label": "Abbreviated configuration", "value": "[Ar] 4s2 3d10 4p4", "unit": ""},
                        {"label": "Valence electrons", "value": "6", "unit": ""},
                    ],
                },
            ],
        },
    ),
    # ── 21b. Architect: noble gas config — Level 2 (faded, selenium) ─────────
    (
        "unit-electrons",
        3,
        "medium",
        "architect",
        {
            "title": "Abbreviated Configuration for Selenium",
            "statement": (
                "An AP Chemistry student is reviewing electron configurations and wants a fast way "
                "to represent selenium using noble gas notation.\n\n"
                "Selenium has atomic number $34$. The previous noble gas is argon, $\\mathrm{Ar}$, "
                "with $18$ electrons.\n\n"
                "Write the noble gas abbreviated electron configuration for selenium and determine "
                "the number of valence electrons."
            ),
            "steps": [
                {
                    "label": "Inventory / Rules",
                    "type": "multi_input",
                    "instruction": "Identify the core noble gas and remaining electrons.",
                    "explanation": "Subtract core electrons: $34 - 18 = 16$ electrons beyond $\\mathrm{Ar}$.",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                    "inputFields": [
                        {"label": "Core noble gas", "value": "$\\mathrm{Ar}$", "unit": ""},
                        {"label": "Remaining electrons", "value": "$16$", "unit": "electrons"},
                    ],
                },
                {
                    "label": "Draft",
                    "type": "drag_drop",
                    "instruction": "List the subshell filling after the noble gas core.",
                    "explanation": "After $[\\mathrm{Ar}]$, fill $4s$, then $3d$, then $4p$ to place $16$ electrons.",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                    "equationParts": [
                        "$[\\mathrm{Ar}]$",
                        "$4s^{2}$",
                        "$3d^{10}$",
                        "$4p^{4}$",
                    ],
                },
                {
                    "label": "Refine",
                    "type": "interactive",
                    "instruction": "Enter the abbreviated electron configuration.",
                    "explanation": "Combine the noble gas core with filled outer subshells in order.",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                    "correctAnswer": "[Ar] 4s2 3d10 4p4",
                },
                {
                    "label": "Final Answer",
                    "type": "interactive",
                    "instruction": "State the number of valence electrons.",
                    "explanation": "For selenium, the highest principal level is $n=4$: $4s^{2} 4p^{4}$, totaling $6$.",
                    "skillUsed": "Identify valence electrons from configurations",
                    "correctAnswer": "6",
                },
            ],
        },
    ),
    # ── 22. Architect: electron configuration — Level 2 (Faded) ─────────────
    (
        "unit-electrons",
        3,
        "medium",
        "architect",
        {
            "title": "Noble Gas Configuration for Calcium",
            "statement": (
                "An AP Chemistry student is reviewing electron configurations and needs a fast way to "
                "represent calcium, $\\mathrm{Ca}$, using noble gas notation.\n\n"
                "Calcium has atomic number $20$. The previous noble gas is argon, $\\mathrm{Ar}$, with $18$ electrons.\n\n"
                "Write the noble gas abbreviated electron configuration for calcium and determine its number of valence electrons."
            ),
            "steps": [
                {
                    "label": "Inventory / Rules",
                    "type": "interactive",
                    "instruction": "Identify the core noble gas and remaining electrons.",
                    "explanation": "Subtract the core electrons from the total: $20 - 18 = 2$ electrons beyond $\\mathrm{Ar}$.",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                    "correctAnswer": "Core: [Ar], Remaining: 2",
                },
                {
                    "label": "Draft",
                    "type": "drag_drop",
                    "instruction": "Assemble the subshell filling after the core.",
                    "explanation": "After $[\\mathrm{Ar}]$, the next $2$ electrons fill the $4s$ subshell.",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                    "equationParts": [
                        "$[\\mathrm{Ar}]$",
                        "$4s^2$",
                    ],
                },
                {
                    "label": "Refine",
                    "type": "interactive",
                    "instruction": "Enter the abbreviated electron configuration.",
                    "explanation": "Combine the noble gas core with the filled outer subshells.",
                    "skillUsed": "Write noble gas abbreviated electron configurations",
                    "correctAnswer": "[Ar] 4s2",
                },
                {
                    "label": "Final Answer",
                    "type": "interactive",
                    "instruction": "State the number of valence electrons.",
                    "explanation": "For calcium, the highest principal level is $n=4$: $4s^2$, totaling $2$ valence electrons.",
                    "skillUsed": "Identify valence electrons from configurations",
                    "correctAnswer": "2",
                },
            ],
        },
    ),
    # ── 23. Solver: Arrhenius — activation energy from two rate constants ─────
    (
        "ap-unit-5",
        6,
        "medium",
        "solver",
        {
            "title": "Activation Energy from Two Rate Constants",
            "statement": (
                "A student investigates the decomposition of a gaseous reactant and measures the rate constant "
                "at two different temperatures.\n\n"
                "At $298\\,\\text{K}$, the rate constant is $k_1 = 2.50 \\times 10^{-3}\\,\\text{s}^{-1}$. "
                "At $315\\,\\text{K}$, the rate constant is $k_2 = 8.20 \\times 10^{-3}\\,\\text{s}^{-1}$.\n\n"
                "Given that $R = 8.314\\,\\text{J}\\,\\text{mol}^{-1}\\,\\text{K}^{-1}$, calculate the activation energy, "
                "$E_a$, for this reaction.\n\n"
                "*Hint: Use the two-point form of the Arrhenius equation.*"
            ),
            "steps": [
                {
                    "label": "Equation",
                    "type": "drag_drop",
                    "instruction": "Arrange the two-point Arrhenius equation.",
                    "explanation": (
                        "Use the logarithmic form of the Arrhenius equation to relate two rate constants "
                        "at different temperatures."
                    ),
                    "equationParts": [
                        "$\\ln\\left(\\frac{k_2}{k_1}\\right)$",
                        "=",
                        "$\\frac{E_a}{R}$",
                        "$\\left(\\frac{1}{T_1} - \\frac{1}{T_2}\\right)$",
                    ],
                    "skillUsed": "Apply the Arrhenius equation to relate rate constants and temperature",
                },
                {
                    "label": "Knowns",
                    "type": "multi_input",
                    "instruction": "Identify the given values.",
                    "explanation": "List both rate constants, both temperatures, and the gas constant $R$.",
                    "inputFields": [
                        {"label": "$k_1$", "value": "$2.50 \\times 10^{-3}$", "unit": "$\\text{s}^{-1}$"},
                        {"label": "$k_2$", "value": "$8.20 \\times 10^{-3}$", "unit": "$\\text{s}^{-1}$"},
                        {"label": "$T_1$", "value": "$298$", "unit": "$\\text{K}$"},
                        {"label": "$T_2$", "value": "$315$", "unit": "$\\text{K}$"},
                        {
                            "label": "$R$",
                            "value": "$8.314$",
                            "unit": "$\\text{J}\\,\\text{mol}^{-1}\\,\\text{K}^{-1}$",
                        },
                    ],
                    "skillUsed": "Extract known values from a kinetics problem",
                },
                {
                    "label": "Substitute",
                    "type": "interactive",
                    "instruction": "Substitute the values into the Arrhenius equation.",
                    "explanation": (
                        "$\\ln\\left(\\frac{8.20 \\times 10^{-3}}{2.50 \\times 10^{-3}}\\right) = "
                        "\\frac{E_a}{8.314} \\left(\\frac{1}{298} - \\frac{1}{315}\\right)$."
                    ),
                    "correctAnswer": (
                        "$\\ln\\left(\\frac{8.20 \\times 10^{-3}}{2.50 \\times 10^{-3}}\\right) = "
                        "\\frac{E_a}{8.314} \\left(\\frac{1}{298} - \\frac{1}{315}\\right)$"
                    ),
                    "skillUsed": "Substitute values into the Arrhenius equation",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Solve for the activation energy.",
                    "explanation": (
                        "Rearranging gives:\n\n"
                        "$E_a = \\frac{8.314 \\times \\ln\\left(\\frac{8.20 \\times 10^{-3}}{2.50 \\times 10^{-3}}\\right)}"
                        "{\\left(\\frac{1}{298} - \\frac{1}{315}\\right)} "
                        "\\approx 5.44 \\times 10^{4}\\,\\text{J/mol}$."
                    ),
                    "correctAnswer": "$5.44 \\times 10^{4}\\,\\text{J/mol}$",
                    "skillUsed": "Calculate activation energy using the Arrhenius equation",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Express the activation energy in kJ/mol.",
                    "explanation": (
                        "Converting to kilojoules:\n\n$E_a = 54.4\\,\\text{kJ/mol}$ (3 significant figures)."
                    ),
                    "correctAnswer": "$54.4\\,\\text{kJ/mol}$",
                    "skillUsed": "Convert units and report with correct significant figures",
                },
            ],
        },
    ),
    # ── 24. Solver: Arrhenius — variant 2 (different temperatures / rate constants) ─
    (
        "ap-unit-5",
        6,
        "medium",
        "solver",
        {
            "title": "Determining Activation Energy from Temperature Change",
            "statement": (
                "A chemical reaction has a rate constant of $k_1 = 1.20 \\times 10^{-4}\\,\\text{s}^{-1}$ at "
                "$285\\,\\text{K}$. When the temperature is increased to $305\\,\\text{K}$, the rate constant becomes "
                "$k_2 = 4.80 \\times 10^{-4}\\,\\text{s}^{-1}$.\n\n"
                "Given that $R = 8.314\\,\\text{J}\\,\\text{mol}^{-1}\\,\\text{K}^{-1}$, calculate the activation energy, "
                "$E_a$, for this reaction.\n\n"
                "*Hint: Start from the two-point Arrhenius equation.*"
            ),
            "steps": [
                {
                    "label": "Equation",
                    "type": "drag_drop",
                    "instruction": "Arrange the two-point Arrhenius equation.",
                    "explanation": (
                        "Use the logarithmic form to compare rate constants at two temperatures."
                    ),
                    "equationParts": [
                        "$\\ln\\left(\\frac{k_2}{k_1}\\right)$",
                        "=",
                        "$\\frac{E_a}{R}$",
                        "$\\left(\\frac{1}{T_1} - \\frac{1}{T_2}\\right)$",
                    ],
                    "skillUsed": "Apply the Arrhenius equation to relate rate constants and temperature",
                },
                {
                    "label": "Knowns",
                    "type": "multi_input",
                    "instruction": "Identify the given values.",
                    "explanation": "List both rate constants, both temperatures, and the gas constant $R$.",
                    "inputFields": [
                        {"label": "$k_1$", "value": "$1.20 \\times 10^{-4}$", "unit": "$\\text{s}^{-1}$"},
                        {"label": "$k_2$", "value": "$4.80 \\times 10^{-4}$", "unit": "$\\text{s}^{-1}$"},
                        {"label": "$T_1$", "value": "$285$", "unit": "$\\text{K}$"},
                        {"label": "$T_2$", "value": "$305$", "unit": "$\\text{K}$"},
                        {
                            "label": "$R$",
                            "value": "$8.314$",
                            "unit": "$\\text{J}\\,\\text{mol}^{-1}\\,\\text{K}^{-1}$",
                        },
                    ],
                    "skillUsed": "Extract known values from a kinetics problem",
                },
                {
                    "label": "Substitute",
                    "type": "interactive",
                    "instruction": "Substitute the values into the equation.",
                    "explanation": (
                        "$\\ln\\left(\\frac{4.80 \\times 10^{-4}}{1.20 \\times 10^{-4}}\\right) = "
                        "\\frac{E_a}{8.314} \\left(\\frac{1}{285} - \\frac{1}{305}\\right)$."
                    ),
                    "correctAnswer": (
                        "$\\ln\\left(\\frac{4.80 \\times 10^{-4}}{1.20 \\times 10^{-4}}\\right) = "
                        "\\frac{E_a}{8.314} \\left(\\frac{1}{285} - \\frac{1}{305}\\right)$"
                    ),
                    "skillUsed": "Substitute values into the Arrhenius equation",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Solve for the activation energy.",
                    "explanation": (
                        "First compute the ratio:\n\n"
                        "$\\frac{k_2}{k_1} = 4.00 \\Rightarrow \\ln(4.00) \\approx 1.386$\n\n"
                        "Then:\n\n"
                        "$E_a = \\frac{8.314 \\times 1.386}{\\left(\\frac{1}{285} - \\frac{1}{305}\\right)} "
                        "\\approx 7.20 \\times 10^{4}\\,\\text{J/mol}$."
                    ),
                    "correctAnswer": "$7.20 \\times 10^{4}\\,\\text{J/mol}$",
                    "skillUsed": "Calculate activation energy using logarithms and algebra",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Express the activation energy in kJ/mol.",
                    "explanation": (
                        "Convert to kilojoules:\n\n$E_a = 72.0\\,\\text{kJ/mol}$ (3 significant figures)."
                    ),
                    "correctAnswer": "$72.0\\,\\text{kJ/mol}$",
                    "skillUsed": "Convert units and report with correct significant figures",
                },
            ],
        },
    ),
    # ── 13. Detective: initial rates (worked) with multi-input conclusion ───
    (
        "ap-unit-5",
        1,
        "medium",
        "detective",
        {
            "title": "Initial Rates for a Two-Reactant Reaction",
            "statement": (
                "A reaction between aqueous reactants $\\text{X}$ and $\\text{Y}$ follows "
                "$\\text{X} + \\text{Y} \\rightarrow \\text{products}$. A student measures initial rates at "
                "the same temperature to determine the rate law.\n\n"
                "Experiment 1: $[\\text{X}] = 0.15 \\text{ M}$, $[\\text{Y}] = 0.10 \\text{ M}$, "
                "rate $= 3.0 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 2: $[\\text{X}] = 0.30 \\text{ M}$, $[\\text{Y}] = 0.10 \\text{ M}$, "
                "rate $= 6.0 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 3: $[\\text{X}] = 0.15 \\text{ M}$, $[\\text{Y}] = 0.20 \\text{ M}$, "
                "rate $= 1.2 \\times 10^{-2} \\text{ M/s}$.\n\n"
                "Use the data to determine the order in $\\text{X}$, the order in $\\text{Y}$, "
                "and the overall reaction order."
            ),
            "steps": [
                {
                    "label": "Data Extraction",
                    "type": "multi_input",
                    "instruction": "Extract the experiment values.",
                    "explanation": "Record each trial's concentrations and measured initial rate.",
                    "inputFields": [
                        {
                            "label": "Experiment 1",
                            "value": "$[\\text{X}] = 0.15$, $[\\text{Y}] = 0.10$, rate $= 3.0 \\times 10^{-3}$",
                            "unit": "",
                        },
                        {
                            "label": "Experiment 2",
                            "value": "$[\\text{X}] = 0.30$, $[\\text{Y}] = 0.10$, rate $= 6.0 \\times 10^{-3}$",
                            "unit": "",
                        },
                        {
                            "label": "Experiment 3",
                            "value": "$[\\text{X}] = 0.15$, $[\\text{Y}] = 0.20$, rate $= 1.2 \\times 10^{-2}$",
                            "unit": "",
                        },
                    ],
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Feature ID",
                    "type": "interactive",
                    "instruction": "Identify the order in X.",
                    "explanation": "From Exp 1 to 2, $[\\text{X}]$ doubles and rate doubles, so exponent is 1.",
                    "correctAnswer": "1",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Apply Concept",
                    "type": "interactive",
                    "instruction": "Identify the order in Y.",
                    "explanation": "From Exp 1 to 3, $[\\text{Y}]$ doubles and rate quadruples, so exponent is 2.",
                    "correctAnswer": "2",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Conclusion",
                    "type": "multi_input",
                    "instruction": "State the rate law and overall order.",
                    "explanation": "Add exponents: $1+2=3$. Report both the symbolic law and overall order.",
                    "inputFields": [
                        {"label": "Rate Law", "value": "k[X][Y]^2", "unit": ""},
                        {"label": "Overall Order", "value": "3", "unit": ""},
                    ],
                    "skillUsed": "Determine overall reaction order",
                },
            ],
        },
    ),
    # ── 14. Detective: initial rates (faded) with multi-input conclusion ────
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
            "steps": [
                {
                    "label": "Data Extraction",
                    "type": "multi_input",
                    "instruction": "Extract the experiment values.",
                    "explanation": "Record each trial's concentrations and measured initial rate.",
                    "inputFields": [
                        {
                            "label": "Experiment 1",
                            "value": "$[\\text{NO}] = 0.10$, $[\\text{H}_2] = 0.10$, rate $= 1.2 \\times 10^{-3}$",
                            "unit": "",
                        },
                        {
                            "label": "Experiment 2",
                            "value": "$[\\text{NO}] = 0.20$, $[\\text{H}_2] = 0.10$, rate $= 4.8 \\times 10^{-3}$",
                            "unit": "",
                        },
                        {
                            "label": "Experiment 3",
                            "value": "$[\\text{NO}] = 0.20$, $[\\text{H}_2] = 0.20$, rate $= 9.6 \\times 10^{-3}$",
                            "unit": "",
                        },
                    ],
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Feature ID",
                    "type": "interactive",
                    "instruction": "Identify the order with respect to NO.",
                    "explanation": "From Exp 1 to 2, doubling $[\\text{NO}]$ quadruples rate, so exponent is 2.",
                    "correctAnswer": "2",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Apply Concept",
                    "type": "interactive",
                    "instruction": "Identify the order with respect to H2.",
                    "explanation": "From Exp 2 to 3, doubling $[\\text{H}_2]$ doubles rate, so exponent is 1.",
                    "correctAnswer": "1",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Conclusion",
                    "type": "multi_input",
                    "instruction": "State the rate law and overall order.",
                    "explanation": "Add exponents: $2+1=3$. Report the law and the total order.",
                    "inputFields": [
                        {"label": "Rate Law", "value": "k[NO]^2[H2]", "unit": ""},
                        {"label": "Overall Order", "value": "3", "unit": ""},
                    ],
                    "skillUsed": "Determine overall reaction order",
                },
            ],
        },
    ),
    # ── 15. Detective: initial rates (P,Q) second-second → fourth order ────
    (
        "ap-unit-5",
        1,
        "medium",
        "detective",
        {
            "title": "Determining Reaction Orders from Initial Rates",
            "statement": (
                "A chemist studies the reaction of a colored compound $\\text{P}$ with a catalyst "
                "$\\text{Q}$ in aqueous solution: $\\text{P} + \\text{Q} \\rightarrow \\text{colorless product}$. "
                "They measure initial rates at the same temperature.\n\n"
                "Experiment 1: $[\\text{P}] = 0.10 \\text{ M}$, $[\\text{Q}] = 0.05 \\text{ M}$, "
                "rate $= 1.5 \\times 10^{-4} \\text{ M/s}$.\n\n"
                "Experiment 2: $[\\text{P}] = 0.20 \\text{ M}$, $[\\text{Q}] = 0.05 \\text{ M}$, "
                "rate $= 6.0 \\times 10^{-4} \\text{ M/s}$.\n\n"
                "Experiment 3: $[\\text{P}] = 0.10 \\text{ M}$, $[\\text{Q}] = 0.10 \\text{ M}$, "
                "rate $= 6.0 \\times 10^{-4} \\text{ M/s}$.\n\n"
                "Use this data to determine the order with respect to $\\text{P}$, the order with "
                "respect to $\\text{Q}$, and the overall reaction order."
            ),
            "steps": [
                {
                    "label": "Data Extraction",
                    "type": "multi_input",
                    "instruction": "Compare Exp 1 and 2: determine [P] and rate factors.",
                    "explanation": "Divide corresponding values between experiments to find each ratio.",
                    "inputFields": [
                        {"label": "[P] ratio (Exp 2 / Exp 1)", "value": "2", "unit": ""},
                        {"label": "Rate ratio (Exp 2 / Exp 1)", "value": "4", "unit": ""},
                    ],
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Feature ID",
                    "type": "interactive",
                    "instruction": "Determine the reaction order with respect to P.",
                    "explanation": "Doubling [P] at constant [Q] quadruples rate, so $2^n=4$ and $n=2$.",
                    "correctAnswer": "2",
                    "skillUsed": "Determine individual reaction orders",
                },
                {
                    "label": "Apply Concept",
                    "type": "interactive",
                    "instruction": "Determine the reaction order with respect to Q.",
                    "explanation": "From Exp 1 to 3, [Q] doubles while [P] is fixed and rate quadruples, so order is 2.",
                    "correctAnswer": "2",
                    "skillUsed": "Write rate law expressions from experimental data",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Calculate the overall reaction order.",
                    "explanation": "Overall order is the sum of exponents: $2+2=4$.",
                    "correctAnswer": "4",
                    "skillUsed": "Determine overall reaction order",
                },
            ],
        },
    ),
    # ── 16. Recipe: Faraday's Law — silver plating mass (Level 1) ────────────
    (
        "ap-unit-9",
        6,
        "medium",
        "recipe",
        {
            "title": "Silver Plating from Electrolysis Time",
            "statement": (
                "A jeweler uses electrolysis to plate a metal pendant with silver. "
                "A constant current of $2.85 \\text{ A}$ is passed through a solution containing "
                "$\\text{Ag}^+$ ions for $18.0 \\text{ min}$.\n\n"
                "Use $F = 96485 \\text{ C/mol}$ and the molar mass of silver, $M = 107.87 \\text{ g/mol}$. "
                "The reduction is $\\text{Ag}^+ + \\text{e}^- \\rightarrow \\text{Ag}$, "
                "so $n = 1$ electron per silver atom.\n\n"
                "Calculate the mass of silver deposited on the pendant in grams."
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "multi_input",
                    "instruction": "Identify the given values for Faraday's Law.",
                    "explanation": "Extract $I$, $t$, $M$, and $n$ from the problem before any calculation.",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                    "inputFields": [
                        {"label": "$I$", "value": "2.85", "unit": "A"},
                        {"label": "$t$", "value": "18.0", "unit": "min"},
                        {"label": "$M$", "value": "107.87", "unit": "g/mol"},
                        {"label": "$n$", "value": "1", "unit": "e⁻"},
                    ],
                },
                {
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "instruction": "Convert time into seconds.",
                    "explanation": "Use $18.0 \\text{ min} \\times 60 = 1080 \\text{ s}$ before applying $Q = It$.",
                    "skillUsed": "Apply Faraday's constant (F = 96,485 C/mol)",
                    "correctAnswer": "1080 s",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Set up the mass calculation expression.",
                    "explanation": "Apply $m = \\frac{M \\cdot I \\cdot t}{n \\cdot F} = \\frac{107.87 \\times 2.85 \\times 1080}{1 \\times 96485}$.",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                    "correctAnswer": "(107.87 * 2.85 * 1080) / (1 * 96485)",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Compute the unrounded deposited mass.",
                    "explanation": "Evaluating gives $\\frac{332023.96}{96485} = 3.4411 \\text{ g}$.",
                    "skillUsed": "Apply Faraday's constant (F = 96,485 C/mol)",
                    "correctAnswer": "3.4411",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Report the final mass with sig figs.",
                    "explanation": "Round to 3 sig figs: both $2.85 \\text{ A}$ and $18.0 \\text{ min}$ have 3 significant figures.",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                    "correctAnswer": "3.44 g",
                },
            ],
        },
    ),
    # ── 17. Solver: ΔG°/K/E° interconversion (Level 2) ──────────────────────
    (
        "ap-unit-9",
        2,
        "medium",
        "solver",
        {
            "title": "Finding the Equilibrium Constant from Standard Cell Potential",
            "statement": (
                "An AP Chemistry student is analyzing a galvanic cell at $25.0^\\circ\\text{C}$ "
                "and wants to connect electrochemistry to thermodynamics.\n\n"
                "The balanced redox reaction transfers $n = 2$ electrons, and the standard cell potential "
                "is $E^\\circ = 0.34 \\text{ V}$. Use $F = 96485 \\text{ C/mol}$, "
                "$R = 8.314 \\text{ J/(mol} \\cdot \\text{K)}$, and $T = 298 \\text{ K}$.\n\n"
                "Calculate the standard free energy change, $\\Delta G^\\circ$, and then determine "
                "the equilibrium constant, $K$, for the reaction."
            ),
            "steps": [
                {
                    "label": "Equation",
                    "type": "drag_drop",
                    "instruction": "Identify the needed equations.",
                    "explanation": "Use $\\Delta G^\\circ = -nFE^\\circ$ and $\\Delta G^\\circ = -RT\\ln K$.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "equationParts": [
                        "$\\Delta G^\\circ$",
                        "=",
                        "$-$",
                        "$n$",
                        "$F$",
                        "$E^\\circ$",
                    ],
                },
                {
                    "label": "Knowns",
                    "type": "multi_input",
                    "instruction": "List the given values.",
                    "explanation": "Identify all known variables before substitution.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "inputFields": [
                        {"label": "Electrons transferred", "value": "$2$", "unit": ""},
                        {"label": "Standard cell potential", "value": "$0.34$", "unit": "V"},
                        {"label": "Faraday constant", "value": "$96485$", "unit": "$\\text{C/mol}$"},
                        {"label": "Gas constant", "value": "$8.314$", "unit": "$\\text{J/(mol}\\cdot\\text{K)}$"},
                        {"label": "Temperature", "value": "$298$", "unit": "K"},
                    ],
                },
                {
                    "label": "Substitute",
                    "type": "interactive",
                    "instruction": "Substitute into the $\\Delta G^\\circ$ formula.",
                    "explanation": "Insert $n$, $F$, and $E^\\circ$ into $\\Delta G^\\circ = -nFE^\\circ$.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "correctAnswer": "-2 * 96485 * 0.34",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Calculate $K$ from $\\Delta G^\\circ$.",
                    "explanation": "Find $\\Delta G^\\circ = -65609.8 \\text{ J/mol}$, then $\\ln K = \\frac{-\\Delta G^\\circ}{RT} = 26.47$.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "correctAnswer": "$3.15 \\times 10^{11}$",
                },
                {
                    "label": "Answer",
                    "type": "multi_input",
                    "instruction": "State both final results.",
                    "explanation": "Positive $E^\\circ$ gives negative $\\Delta G^\\circ$ and large $K > 1$.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "inputFields": [
                        {"label": "$\\Delta G^\\circ$", "value": "$-65.6 \\text{ kJ/mol}$", "unit": ""},
                        {"label": "$K$", "value": "$3.15 \\times 10^{11}$", "unit": ""},
                    ],
                },
            ],
        },
    ),
    # ── 18. Recipe: Faraday's Law — H₂ from water electrolysis (variant) ───────
    (
        "ap-unit-9",
        6,
        "medium",
        "recipe",
        {
            "title": "Hydrogen Gas Generation in Water Electrolysis",
            "statement": (
                "A student performs electrolysis of water to produce hydrogen gas at the cathode. "
                "A steady current of $1.60 \\text{ A}$ is applied for $25.0 \\text{ min}$.\n\n"
                "The half-reaction at the cathode is:\n"
                "$2\\text{H}_2\\text{O} + 2\\text{e}^- \\rightarrow \\text{H}_2 + 2\\text{OH}^-$\n\n"
                "Use $F = 96485 \\text{ C/mol}$ and the molar mass of hydrogen gas, "
                "$M = 2.016 \\text{ g/mol}$. Note that $n = 2$ electrons are required per mole of $\\text{H}_2$.\n\n"
                "Calculate the mass of hydrogen gas produced."
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "multi_input",
                    "instruction": "Identify the electrolysis variables.",
                    "explanation": "Here, you're solving for gas produced, not metal deposited — but the same Faraday structure applies.",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                    "inputFields": [
                        {"label": "$I$", "value": "1.60", "unit": "A"},
                        {"label": "$t$", "value": "25.0", "unit": "min"},
                        {"label": "$M$", "value": "2.016", "unit": "g/mol"},
                        {"label": "$n$", "value": "2", "unit": "e⁻"},
                    ],
                },
                {
                    "label": "Conversion Factors",
                    "type": "interactive",
                    "instruction": "Convert time to seconds.",
                    "explanation": "Faraday's Law requires charge in coulombs, so convert minutes → seconds first.",
                    "skillUsed": "Apply Faraday's constant (F = 96,485 C/mol)",
                    "correctAnswer": "1500 s",
                },
                {
                    "label": "Conceptual Setup",
                    "type": "interactive",
                    "instruction": "Write the full reasoning pathway.",
                    "explanation": "Instead of jumping to the formula, think: current → charge → moles e⁻ → moles H₂ → mass.",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                    "correctAnswer": "I*t → Q → mol e⁻ → mol H2 → g H2",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "interactive",
                    "instruction": "Construct the expression for mass.",
                    "explanation": "Use $m = \\frac{M \\cdot I \\cdot t}{n \\cdot F}$ but now with $n=2$.",
                    "skillUsed": "Apply Faraday's constant (F = 96,485 C/mol)",
                    "correctAnswer": "(2.016 * 1.60 * 1500) / (2 * 96485)",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Report final mass with correct sig figs.",
                    "explanation": "Be careful — small molar mass + division by 2 → very small mass.",
                    "skillUsed": "Calculate mass deposited or volume of gas produced during electrolysis",
                    "correctAnswer": "0.0251 g",
                },
            ],
        },
    ),
    # ── 19. Solver: E° from K (variant of ΔG°/K/E° lesson) ─────────────────────
    (
        "ap-unit-9",
        2,
        "medium",
        "solver",
        {
            "title": "Determining Cell Potential from Equilibrium Constant",
            "statement": (
                "A redox reaction at $25^\\circ\\text{C}$ has an experimentally determined "
                "equilibrium constant of $K = 4.5 \\times 10^{-6}$.\n\n"
                "The reaction involves the transfer of $n = 1$ electron.\n\n"
                "Use $R = 8.314 \\text{ J/(mol}\\cdot\\text{K)}$, $T = 298 \\text{ K}$, "
                "and $F = 96485 \\text{ C/mol}$.\n\n"
                "Calculate the standard cell potential $E^\\circ$ and determine whether the reaction "
                "is spontaneous under standard conditions."
            ),
            "steps": [
                {
                    "label": "Equation",
                    "type": "drag_drop",
                    "instruction": "Select the correct relationship linking $K$ and $E^\\circ$.",
                    "explanation": "You must combine $\\Delta G^\\circ = -RT\\ln K$ and $\\Delta G^\\circ = -nFE^\\circ$.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "equationParts": [
                        "$E^\\circ$",
                        "=",
                        "$\\frac{RT}{nF}$",
                        "$\\ln K$",
                    ],
                },
                {
                    "label": "Knowns",
                    "type": "multi_input",
                    "instruction": "Identify all given values.",
                    "explanation": "Unlike typical problems, you're starting from $K$, not $E^\\circ$.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "inputFields": [
                        {"label": "$K$", "value": "$4.5 \\times 10^{-6}$", "unit": ""},
                        {"label": "$n$", "value": "$1$", "unit": ""},
                        {"label": "$R$", "value": "$8.314$", "unit": "$\\text{J/(mol·K)}$"},
                        {"label": "$T$", "value": "$298$", "unit": "K"},
                        {"label": "$F$", "value": "$96485$", "unit": "$\\text{C/mol}$"},
                    ],
                },
                {
                    "label": "Transform",
                    "type": "interactive",
                    "instruction": "Write the expression for $E^\\circ$.",
                    "explanation": "Rearrange: $E^\\circ = \\frac{RT}{nF} \\ln K$.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "correctAnswer": "(8.314 * 298 / (1 * 96485)) * ln(4.5e-6)",
                },
                {
                    "label": "Interpretation Before Calculation",
                    "type": "interactive",
                    "instruction": "Predict the sign of $E^\\circ$.",
                    "explanation": "Since $K < 1$, $\\ln K$ is negative → $E^\\circ$ must be negative.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "correctAnswer": "Negative",
                },
                {
                    "label": "Answer",
                    "type": "multi_input",
                    "instruction": "State the final result and conclusion.",
                    "explanation": "A negative $E^\\circ$ indicates a non-spontaneous reaction under standard conditions.",
                    "skillUsed": "Interconvert ΔG°, K, and E° for electrochemical and thermodynamic problems",
                    "inputFields": [
                        {"label": "$E^\\circ$", "value": "$-0.32 \\text{ V}$", "unit": ""},
                        {"label": "Spontaneity", "value": "Non-spontaneous", "unit": ""},
                    ],
                },
            ],
        },
    ),
    # ── 20. Recipe: Molar Mass (2-Step) — mass → molecules of Cl₂ ─────────────
    (
        "unit-mole",
        2,
        "medium",
        "recipe",
        {
            "title": "Mass to Particles of Chlorine Gas",
            "statement": (
                "A sealed container holds $35.5 \\text{ g}$ of chlorine gas, $\\mathrm{Cl_2}$.\n\n"
                "Using Avogadro's number, $6.022 \\times 10^{23}$ particles per mole, "
                "calculate the number of molecules of $\\mathrm{Cl_2}$ present.\n\n"
                "Note: Chlorine exists as a diatomic molecule."
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "multi_input",
                    "instruction": "Identify given and target quantities.",
                    "explanation": "You are converting mass → particles.",
                    "skillUsed": "Convert between grams, moles, and particles in two steps",
                    "inputFields": [
                        {"label": "Given mass", "value": "35.5", "unit": "g"},
                        {"label": "Target", "value": "molecules", "unit": ""},
                        {"label": "Compound", "value": "$\\mathrm{Cl_2}$", "unit": ""},
                    ],
                },
                {
                    "label": "Molar Mass",
                    "type": "interactive",
                    "instruction": "Determine molar mass of $\\mathrm{Cl_2}$.",
                    "explanation": "Each Cl is 35.45 g/mol → multiply by 2.",
                    "skillUsed": "Calculate molar mass of compounds",
                    "correctAnswer": "70.90 g/mol",
                },
                {
                    "label": "Step 1: Mass → Moles",
                    "type": "interactive",
                    "instruction": "Convert grams to moles.",
                    "explanation": "Divide by molar mass.",
                    "skillUsed": "Convert between grams and moles",
                    "correctAnswer": "35.5 / 70.90",
                },
                {
                    "label": "Step 2: Moles → Particles",
                    "type": "interactive",
                    "instruction": "Convert moles to molecules.",
                    "explanation": "Multiply by Avogadro's number.",
                    "skillUsed": "Convert between moles and particles",
                    "correctAnswer": "0.500 * 6.022e23",
                },
                {
                    "label": "Final Answer + Insight",
                    "type": "interactive",
                    "instruction": "State the number of molecules.",
                    "explanation": (
                        "≈ $3.01 \\times 10^{23}$ molecules.\n"
                        "Insight: Half a mole always gives half of Avogadro's number."
                    ),
                    "skillUsed": "Convert between grams, moles, and particles in two steps",
                    "correctAnswer": "$3.01 \\times 10^{23}$ molecules",
                },
            ],
        },
    ),
    # ── 21. Recipe: Molar Mass (2-Step) — formula units → mass of O in Al₂O₃ ───
    (
        "unit-mole",
        2,
        "medium",
        "recipe",
        {
            "title": "Particles to Mass of Oxygen in a Compound",
            "statement": (
                "A sample contains $1.204 \\times 10^{24}$ formula units of aluminum oxide, "
                "$\\mathrm{Al_2O_3}$.\n\n"
                "Using Avogadro's number, $6.022 \\times 10^{23}$ formula units per mole, "
                "calculate the mass of oxygen present in the sample.\n\n"
                "Molar masses: Al = 26.98 g/mol, O = 16.00 g/mol."
            ),
            "steps": [
                {
                    "label": "Goal / Setup",
                    "type": "multi_input",
                    "instruction": "Identify what is given and what is required.",
                    "explanation": "You are not finding total mass — only the oxygen portion.",
                    "skillUsed": "Convert between grams, moles, and particles in two steps",
                    "inputFields": [
                        {"label": "Given", "value": "$1.204 \\times 10^{24}$", "unit": "formula units"},
                        {"label": "Target", "value": "mass of oxygen", "unit": "g"},
                        {"label": "Compound", "value": "$\\mathrm{Al_2O_3}$", "unit": ""},
                    ],
                },
                {
                    "label": "Conversion Plan",
                    "type": "interactive",
                    "instruction": "Determine the pathway.",
                    "explanation": "Particles → moles of compound → moles of oxygen → mass of oxygen.",
                    "skillUsed": "Stoichiometric relationships within compounds",
                    "correctAnswer": "formula units → mol Al2O3 → mol O → g O",
                },
                {
                    "label": "Step 1: Particles → Moles of Compound",
                    "type": "interactive",
                    "instruction": "Convert formula units to moles of $\\mathrm{Al_2O_3}$.",
                    "explanation": "Divide by Avogadro's number.",
                    "skillUsed": "Convert between particles and moles",
                    "correctAnswer": "$1.204 \\times 10^{24} / 6.022 \\times 10^{23}$",
                },
                {
                    "label": "Step 2: Moles of Compound → Moles of Oxygen",
                    "type": "interactive",
                    "instruction": "Use the formula to find moles of oxygen atoms.",
                    "explanation": "Each $\\mathrm{Al_2O_3}$ contains 3 oxygen atoms.",
                    "skillUsed": "Use subscripts to determine mole ratios",
                    "correctAnswer": "2.00 * 3",
                },
                {
                    "label": "Final Answer + Insight",
                    "type": "interactive",
                    "instruction": "Convert to grams and report the final mass.",
                    "explanation": (
                        "Moles O ≈ 6.00 mol → mass = $6.00 \\times 16.00 = 96.0$ g.\n"
                        "Insight: Always account for subscripts when targeting a specific element."
                    ),
                    "skillUsed": "Convert between moles and mass",
                    "correctAnswer": "96.0 g",
                },
            ],
        },
    ),
]