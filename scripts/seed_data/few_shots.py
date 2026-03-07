"""Curated few-shot examples for problem generation.

Tuple layout: (unit_id, lesson_index, difficulty, blueprint, problem_dict)
The `blueprint` field maps to Lesson.blueprint from the DB.
Field names in step dicts use camelCase (API/JSON convention) to match LLM output exactly.
"""

FEW_SHOT_DATA: list[tuple[str, int, str, str, dict]] = [
    (
        "unit-atomic-theory",
        2,
        "medium",
        "detective",
        {
            "title": "Identifying an Element from Isotopic Abundance",
            "statement": (
                "A sample contains an element with two naturally occurring isotopes detected by mass spectrometry: "
                "one has a mass of 63.0 amu (abundance 69.0%), and the other has a mass of 65.0 amu (abundance 31.0%). "
                "Identify the element."
            ),
            "steps": [
                {
                    "label": "Data Extraction",
                    "type": "given",
                    "instruction": "Identify the mass of the most abundant isotope.",
                    "correctAnswer": "63.0",
                    "skillUsed": "Extract data from representation",
                },
                {
                    "label": "Feature ID",
                    "type": "variable_id",
                    "instruction": "Convert the given percentage abundances into decimals.",
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
                    "correctAnswer": "63.62 amu",
                    "skillUsed": "Apply chemical concept to data",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Identify the element's chemical symbol.",
                    "correctAnswer": "Cu",
                    "skillUsed": "Draw scientific conclusion",
                },
            ],
        },
    ),
    (
        "unit-periodic-table",
        2,
        "easy",
        "lawyer",
        {
            "title": "Comparing Atomic Radius",
            "statement": (
                "Compare the atomic radii of Sodium (Na) and Chlorine (Cl). "
                "Which element has a larger atomic radius and why?"
            ),
            "steps": [
                {
                    "label": "Concept ID",
                    "type": "given",
                    "instruction": "Identify the principle governing atomic radius across a period.",
                    "correctAnswer": "Effective Nuclear Charge",
                    "skillUsed": "Identify governing concept",
                },
                {
                    "label": "Relation",
                    "type": "comparison",
                    "instruction": "Compare the effective nuclear charge of Na and Cl.",
                    "comparisonParts": ["Zeff of Na", "Zeff of Cl"],
                    "correctAnswer": "<",
                    "skillUsed": "State chemical relationship",
                },
                {
                    "label": "Evidence / Claim",
                    "type": "interactive",
                    "instruction": "How does a higher effective nuclear charge affect the electron cloud?",
                    "correctAnswer": "Pulls electrons closer",
                    "skillUsed": "Provide evidence/reasoning",
                },
                {
                    "label": "Conclusion",
                    "type": "interactive",
                    "instruction": "Identify the element with the larger atomic radius.",
                    "correctAnswer": "Na",
                    "skillUsed": "State final conclusion",
                },
            ],
        },
    ),
    (
        "ap-unit-5",
        3,
        "medium",
        "solver",
        {
            "title": "Zero-Order Decay: Drug Elimination",
            "statement": (
                "A drug degrades in the bloodstream following zero-order kinetics. "
                "The initial concentration is 0.80 M and the rate constant k = 0.020 M/s. "
                "What is the concentration after 20 seconds?"
            ),
            "steps": [
                {
                    "label": "Equation",
                    "type": "drag_drop",
                    "instruction": "Form the correct zero-order integrated rate law.",
                    "equationParts": ["[A]t", "=", "[A]0", "-", "k", "*", "t"],
                    "skillUsed": "Select correct equation",
                },
                {
                    "label": "Knowns",
                    "type": "variable_id",
                    "instruction": "Extract the given values and their units.",
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
                    "instruction": "Plug the known values into the integrated rate law.",
                    "correctAnswer": "0.80 - (0.020)(20)",
                    "skillUsed": "Substitute values into equation",
                },
                {
                    "label": "Calculate",
                    "type": "interactive",
                    "instruction": "Compute the product of k and t.",
                    "correctAnswer": "0.40",
                    "skillUsed": "Compute final answer with sig figs",
                },
                {
                    "label": "Answer",
                    "type": "interactive",
                    "instruction": "Calculate the final concentration.",
                    "correctAnswer": "0.40 M",
                    "skillUsed": "Compute final answer with sig figs",
                },
            ],
        },
    ),
]
