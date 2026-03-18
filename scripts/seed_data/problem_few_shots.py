"""Curated few-shot examples for problem generation.

Tuple layout: (unit_id, lesson_index, difficulty, blueprint, problem_dict)
The `blueprint` field maps to Lesson.blueprint from the DB.
Field names in step dicts use camelCase (API/JSON convention) to match LLM output exactly.

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
                    "type": "given",
                    "instruction": "Write the unbalanced skeleton equation.",
                    "explanation": "Al is aluminum; $\\mathrm{O_2}$ is diatomic oxygen; product is $\\mathrm{Al_2O_3}$.",
                    "correctAnswer": "$\\mathrm{Al} + \\mathrm{O_2} \\rightarrow \\mathrm{Al_2O_3}$",
                    "skillUsed": "Identify chemical rules/inventory",
                },
                {
                    "label": "Draft",
                    "type": "given",
                    "instruction": "Find the LCM for oxygen atoms on both sides.",
                    "explanation": "LCM of $2$ ($\\mathrm{O_2}$) and $3$ ($\\mathrm{Al_2O_3}$) is $2 \\times 3 = 6$.",
                    "correctAnswer": "6",
                    "skillUsed": "Draft initial symbolic representation",
                },
                {
                    "label": "Refine",
                    "type": "given",
                    "instruction": "Place coefficients to reach 6 oxygen atoms.",
                    "explanation": "Put $3$ in front of $\\mathrm{O_2}$ and $2$ in front of $\\mathrm{Al_2O_3}$.",
                    "correctAnswer": "$\\mathrm{Al} + 3\\mathrm{O_2} \\rightarrow 2\\mathrm{Al_2O_3}$",
                    "skillUsed": "Refine structure/coefficients",
                },
                {
                    "label": "Final Answer",
                    "type": "given",
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
                    "explanation": "Divide each percentage by $100$: $69.0 \\div 100 = 0.690$ and $31.0 \\div 100 = 0.310$.",
                    "labeledValues": [
                        {"variable": "Abundance 1", "value": "$0.690$", "unit": ""},
                        {"variable": "Abundance 2", "value": "$0.310$", "unit": ""},
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
                    "type": "given",
                    "instruction": "Calculate moles of $\\mathrm{H_2}$ available.",
                    "explanation": "$10.0 \\text{ g} \\div 2.02 \\text{ g/mol} = 4.95 \\text{ mol}$.",
                    "correctAnswer": "4.95",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "label": "Conversion Factors",
                    "type": "given",
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
                    "type": "variable_id",
                    "instruction": "Extract the given values with units.",
                    "explanation": None,
                    "labeledValues": [
                        {"variable": "$[A]_0$", "value": "$0.80$", "unit": "M"},
                        {"variable": "$k$", "value": "$0.020$", "unit": "M/s"},
                        {"variable": "$t$", "value": "$20$", "unit": "s"},
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
                    "explanation": "$\\mathrm{Ca} + 2(\\mathrm{Cl}) = 40.08 + 2(35.45) = 110.98 \\text{ g/mol}$.",
                    "correctAnswer": "$110.98 \\text{ g/mol}$",
                    "skillUsed": "Select conversion factors",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "given",
                    "instruction": "Set up the conversion to cancel moles.",
                    "explanation": "Multiply starting moles by molar mass so the $\\text{mol}$ units cancel out.",
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
                    "type": "given",
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given $2.50 \\text{ mol}$ into grams ($\\text{g}$).",
                    "correctAnswer": "2.50 mol to g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Conversion Factors",
                    "type": "given",
                    "instruction": "Find the molar mass of $\\mathrm{MgCl_2}$.",
                    "explanation": "$\\mathrm{Mg} + 2(\\mathrm{Cl}) = 24.31 + 2(35.45) = 95.21 \\text{ g/mol}$.",
                    "correctAnswer": "$95.21 \\text{ g/mol}$",
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
                    "explanation": "Compute the product: $2.50 \\times 95.21 = 238.025$.",
                    "correctAnswer": "238.025",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Answer",
                    "type": "given",
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
                    "type": "given",
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given $2.35 \\text{ mol}$ into grams ($\\text{g}$).",
                    "correctAnswer": "2.35 mol to g",
                    "skillUsed": "Convert between moles and grams (1-step)",
                },
                {
                    "label": "Conversion Factors",
                    "type": "given",
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
                    "type": "given",
                    "instruction": "Identify the system and the surroundings.",
                    "explanation": "The chemical process of the salt dissolving is the system; the solvent (water) is the surroundings.",
                    "correctAnswer": "System: $\\mathrm{NH_4NO_3}$, Surr: Water",
                    "skillUsed": "Identify governing concept",
                },
                {
                    "label": "Relation",
                    "type": "given",
                    "instruction": "Determine the direction of heat flow.",
                    "explanation": "Water temperature decreases, so thermal energy leaves the water and enters the dissolving salt.",
                    "correctAnswer": "From water to $\\mathrm{NH_4NO_3}$",
                    "skillUsed": "State chemical relationship",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "given",
                    "instruction": "Classify the process as endothermic or exothermic.",
                    "explanation": "Processes that absorb heat from their surroundings are classified as endothermic.",
                    "correctAnswer": "Endothermic",
                    "skillUsed": "Provide evidence/reasoning",
                },
                {
                    "label": "Conclusion",
                    "type": "given",
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
                    "type": "given",
                    "instruction": "Identify the system and surroundings.",
                    "explanation": "The dissolving salt is the system; the solution (water) acts as the surroundings.",
                    "correctAnswer": "System: NH4NO3, Surr: Water",
                    "skillUsed": "Define system and surroundings",
                },
                {
                    "label": "Relation",
                    "type": "given",
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
                    "type": "variable_id",
                    "instruction": "List the system and surroundings.",
                    "explanation": "The chemicals dissolving are the system; water and calorimeter are surroundings.",
                    "labeledValues": [
                        {"variable": "System", "value": "$\\mathrm{NH_4NO_3}$ dissolving in water", "unit": ""},
                        {"variable": "Surroundings", "value": "water and calorimeter", "unit": ""},
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
                    "type": "variable_id",
                    "instruction": "Identify the system and surroundings.",
                    "explanation": "The chemical reaction is the system; the surrounding water in the cup is the surroundings.",
                    "labeledValues": [
                        {"variable": "System", "value": "$\\mathrm{HCl}$ and $\\mathrm{NaOH}$ reacting", "unit": ""},
                        {"variable": "Surroundings", "value": "solution water in the cup", "unit": ""},
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
                    "type": "given",
                    "instruction": "Identify the starting value and target unit.",
                    "explanation": "We need to convert the given mass ($11.1 \\text{ g}$) into particles, called formula units.",
                    "correctAnswer": "11.1 g to formula units",
                    "skillUsed": "Identify conversion goal",
                },
                {
                    "label": "Conversion Factors",
                    "type": "given",
                    "instruction": "Find the molar mass of calcium chloride.",
                    "explanation": "$\\mathrm{Ca} + 2(\\mathrm{Cl}) = 40.08 + 2(35.45) = 110.98 \\text{ g/mol}$.",
                    "correctAnswer": "110.98",
                    "skillUsed": "Calculate molar mass of compounds",
                },
                {
                    "label": "Dimensional Setup",
                    "type": "given",
                    "instruction": "Set up the two-step conversion.",
                    "explanation": "Divide by molar mass to get moles, then multiply by Avogadro's number ($6.022 \\times 10^{23}$).",
                    "correctAnswer": "(11.1 / 110.98) × 6.022×10²³",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Calculate",
                    "type": "given",
                    "instruction": "Calculate the unrounded number of formula units.",
                    "explanation": None,
                    "correctAnswer": "6.0238 × 10²²",
                    "skillUsed": "Set up dimensional analysis",
                },
                {
                    "label": "Answer",
                    "type": "given",
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
        0,
        "medium",
        "detective",
        {
            "title": "Initial Rates: Determining a Rate Law",
            "statement": (
                "A reaction between gases $\\mathrm{A}$ and $\\mathrm{B}$ follows the form "
                "$\\mathrm{A} + \\mathrm{B} \\rightarrow \\text{products}$. A student measures initial rates at the same temperature.\n\n"
                "Experiment 1: $[\\mathrm{A}] = 0.10 \\text{ M}$, $[\\mathrm{B}] = 0.10 \\text{ M}$, "
                "rate $= 2.0 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 2: $[\\mathrm{A}] = 0.20 \\text{ M}$, $[\\mathrm{B}] = 0.10 \\text{ M}$, "
                "rate $= 4.0 \\times 10^{-3} \\text{ M/s}$.\n\n"
                "Experiment 3: $[\\mathrm{A}] = 0.10 \\text{ M}$, $[\\mathrm{B}] = 0.30 \\text{ M}$, "
                "rate $= 1.8 \\times 10^{-2} \\text{ M/s}$.\n\n"
                "Use the data to determine the order in $\\mathrm{A}$, the order in $\\mathrm{B}$, "
                "and the overall reaction order. What is the rate law?"
            ),
            "steps": [
                {
                    "label": "Data Extraction",
                    "type": "variable_id",
                    "instruction": "Extract the experiment values.",
                    "explanation": None,
                    "labeledValues": [
                        {
                            "variable": "Experiment 1",
                            "value": "$[\\mathrm{A}] = 0.10$, $[\\mathrm{B}] = 0.10$, rate $= 2.0 \\times 10^{-3}$",
                            "unit": "M, M, M/s",
                        },
                        {
                            "variable": "Experiment 2",
                            "value": "$[\\mathrm{A}] = 0.20$, $[\\mathrm{B}] = 0.10$, rate $= 4.0 \\times 10^{-3}$",
                            "unit": "M, M, M/s",
                        },
                        {
                            "variable": "Experiment 3",
                            "value": "$[\\mathrm{A}] = 0.10$, $[\\mathrm{B}] = 0.30$, rate $= 1.8 \\times 10^{-2}$",
                            "unit": "M, M, M/s",
                        },
                    ],
                    "skillUsed": "Extract data from representation",
                },
                {
                    "label": "Feature ID",
                    "type": "given",
                    "instruction": "Identify the order in $\\mathrm{A}$.",
                    "explanation": "From Experiments 1 and 2, doubling $[\\mathrm{A}]$ doubles the rate, so $m = 1$.",
                    "correctAnswer": "1",
                    "skillUsed": "Identify key feature or pattern",
                },
                {
                    "label": "Apply Concept",
                    "type": "given",
                    "instruction": "Identify the order in $\\mathrm{B}$.",
                    "explanation": "From Experiments 1 and 3, tripling $[\\mathrm{B}]$ increases the rate by $9$, so $n = 2$.",
                    "correctAnswer": "2",
                    "skillUsed": "Apply chemical concept to data",
                },
                {
                    "label": "Conclusion",
                    "type": "given",
                    "instruction": "State the rate law and overall order.",
                    "explanation": "Add exponents: $1 + 2 = 3$, so rate $= k[\\mathrm{A}][\\mathrm{B}]^2$ (third order).",
                    "correctAnswer": "rate = k[A][B]^2; 3rd order",
                    "skillUsed": "Draw scientific conclusion",
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
                    "type": "variable_id",
                    "instruction": "Identify the formula and atomic mass values.",
                    "explanation": "Extract the chemical formula and the mass from the text.",
                    "labeledValues": [
                        {"variable": "formula", "value": "$\\mathrm{O_2}$", "unit": ""},
                        {"variable": "O atomic mass", "value": "$16.00$", "unit": "g/mol"},
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
                    "type": "variable_id",
                    "instruction": "Identify the primary hazard and the broken rule.",
                    "explanation": "Extract the specific danger and the safety violation from the scenario.",
                    "labeledValues": [
                        {"variable": "Hazard", "value": "corrosive acid", "unit": ""},
                        {"variable": "Broken Rule", "value": "goggles on forehead", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Relation",
                    "type": "given",
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
                    "type": "variable_id",
                    "instruction": "Identify the primary hazard and the broken rule.",
                    "explanation": "Extract the chemical danger and the unsafe behavior from the scenario.",
                    "labeledValues": [
                        {"variable": "Hazard", "value": "corrosive base", "unit": ""},
                        {"variable": "Broken Rule", "value": "goggles on forehead", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Relation",
                    "type": "given",
                    "instruction": "State the safety rule being violated.",
                    "explanation": "Safety equipment must be worn correctly to provide actual protection.",
                    "correctAnswer": "always wear safety goggles over the eyes",
                    "skillUsed": "Identify common lab safety rules",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "given",
                    "instruction": "State the risk of this unsafe behavior.",
                    "explanation": "A splash from a corrosive base can cause permanent eye damage if unprotected.",
                    "correctAnswer": "chemical splash to the eyes",
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Conclusion",
                    "type": "given",
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
                    "type": "variable_id",
                    "instruction": "Identify the hazard and the broken rule.",
                    "explanation": "Extract the specific chemical danger and the unsafe action from the scenario.",
                    "labeledValues": [
                        {"variable": "Hazard", "value": "toxic heavy metals", "unit": ""},
                        {"variable": "Broken Rule", "value": "pouring chemicals down the sink", "unit": ""},
                    ],
                    "skillUsed": "Recognize hazard symbols",
                },
                {
                    "label": "Relation",
                    "type": "given",
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
                    "type": "variable_id",
                    "instruction": "Identify the hazard and the broken rule.",
                    "explanation": "Extract the chemical danger and the prohibited behavior.",
                    "labeledValues": [
                        {"variable": "Hazard", "value": "harmful if swallowed", "unit": ""},
                        {"variable": "Broken Rule", "value": "drinking in the lab", "unit": ""},
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
                    "type": "variable_id",
                    "instruction": "Distribute the 15 electrons into the correct subshells.",
                    "explanation": "Following the Aufbau principle: $1s$, $2s$, $2p$, $3s$ fill completely; 3 remain for $3p$.",
                    "skillUsed": "Write basic electron configurations",
                    "correctAnswer": None,
                    "equationParts": None,
                    "labeledValues": [
                        {"variable": "1s", "value": "2", "unit": "$e^-$"},
                        {"variable": "2s", "value": "2", "unit": "$e^-$"},
                        {"variable": "2p", "value": "6", "unit": "$e^-$"},
                        {"variable": "3s", "value": "2", "unit": "$e^-$"},
                        {"variable": "3p", "value": "3", "unit": "$e^-$"},
                    ],
                    "comparisonParts": None,
                },
                {
                    "label": "Draft",
                    "type": "drag_drop",
                    "instruction": "Arrange the subshells in the correct Aufbau order.",
                    "explanation": "Fill lowest to highest energy: $1s \\rightarrow 2s \\rightarrow 2p \\rightarrow 3s \\rightarrow 3p$.",
                    "skillUsed": "Write full electron configurations",
                    "correctAnswer": None,
                    "equationParts": ["$1s^2$", "$2s^2$", "$2p^6$", "$3s^2$", "$3p^3$"],
                    "labeledValues": None,
                    "comparisonParts": None,
                },
                {
                    "label": "Refine",
                    "type": "interactive",
                    "instruction": "How many unpaired electrons are in the 3p subshell?",
                    "explanation": "By Hund's rule, the three $3p$ electrons each occupy a separate orbital singly.",
                    "skillUsed": "Draw orbital notation diagrams",
                    "correctAnswer": "3",
                    "equationParts": None,
                    "labeledValues": None,
                    "comparisonParts": None,
                },
                {
                    "label": "Final Answer",
                    "type": "interactive",
                    "instruction": "State the complete electron configuration.",
                    "explanation": "Combine the ordered subshells into a single notation string.",
                    "skillUsed": "Write full electron configurations",
                    "correctAnswer": "1s2 2s2 2p6 3s2 3p3",
                    "equationParts": None,
                    "labeledValues": None,
                    "comparisonParts": None,
                },
            ],
        },
    ),
]