"""
Category detector and example selector for the LLM equivalence grader.

select_examples(correct_answer, step_label) → formatted string injected into
the system prompt.  Only relevant blocks are included so the prompt stays
compact; GENERAL is always appended as a fallback anchor.
"""

from __future__ import annotations

import re

from app.services.ai.step_validation import few_shots_data as _d

# ── Category regexes ──────────────────────────────────────────────────────────

_RE_ARROW       = re.compile(r"→|->|\\rightarrow", re.IGNORECASE)
_RE_NOBLE_CORE  = re.compile(r"\[(ar|he|ne|kr|xe|rn)\]|1s2|2s2", re.IGNORECASE)
_RE_RATE_LAW    = re.compile(r"k\s*\[", re.IGNORECASE)
_RE_EQUILIBRIUM = re.compile(r"\b(kc|kp|ksp|keq|qc|qp)\b|\[\w", re.IGNORECASE)
_RE_THERMO      = re.compile(r"δg|δh|δs|\\delta\s*[ghs]|gibbs|enthalpy|entropy", re.IGNORECASE)
_RE_EXPRESSION  = re.compile(r"[\*/\(\)]\s*\d|\d\s*[\*/\(\)]")
_RE_NUMERIC     = re.compile(r"^[+\-]?\s*\d[\d.,e\s×\^+\-]*[a-z/°²³]*$", re.IGNORECASE)

_HEADER = "─── CALIBRATION EXAMPLES ───────────────────────────────────────────\n"
_FOOTER = "─────────────────────────────────────────────────────────────────────\n"


def select_examples(correct_answer: str, step_label: str) -> str:
    """
    Return a formatted string of calibration examples relevant to this step.

    Always includes GENERAL.  Prepends at most two domain-specific blocks
    chosen from correct_answer content and step_label keywords.
    """
    ca    = correct_answer.strip()
    label = step_label.lower()

    blocks: list[str] = []

    # Compound (;-separated) — highest priority regardless of other signals
    if ";" in ca:
        blocks.append(_d.COMPOUND)

    # Balanced equation
    if _RE_ARROW.search(ca):
        blocks.append(_d.EQUATION)

    # Electron configuration
    elif _RE_NOBLE_CORE.search(ca):
        blocks.append(_d.CONFIG)

    # Rate law
    elif _RE_RATE_LAW.search(ca) or any(kw in label for kw in ("rate law", "rate", "kinetic", "arrhenius")):
        blocks.append(_d.RATE_LAW)

    # Equilibrium expression
    elif _RE_EQUILIBRIUM.search(ca) or any(kw in label for kw in ("equilibrium", "ksp", "kc", "kp", "ice", "solubility")):
        blocks.append(_d.EQUILIBRIUM)

    # Thermodynamic quantity
    elif _RE_THERMO.search(ca) or any(kw in label for kw in ("gibbs", "enthalpy", "entropy", "thermodynamic", "δg", "δh", "δs")):
        blocks.append(_d.THERMODYNAMIC)

    # Algebraic expression / calculation setup
    elif _RE_EXPRESSION.search(ca):
        blocks.append(_d.EXPRESSION)

    # Pure numeric (single value ± unit)
    elif _RE_NUMERIC.match(ca.replace("×", "x").replace(" ", "")):
        blocks.append(_d.NUMERIC)

    # General is always the final anchor
    blocks.append(_d.GENERAL)

    return _HEADER + "\n".join(blocks) + _FOOTER
