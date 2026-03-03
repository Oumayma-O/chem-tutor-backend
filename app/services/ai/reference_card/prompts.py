"""
System prompt and few-shot examples for the reference card LLM chain.

Design rules enforced in the prompt:
  - Symbolic equations only (e.g. "[A]t = [A]₀ - k·t", not "0.50 - 0.02×30")
  - No numbers, no worked-out values, no specific measurements
  - Exactly 5 steps: Equation | Knowns | Substitute | Calculate | Answer
  - Each step is one concise sentence or short phrase — fiche-de-cours density
"""

REFERENCE_CARD_SYSTEM = """\
You are a chemistry teacher writing a concise "fiche de cours" (study reference card) \
for a single chemistry topic.

RULES (strictly follow all of them):
1. Show the GENERAL METHOD only — NO numerical examples, NO specific values.
2. Use symbolic variables (e.g. [A]₀, k, t, n, V, ΔH) but NEVER concrete numbers.
3. Produce exactly 5 steps with these exact labels in order:
     Equation  → the key formula(s) in symbolic form
     Knowns    → which variables to identify from the problem
     Substitute → how to plug values in (conceptual instruction only)
     Calculate  → what arithmetic/algebra to perform (symbolic description)
     Answer     → what units/significant figures/form the result should take
4. Each "content" field is one concise sentence or short phrase.
5. Write the "hint" as one sentence encouraging the student to apply the card to their problem.
6. Output valid JSON matching the schema — nothing else.
"""

# ---------------------------------------------------------------------------
# Few-shot examples (human → assistant pairs)
# ---------------------------------------------------------------------------

FEW_SHOT_EXAMPLES = [
    {
        "human": (
            "Generate a reference card for topic 'Zero-Order Kinetics' "
            "(chapter_id='chemical-kinetics', topic_index=0)."
        ),
        "assistant": """\
{
  "topic": "Zero-Order Kinetics",
  "chapter_id": "chemical-kinetics",
  "topic_index": 0,
  "steps": [
    {"label": "Equation",    "content": "[A]t = [A]₀ − k·t"},
    {"label": "Knowns",      "content": "Identify [A]₀ (initial concentration), k (rate constant), and t (time)"},
    {"label": "Substitute",  "content": "Plug [A]₀, k, and t directly into the equation"},
    {"label": "Calculate",   "content": "Compute k × t, then subtract the result from [A]₀"},
    {"label": "Answer",      "content": "Express the concentration in M with correct significant figures"}
  ],
  "hint": "This shows the general zero-order approach — apply it to the numbers in your current problem!"
}""",
    },
    {
        "human": (
            "Generate a reference card for topic 'First-Order Kinetics' "
            "(chapter_id='chemical-kinetics', topic_index=1)."
        ),
        "assistant": """\
{
  "topic": "First-Order Kinetics",
  "chapter_id": "chemical-kinetics",
  "topic_index": 1,
  "steps": [
    {"label": "Equation",    "content": "ln[A]t = ln[A]₀ − k·t"},
    {"label": "Knowns",      "content": "Identify which of [A]₀, [A]t, k, or t is unknown, and list the given values"},
    {"label": "Substitute",  "content": "Take the natural log of each concentration, then substitute all knowns"},
    {"label": "Calculate",   "content": "Rearrange algebraically to isolate the unknown and solve"},
    {"label": "Answer",      "content": "Report concentration in M or time in s (match problem units)"}
  ],
  "hint": "Apply this first-order method — use the actual values from your problem!"
}""",
    },
    {
        "human": (
            "Generate a reference card for topic 'Mole-to-Mole Stoichiometry' "
            "(chapter_id='stoichiometry', topic_index=0)."
        ),
        "assistant": """\
{
  "topic": "Mole-to-Mole Stoichiometry",
  "chapter_id": "stoichiometry",
  "topic_index": 0,
  "steps": [
    {"label": "Equation",    "content": "moles A × (coeff B / coeff A) = moles B"},
    {"label": "Knowns",      "content": "Identify the given substance, the target substance, and their stoichiometric coefficients from the balanced equation"},
    {"label": "Substitute",  "content": "Write the mole ratio (target coeff / given coeff) and multiply by the given moles"},
    {"label": "Calculate",   "content": "Multiply moles given by the mole ratio to obtain moles of the target substance"},
    {"label": "Answer",      "content": "Express the result in mol with appropriate significant figures"}
  ],
  "hint": "Use the balanced equation from your problem to fill in the coefficients — the rest follows this card!"
}""",
    },
]
