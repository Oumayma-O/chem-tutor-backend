"""
Heuristic: does the student answer contain any letters that likely denote a unit?

Used to catch "naked" numeric answers when the canonical answer includes a unit, without
trying to parse LaTeX-heavy strings for an exact unit match.

Not the same as ``local_hybrid._math_core_has_letters``: that helper decides whether the
answer is *formula-like* (skip numeric shortcut); this one asks whether any letters survive
after stripping math/LaTeX noise (proxy for "did they type a unit suffix?").
"""

from __future__ import annotations

import re

# Strip LaTeX command names, scientific notation, digits, common operators, and spelled-out ×/·.
_RE_STRIP_MATH = re.compile(
    r"\\[a-zA-Z]+"  # \times, \cdot, \mathrm, ...
    r"|[eE][+-]?\d+"  # 1e-3 style
    r"|[\d.\s+\-*/^()[\]{}=,]"  # digits, whitespace, punctuation
    r"|\b(?:times|cdot)\b",  # literal "times"/"cdot" if pasted without backslash
    re.IGNORECASE,
)


def student_provided_unit(student_answer: str) -> bool:
    """
    True if, after removing obvious math/LaTeX noise, any ASCII letters remain.

    Pure numbers / scientific notation / ``80 \\times 10^{-4}`` → False.
    ``0.0080 M/s``, ``8e-3 M``, ``\\mathrm{g}`` → True.
    """
    if not (student_answer or "").strip():
        return False
    cleaned = _RE_STRIP_MATH.sub("", student_answer)
    return bool(re.search(r"[A-Za-z]", cleaned))
