"""User-facing validation feedback strings (single source of truth)."""

# Empty / configuration
FEEDBACK_EMPTY_STUDENT_ANSWER = "Please enter an answer."
FEEDBACK_MISSING_CANONICAL = "Expected answer missing for this step."

# When local/LLM paths mark incorrect but attach no specific feedback (hint pipeline safety net)
FEEDBACK_GENERIC_INCORRECT = (
    "That's not quite right. Compare your answer to what this step expects."
)

# Unit presence — Phase 1 numeric path and post-processing for non-LLM resolutions
FEEDBACK_INCLUDE_UNIT_SHORT = "Include the unit that goes with your value."

# Unit presence — after LLM marked correct but heuristic finds no unit letters
FEEDBACK_LLM_VALUE_OK_MISSING_UNIT = (
    "You have the correct value, but you forgot to include the units (e.g., M/s, g/mol)."
)
