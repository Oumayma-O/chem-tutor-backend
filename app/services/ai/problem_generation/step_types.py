"""Step-type assignment and scaffolding (is_given) for problem levels."""

from app.domain.schemas.tutor import ProblemOutput

_DRAG_DROP_LABELS = {"equation", "substitute", "formula", "expression", "draft", "arrange", "order", "sequence", "configuration"}
_MULTI_INPUT_LABELS = {"knowns", "given", "variables", "identify", "known values", "data extraction", "extraction"}


def _infer_step_type(label: str, step: object) -> str:
    """Infer the real widget type from a step label and its payload."""
    lower = label.lower()
    if any(kw in lower for kw in _DRAG_DROP_LABELS):
        return "drag_drop"
    if any(kw in lower for kw in _MULTI_INPUT_LABELS):
        return "multi_input"
    return "interactive"


def enforce_step_types(problem: ProblemOutput, level: int) -> ProblemOutput:
    """
    Assign real widget types and set ``is_given`` for every step based on level.

    Widget type is inferred from the step label; falls back to ``interactive``
    when the required payload (equation_parts / input_fields) is absent.

    is_given rules (server-computed — never stored by LLM):
      Level 1 → all steps are given (full worked example)
      Level 2 → steps 1 and 2 are given (faded example scaffolding)
      Level 3 → no steps are given (full student practice)
    """
    for i, step in enumerate(problem.steps):
        # Infer real widget type from label
        inferred = _infer_step_type(step.label, step)

        # Fall back to interactive if the required payload is absent
        if inferred == "drag_drop" and not step.equation_parts:
            inferred = "interactive"
        if inferred == "multi_input" and not step.input_fields:
            inferred = "interactive"

        step.type = inferred  # type: ignore[assignment]

        # Set scaffolding flag by level and position (0-indexed)
        if level == 1:
            step.is_given = True
        elif level == 2:
            step.is_given = i < 2
        else:
            step.is_given = False

    return problem
