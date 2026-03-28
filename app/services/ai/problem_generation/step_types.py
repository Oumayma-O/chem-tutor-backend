"""Step-type assignment and scaffolding (is_given) guardrail for problem levels."""

from app.domain.schemas.tutor import ProblemOutput

_DRAG_DROP_LABELS = {"equation", "substitute", "formula", "expression", "draft", "arrange", "order", "sequence", "configuration"}
_MULTI_INPUT_LABELS = {"knowns", "given", "variables", "identify", "known values", "data extraction", "extraction", "goal / setup", "setup"}


def _infer_step_type(label: str, step: object) -> str:
    """Infer widget type: payload presence is unambiguous; label keywords are a fallback."""
    # Payload-first: presence of widget payload determines type definitively
    if getattr(step, "equation_parts", None):
        return "drag_drop"
    if getattr(step, "input_fields", None):
        return "multi_input"
    if getattr(step, "comparison_parts", None):
        return "comparison"
    # Label heuristic fallback for pure interactive steps
    lower = label.lower()
    if any(kw in lower for kw in _DRAG_DROP_LABELS):
        return "drag_drop"
    if any(kw in lower for kw in _MULTI_INPUT_LABELS):
        return "multi_input"
    return "interactive"


def enforce_step_types(problem: ProblemOutput, level: int) -> ProblemOutput:
    """
    Guardrail: fix widget types and enforce hard is_given rules for L1 and L3.

    Widget type is inferred from payload fields first (unambiguous); label
    keywords are a fallback for steps with no payload.

    is_given guardrail (LLM sets this; server enforces edge cases only):
      Level 1 → all steps MUST be given — force True if LLM missed any
      Level 2 → LLM controls (typically first 2 given); server does not override
      Level 3 → no steps may be given — force False if LLM set any True
    """
    for i, step in enumerate(problem.steps):
        inferred = _infer_step_type(step.label, step)

        # Fall back to math_input if the required payload is absent
        if inferred == "drag_drop" and not step.equation_parts:
            inferred = "interactive"
        if inferred == "multi_input" and not step.input_fields:
            inferred = "interactive"
        if inferred == "comparison" and not step.comparison_parts:
            inferred = "interactive"

        step.type = inferred  # type: ignore[assignment]

        # Guardrail: enforce hard level rules; trust LLM for level 2
        if level == 1:
            step.is_given = True          # L1 must always be full worked example
        elif level == 3:
            step.is_given = False         # L3 must always be independent practice
        # level 2: leave LLM-set is_given unchanged

    return problem
