"""Null-byte and label sanitization for LLM-generated ProblemOutput."""

from app.domain.schemas.tutor import ProblemOutput


def _strip_nulls(s: str) -> str:
    return s.replace("\x00", "") if s else s


def sanitize_problem(problem: ProblemOutput) -> ProblemOutput:
    """Strip null bytes and trim pipe-separated step labels."""
    problem.title = _strip_nulls(problem.title)
    problem.statement = _strip_nulls(problem.statement)
    problem.lesson = _strip_nulls(problem.lesson)
    for step in problem.steps:
        step.label = _strip_nulls(step.label)
        if " | " in step.label:
            step.label = step.label.split(" | ")[0].strip()
        step.instruction = _strip_nulls(step.instruction)
        if step.explanation:
            step.explanation = _strip_nulls(step.explanation)
        if step.correct_answer:
            step.correct_answer = _strip_nulls(step.correct_answer)
        if step.skill_used:
            step.skill_used = _strip_nulls(step.skill_used)
        if step.equation_parts:
            step.equation_parts = [_strip_nulls(p) for p in step.equation_parts]
        if step.input_fields:
            for lv in step.input_fields:
                lv.label = _strip_nulls(lv.label)
                lv.value = _strip_nulls(lv.value)
                lv.unit = _strip_nulls(lv.unit)
        if step.comparison_parts:
            step.comparison_parts = [_strip_nulls(p) for p in step.comparison_parts]
    return problem
