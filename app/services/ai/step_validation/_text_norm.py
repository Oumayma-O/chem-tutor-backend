"""Shared text normalisation for answer comparison."""

from __future__ import annotations


def normalise(s: str | None) -> str:
    """Canonical normalisation for answer comparison.

    Strips LaTeX delimiters, collapses spaces, and maps equivalent operators
    to a single form so string-level comparisons are notation-agnostic.
    """
    return (
        (s or "")
        .strip()
        .lower()
        .replace("$", "")       # strip LaTeX math delimiters
        .replace("{", "")       # strip LaTeX grouping braces  (10^{11} → 10^11)
        .replace("}", "")
        .replace(" ", "")
        .replace("×", "*")
        .replace("·", "*")
        .replace("−", "-")
        .replace("–", "-")
        .replace("**", "^")     # Python exponent → caret form
    )
