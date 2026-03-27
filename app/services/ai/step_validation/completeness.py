"""Ensure multi-part canonical answers (e.g. ``equation; overall order``) are fully reflected."""

from __future__ import annotations

from app.domain.schemas.tutor import ValidationOutput
from app.services.ai.step_validation.checkers import normalise


def _norm_segments(s: str) -> str:
    """Normalize for substring checks; map common word order forms to numeric ordinals."""
    t = normalise(s)
    for word, n in (
        ("first", "1st"),
        ("second", "2nd"),
        ("third", "3rd"),
        ("fourth", "4th"),
        ("fifth", "5th"),
    ):
        t = t.replace(word, n)
    return t


def _segments(correct: str) -> list[str]:
    return [p.strip() for p in (correct or "").split(";") if p.strip()]


def _segment_is_missing(pn: str, st: str) -> bool:
    """Return True only if normalised segment ``pn`` is genuinely absent from student text ``st``.

    For variable=value segments (e.g. ``δg°=-65.6kj/mol``), if the key (variable name before ``=``)
    is present in the student's answer, the student addressed that quantity in a different form
    (e.g. different SI prefix). In that case we trust the LLM's equivalence verdict instead of
    flagging it as missing.
    """
    if pn in st:
        return False
    if "=" in pn:
        key = pn.split("=")[0]
        if key and key in st:
            return False
    return True


def first_missing_segment_message(student: str, correct: str) -> str | None:
    """If ``correct`` lists ``;``-separated required parts, each must appear in ``student`` (normalized)."""
    parts = _segments(correct)
    if len(parts) <= 1:
        return None
    st = _norm_segments(student)
    for part in parts:
        pn = _norm_segments(part)
        if not pn:
            continue
        if _segment_is_missing(pn, st):
            return f"Include this in your answer: {part}"
    return None


def partial_multisegment_feedback(student: str, correct: str) -> str | None:
    """
    When at least one ``;`` chunk from ``correct`` appears in ``student`` but not all do,
    return feedback that names only what is still missing.

    If nothing from ``correct`` is matched as a substring, return None and let phase1/LLM decide
    (avoids blaming a \"missing rate law\" when the student wrote a wrong rate law).
    """
    parts = [p.strip() for p in _segments(correct) if p.strip()]
    if len(parts) <= 1:
        return None
    st = _norm_segments(student)
    missing: list[str] = []
    for part in parts:
        pn = _norm_segments(part)
        if not pn:
            continue
        if _segment_is_missing(pn, st):
            missing.append(part)
    if not missing:
        return None
    if not any(not _segment_is_missing(_norm_segments(p), st) for p in parts if _norm_segments(p)):
        return None
    if len(missing) == 1:
        return f"Include this in your answer: {missing[0]}"
    return "Include these in your answer: " + "; ".join(missing)


def prefer_partial_multisegment_feedback(
    out: ValidationOutput, student: str, correct: str
) -> ValidationOutput:
    """Replace vague wrong-answer feedback when we can state only the missing ``;``-segments."""
    if out.is_correct:
        return out
    if precise := partial_multisegment_feedback(student, correct):
        return ValidationOutput(
            is_correct=False,
            feedback=precise,
            validation_method="local_incomplete_segments",
            student_value=out.student_value,
            correct_value=out.correct_value,
            unit_correct=out.unit_correct,
        )
    return out
