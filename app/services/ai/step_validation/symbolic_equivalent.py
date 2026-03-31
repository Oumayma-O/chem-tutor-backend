"""Optional symbolic-equivalence checks for algebraic expressions.

Phase intent:
- Deterministic, cheap pass before LLM fallback.
- Handles algebraic rearrangements that string/canonical rules miss.
- Fails closed: on parse/import errors, returns False.
"""

from __future__ import annotations

import re

_RE_ARROW = re.compile(r"(?:->|→|=>|⟶)")
_RE_ALLOWED = re.compile(r"^[A-Za-z0-9_\s\[\]\(\)\+\-\*/\^.=]+$")
_RE_SYMBOL = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _preprocess(expr: str) -> str:
    s = (expr or "").strip()
    s = s.replace("$", "").replace("{", "").replace("}", "")
    s = s.replace("×", "*").replace("·", "*").replace("−", "-").replace("–", "-")
    # Treat concentration-style variables like [A] as symbolic A.
    s = re.sub(r"\[([A-Za-z_][A-Za-z0-9_]*)\]", r"\1", s)
    # Remove harmless whitespace for parser stability.
    return re.sub(r"\s+", "", s)


def _looks_symbolic_candidate(s: str) -> bool:
    if not s or _RE_ARROW.search(s):
        return False
    if not _RE_ALLOWED.match(s):
        return False
    # Must have at least one math operator and one alpha token.
    has_op = any(op in s for op in ("+", "-", "*", "/", "^", "="))
    return has_op and bool(re.search(r"[A-Za-z_]", s))


def symbolic_equivalent(student: str, correct: str) -> bool:
    """Return True if two symbolic algebraic forms are equivalent.

    Uses SymPy when available. If SymPy is unavailable or parsing fails,
    returns False (caller may continue to LLM fallback).
    """
    s = _preprocess(student)
    c = _preprocess(correct)
    if not (_looks_symbolic_candidate(s) and _looks_symbolic_candidate(c)):
        return False

    try:
        from sympy import simplify, symbols
        from sympy.parsing.sympy_parser import (
            convert_xor,
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )
    except Exception:
        return False

    transformations = standard_transformations + (
        implicit_multiplication_application,
        convert_xor,
    )

    sym_names = sorted(set(_RE_SYMBOL.findall(s)) | set(_RE_SYMBOL.findall(c)))
    local_dict = {name: symbols(name) for name in sym_names}

    def _parse(e: str):
        return parse_expr(e, local_dict=local_dict, transformations=transformations, evaluate=True)

    try:
        if "=" in s and "=" in c:
            sl, sr = s.split("=", 1)
            cl, cr = c.split("=", 1)
            s_expr = _parse(sl) - _parse(sr)
            c_expr = _parse(cl) - _parse(cr)
            return simplify(s_expr - c_expr) == 0

        if "=" in s or "=" in c:
            return False

        return simplify(_parse(s) - _parse(c)) == 0
    except Exception:
        return False

