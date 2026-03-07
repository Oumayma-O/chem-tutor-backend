"""Curated few-shot examples for problem generation."""

FEW_SHOT_DATA: list[tuple[str, int, str, str, dict]] = [
    (
        "ap-unit-5",
        0,
        "easy",
        "quantitative",
        {
            "title": "Zero-Order Decay: Drug Elimination",
            "statement": (
                "A drug degrades in the bloodstream following zero-order kinetics. "
                "The initial concentration is 0.80 M and the rate constant k = 0.20 M/s. "
                "What is the concentration after 3 seconds?"
            ),
            "steps": [
                {"label": "Step 1 - Unknown", "type": "given", "instruction": "Identify the target variable to be solved.", "correctAnswer": "Final concentration ([A]t)", "skillUsed": "L-ap-kinetics-rate-laws: Determine target variable"},
                {"label": "Step 2 - Knowns", "type": "given", "instruction": "Extract the given values with their units from the narrative.", "correctAnswer": "[A]0 = 0.80 M, k = 0.20 M/s, t = 3 s", "skillUsed": "L-intro-measurement: Variable extraction and units"},
                {"label": "Step 3 - Equation", "type": "given", "instruction": "Select the correct zero-order integrated rate law.", "correctAnswer": "[A]t = [A]0 - kt", "skillUsed": "L-kinetics-zero-order: Integrated rate law selection"},
                {"label": "Step 4 - Substitute", "type": "given", "instruction": "Plug the known values into the equation.", "correctAnswer": "[A]t = 0.80 - (0.20)(3)", "skillUsed": "L-stoich-mass-mass: Algebraic substitution"},
                {"label": "Step 5 - Calculate", "type": "given", "instruction": "Perform the subtraction to find the final value.", "correctAnswer": "0.80 - 0.60 = 0.20", "skillUsed": "L-intro-measurement: Significant figure precision"},
                {"label": "Step 6 - Answer", "type": "given", "instruction": "State the final result with the correct units.", "correctAnswer": "0.20 M", "skillUsed": "L-intro-measurement: Standard unit application"},
            ],
        },
    ),
    (
        "ap-unit-5",
        1,
        "medium",
        "quantitative",
        {
            "title": "First-Order Half-Life",
            "statement": (
                "A first-order reaction has a rate constant k = 0.0231 min^-1. "
                "Calculate the concentration after 60 minutes if the initial concentration [A]0 = 0.500 M."
            ),
            "steps": [
                {"label": "Step 1 - Unknown", "type": "given", "instruction": "Identify the target variable to be solved.", "correctAnswer": "Final concentration ([A]t)", "skillUsed": "L-ap-kinetics-rate-laws: Determine target variable"},
                {"label": "Step 2 - Knowns", "type": "given", "instruction": "Extract the given values with their units.", "correctAnswer": "[A]0 = 0.500 M, k = 0.0231 min^-1, t = 60 min", "skillUsed": "L-intro-measurement: Variable extraction"},
                {"label": "Step 3 - Equation", "type": "given", "instruction": "Select the correct first-order integrated rate law.", "correctAnswer": "ln[A]t = ln[A]0 - kt", "skillUsed": "L-kinetics-first-order: Integrated rate law selection"},
                {"label": "Step 4 - Substitute", "type": "given", "instruction": "Plug the known values into the natural log equation.", "correctAnswer": "ln[A]t = ln(0.500) - (0.0231)(60)", "skillUsed": "L-stoich-mass-mass: Algebraic substitution"},
                {"label": "Step 5 - Calculate", "type": "given", "instruction": "Solve for [A]t by taking the inverse natural log (e^x).", "correctAnswer": "ln[A]t = -0.693 - 1.386 = -2.079; [A]t = e^(-2.079) = 0.125", "skillUsed": "L-kinetics-first-order: Logarithmic manipulation"},
                {"label": "Step 6 - Answer", "type": "given", "instruction": "State the final result with units and 3 sig figs.", "correctAnswer": "0.125 M", "skillUsed": "L-intro-measurement: Significant figure precision"},
            ],
        },
    ),
    (
        "unit-mole",
        2,
        "medium",
        "quantitative",
        {
            "title": "Two-Step Mole Conversion",
            "statement": "Find the mass in grams of 1.22 moles of sodium (Na). The molar mass of Na is 22.99 g/mol.",
            "steps": [
                {"label": "Step 1 - Unknown", "type": "given", "instruction": "Identify the unit you are trying to find.", "correctAnswer": "Mass of Na (g)", "skillUsed": "L-mole-molar-mass-1step: Identify conversion target"},
                {"label": "Step 2 - Knowns", "type": "given", "instruction": "List the starting value and the conversion factor (molar mass).", "correctAnswer": "n = 1.22 mol, Molar Mass = 22.99 g/mol", "skillUsed": "L-da-intro: Set up unit conversion factors"},
                {"label": "Step 3 - Equation", "type": "given", "instruction": "Select the formula relating moles and mass.", "correctAnswer": "mass = moles x molar mass", "skillUsed": "L-mole-molar-mass-1step: Moles to grams formula"},
                {"label": "Step 4 - Substitute", "type": "given", "instruction": "Plug the values into the conversion setup.", "correctAnswer": "1.22 mol x 22.99 g/mol", "skillUsed": "L-da-intro: Unit cancellation logic"},
                {"label": "Step 5 - Calculate", "type": "given", "instruction": "Multiply the numbers.", "correctAnswer": "28.0478", "skillUsed": "L-intro-measurement: Precision in multiplication"},
                {"label": "Step 6 - Answer", "type": "given", "instruction": "Round to the correct significant figures (3).", "correctAnswer": "28.0 g", "skillUsed": "L-intro-measurement: Significant figure precision"},
            ],
        },
    ),
    (
        "unit-nomenclature",
        1,
        "medium",
        "conceptual",
        {
            "title": "Writing Formula: Aluminum Sulfite",
            "statement": "Write the chemical formula for Aluminum sulfite. Use ion charges to ensure a neutral compound.",
            "steps": [
                {"label": "Step 1 - Identify Ions", "type": "given", "instruction": "Identify the symbols and charges for the cation and polyatomic anion.", "correctAnswer": "Aluminum = Al3+, Sulfite = SO3 2-", "skillUsed": "L-electrons-ions: Determine ion charge"},
                {"label": "Step 2 - Compare Charges", "type": "given", "instruction": "Determine the magnitude of the positive and negative charges.", "correctAnswer": "Al has a +3 charge; SO3 has a -2 charge.", "skillUsed": "L-nomenclature-name-formula: Use polyatomic ion charges"},
                {"label": "Step 3 - Balance Logic", "type": "given", "instruction": "Find the lowest common multiple to reach a net zero charge.", "correctAnswer": "Two Al3+ (+6) and three SO3 2- (-6) balance to zero.", "skillUsed": "L-nomenclature-name-formula: Total positive charge must equal total negative"},
                {"label": "Step 4 - Final Formula", "type": "given", "instruction": "Combine symbols using subscripts (use parentheses for the polyatomic ion).", "correctAnswer": "Al2(SO3)3", "skillUsed": "L-nomenclature-name-formula: Use subscripts to balance charges"},
            ],
        },
    ),
    (
        "ap-unit-1",
        8,
        "medium",
        "analytical",
        {
            "title": "Interpreting Mass Spectrometry Peaks",
            "statement": "A mass spectrum of an element shows two peaks: 35 amu (relative intensity 75%) and 37 amu (relative intensity 25%). Identify the element.",
            "steps": [
                {"label": "Step 1 - Observe Data", "type": "given", "instruction": "Read the x-axis for mass and y-axis for abundance.", "correctAnswer": "Isotope 1: mass 35, abundance 0.75; Isotope 2: mass 37, abundance 0.25", "skillUsed": "L-mass-spectrometry: Peak height corresponds to abundance"},
                {"label": "Step 2 - Correlation", "type": "given", "instruction": "Determine the relative contribution of each isotope to the average mass.", "correctAnswer": "The peak at 35 is 3x more abundant than 37.", "skillUsed": "L-mass-spectrometry: Relative abundance interpretation"},
                {"label": "Step 3 - Calculation", "type": "given", "instruction": "Calculate the weighted average atomic mass.", "correctAnswer": "(35 x 0.75) + (37 x 0.25) = 35.5 amu", "skillUsed": "L-atomic-mass: Calculate average atomic mass"},
                {"label": "Step 4 - Identify", "type": "given", "instruction": "Compare the calculated average mass to the Periodic Table.", "correctAnswer": "35.5 amu corresponds to Chlorine.", "skillUsed": "L-periodic-history: Use atomic mass to organize elements"},
                {"label": "Step 5 - Conclusion", "type": "given", "instruction": "State the name of the identified element.", "correctAnswer": "Chlorine (Cl)", "skillUsed": "L-intro-classification-matter: Elements consist of one type of atom"},
            ],
        },
    ),
]
