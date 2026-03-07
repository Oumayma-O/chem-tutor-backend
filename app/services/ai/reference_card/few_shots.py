"""
Static few-shot examples for reference card generation, organised by strategy.

Format per example:
  human     — the user turn sent to the LLM
  assistant — the expected JSON response (matches ReferenceCardOutput schema)

Keys in assistant JSON always use snake_case to match the Pydantic schema.
"""

_QUANTITATIVE: list[dict] = [
    {
        "human": (
            "Generate a reference card for topic 'Zero-Order Kinetics' "
            "(unit_id='unit-solutions', lesson_index=0)."
        ),
        "assistant": """\
{
  "topic": "Zero-Order Kinetics",
  "unit_id": "unit-solutions",
  "lesson_index": 0,
  "steps": [
    {"label": "Knowns",     "content": "[A]_0, k, t — identify from problem"},
    {"label": "Equation",   "content": "[A]_t = [A]_0 - k*t"},
    {"label": "Substitute", "content": "Plug [A]_0, k, t into equation"},
    {"label": "Answer",     "content": "M, correct sig figs"}
  ],
  "hint": "Apply this zero-order method to the actual values in your problem!"
}""",
    },
    {
        "human": (
            "Generate a reference card for topic 'Mole-to-Mole Stoichiometry' "
            "(unit_id='unit-stoichiometry', lesson_index=0)."
        ),
        "assistant": """\
{
  "topic": "Mole-to-Mole Stoichiometry",
  "unit_id": "unit-stoichiometry",
  "lesson_index": 0,
  "steps": [
    {"label": "Knowns",     "content": "Given substance, target, balanced coeffs"},
    {"label": "Equation",   "content": "moles A x (coeff B / coeff A) = moles B"},
    {"label": "Substitute", "content": "Mole ratio x given moles"},
    {"label": "Answer",     "content": "mol, sig figs"}
  ],
  "hint": "Fill in the coefficients from your balanced equation — the rest follows this card!"
}""",
    },
]

_CONCEPTUAL: list[dict] = [
    {
        "human": (
            "Generate a reference card for topic 'Periodic Trends: Atomic Radius' "
            "(unit_id='unit-periodic-table', lesson_index=2)."
        ),
        "assistant": """\
{
  "topic": "Periodic Trends: Atomic Radius",
  "unit_id": "unit-periodic-table",
  "lesson_index": 2,
  "steps": [
    {"label": "Governing Principle",  "content": "Radius decreases across period; increases down group"},
    {"label": "Concept Application",  "content": "Compare Z_eff and shielding of atoms"},
    {"label": "Final Justification",  "content": "Higher Z_eff pulls e- closer, smaller radius"}
  ],
  "hint": "Use this trend logic to rank the specific elements in your problem!"
}""",
    },
    {
        "human": (
            "Generate a reference card for topic 'Types of Chemical Reactions' "
            "(unit_id='unit-chemical-reactions', lesson_index=0)."
        ),
        "assistant": """\
{
  "topic": "Types of Chemical Reactions",
  "unit_id": "unit-chemical-reactions",
  "lesson_index": 0,
  "steps": [
    {"label": "Governing Principle",  "content": "Synthesis, decomposition, displacement, combustion"},
    {"label": "Concept Application",  "content": "Match reactant/product pattern to type"},
    {"label": "Final Justification",  "content": "State type + evidence from equation"}
  ],
  "hint": "Identify the pattern in your equation and apply this classification card!"
}""",
    },
]

_ANALYTICAL: list[dict] = [
    {
        "human": (
            "Generate a reference card for topic 'Reading Reaction Rate Graphs' "
            "(unit_id='ap-unit-5', lesson_index=1)."
        ),
        "assistant": """\
{
  "topic": "Reading Reaction Rate Graphs",
  "unit_id": "ap-unit-5",
  "lesson_index": 1,
  "steps": [
    {"label": "Data Observation",     "content": "Note slope, intercept, curve shape"},
    {"label": "Feature Correlation",  "content": "Link slope sign/magnitude to reaction order"},
    {"label": "Scientific Inference", "content": "State order/rate constant from graph"}
  ],
  "hint": "Apply these observation steps to the graph in your current problem!"
}""",
    },
]

_FEW_SHOT_MAP: dict[str, list[dict]] = {
    "quantitative": _QUANTITATIVE,
    "conceptual":   _CONCEPTUAL,
    "analytical":   _ANALYTICAL,
}


def get_few_shots_for_strategy(strategy: str) -> list[dict]:
    """Return few-shot (human/assistant) pairs for the given strategy.

    Falls back to quantitative examples for unknown strategies.
    """
    return _FEW_SHOT_MAP.get(strategy, _QUANTITATIVE)
