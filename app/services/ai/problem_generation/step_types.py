"""Step-type assignment and enforcement for problem levels."""

from app.domain.schemas.tutor import ProblemOutput

_DRAG_DROP_LABELS = {"equation", "substitute", "formula", "expression", "draft", "arrange", "order", "sequence", "configuration"}
_MULTI_INPUT_LABELS = {"knowns", "given", "variables", "identify", "known values", "data extraction", "extraction"}


def _expected_step_types(level: int, n: int, labels: list[str] | None = None) -> list[str]:
    """Expected step-type sequence for a level with n steps (3–6)."""
    if level == 1:
        return ["given"] * n
    if level == 2:
        given = min(2, n)
        return ["given"] * given + ["interactive"] * (n - given)
    # Level 3: infer from labels, fallback interactive
    result = []
    for label in labels or []:
        lower = label.lower()
        if any(kw in lower for kw in _DRAG_DROP_LABELS):
            result.append("drag_drop")
        elif any(kw in lower for kw in _MULTI_INPUT_LABELS):
            result.append("multi_input")
        else:
            result.append("interactive")
    while len(result) < n:
        result.append("interactive")
    return result[:n]


def enforce_step_types(problem: ProblemOutput, level: int) -> ProblemOutput:
    """Fix step types on cache hits when served at a different level."""
    labels = [s.label for s in problem.steps]
    expected = _expected_step_types(level, len(problem.steps), labels=labels)
    for step, exp_type in zip(problem.steps, expected):
        step.type = exp_type  # type: ignore[assignment]
        if exp_type == "drag_drop" and not step.equation_parts:
            step.type = "interactive"  # type: ignore[assignment]
        if exp_type == "multi_input" and not step.input_fields:
            step.type = "interactive"  # type: ignore[assignment]
        if exp_type == "comparison" and not step.comparison_parts:
            step.type = "interactive"  # type: ignore[assignment]
    return problem
