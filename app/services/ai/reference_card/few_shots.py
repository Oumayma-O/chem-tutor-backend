"""
Static few-shot examples for reference card generation, organised by Blueprint.

One example per blueprint — keys use snake_case to match the Pydantic schema.
All math MUST use $...$ delimiters; chemical formulas must use \\mathrm{}.
"""

_SOLVER: list[dict] = [
    {
        "human": "Generate a reference card for lesson 'Zero-Order Kinetics' (unit_id='ap-unit-5', lesson_index=1).",
        "assistant": """\
{
  "lesson": "Zero-Order Kinetics",
  "unit_id": "ap-unit-5",
  "lesson_index": 1,
  "steps": [
    {"label": "Equation",   "content": "$[A]_t = [A]_0 - kt$"},
    {"label": "Knowns",     "content": "$[A]_0$, $k$, $t$ — extract from text"},
    {"label": "Substitute", "content": "Plug given values into the rate law"},
    {"label": "Calculate",  "content": "Compute $k \\times t$ first, then subtract"},
    {"label": "Answer",     "content": "State concentration in $\\text{M}$ with sig figs"}
  ],
  "hint": "Apply this zero-order method to the specific values in your problem!"
}""",
    }
]

_RECIPE: list[dict] = [
    {
        "human": "Generate a reference card for lesson 'Molar Mass (1-Step)' (unit_id='unit-mole', lesson_index=1).",
        "assistant": """\
{
  "lesson": "Molar Mass (1-Step)",
  "unit_id": "unit-mole",
  "lesson_index": 1,
  "steps": [
    {"label": "Goal / Setup",       "content": "Identify starting unit and target unit"},
    {"label": "Conversion Factors", "content": "Find molar mass ($\\text{g/mol}$) from periodic table"},
    {"label": "Dimensional Setup",  "content": "Multiply to cancel starting units"},
    {"label": "Calculate",          "content": "Perform the unrounded arithmetic"},
    {"label": "Answer",             "content": "Round to sig figs of the starting value"}
  ],
  "hint": "Find the molar mass of your specific compound on the periodic table to begin!"
}""",
    }
]

_LAWYER: list[dict] = [
    {
        "human": "Generate a reference card for lesson 'Atomic Size' (unit_id='unit-periodic-table', lesson_index=1).",
        "assistant": """\
{
  "lesson": "Atomic Size",
  "unit_id": "unit-periodic-table",
  "lesson_index": 1,
  "steps": [
    {"label": "Concept ID",       "content": "Effective Nuclear Charge ($Z_{\\text{eff}}$) or electron shells"},
    {"label": "Relation",         "content": "Compare $Z_{\\text{eff}}$ or shells between the two atoms"},
    {"label": "Evidence / Claim", "content": "Higher $Z_{\\text{eff}}$ pulls electron cloud closer"},
    {"label": "Conclusion",       "content": "State which atom has the larger radius"}
  ],
  "hint": "Locate both elements on the periodic table to compare their groups and periods!"
}""",
    }
]

_DETECTIVE: list[dict] = [
    {
        "human": "Generate a reference card for lesson 'Mass Spectrometry' (unit_id='ap-unit-1', lesson_index=3).",
        "assistant": """\
{
  "lesson": "Mass Spectrometry",
  "unit_id": "ap-unit-1",
  "lesson_index": 3,
  "steps": [
    {"label": "Data Extraction", "content": "Record $m/z$ and relative abundance for each peak"},
    {"label": "Feature ID",      "content": "Convert percentage abundances to decimals"},
    {"label": "Apply Concept",   "content": "Calculate weighted average: $\\Sigma(\\text{mass} \\times \\text{abundance})$"},
    {"label": "Conclusion",      "content": "Match average mass to an element on the periodic table"}
  ],
  "hint": "Look closely at the heaviest and tallest peaks to guide your math!"
}""",
    }
]

_ARCHITECT: list[dict] = [
    {
        "human": "Generate a reference card for lesson 'Balancing Chemical Equations' (unit_id='unit-chemical-reactions', lesson_index=1).",
        "assistant": """\
{
  "lesson": "Balancing Chemical Equations",
  "unit_id": "unit-chemical-reactions",
  "lesson_index": 1,
  "steps": [
    {"label": "Inventory / Rules", "content": "Count atoms of each element on both sides"},
    {"label": "Draft",             "content": "Find the LCM for unbalanced atoms"},
    {"label": "Refine",            "content": "Add coefficients to balance one element at a time"},
    {"label": "Final Answer",      "content": "Verify all atoms balance; simplify coefficients"}
  ],
  "hint": "Leave oxygen and hydrogen for the very last step!"
}""",
    }
]

_FEW_SHOT_MAP: dict[str, list[dict]] = {
    "solver":    _SOLVER,
    "recipe":    _RECIPE,
    "lawyer":    _LAWYER,
    "detective": _DETECTIVE,
    "architect": _ARCHITECT,
}


def get_few_shots_for_blueprint(blueprint: str) -> list[dict]:
    """Return few-shot (human/assistant) pairs for the given blueprint name."""
    return _FEW_SHOT_MAP.get(blueprint, _SOLVER)
