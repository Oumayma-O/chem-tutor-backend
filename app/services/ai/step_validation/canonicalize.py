"""Deterministic canonicalization for symbolic chemistry/math answers."""

from __future__ import annotations

import re

from app.services.ai.step_validation._text_norm import normalise as _norm

_RE_ARROW = re.compile(r"(?:->|→|=>|⟶)")
_RE_NUM = re.compile(r"^[+\-]?\d+(?:\.\d+)?$")


def _insert_implicit_mul(s: str) -> str:
    out = s
    out = re.sub(r"\]\[", "]*[", out)
    out = re.sub(r"\)\(", ")*(", out)
    out = re.sub(r"(\d)([a-z\[])", r"\1*\2", out)
    out = re.sub(r"([a-z\]])(\[)", r"\1*\2", out)
    out = re.sub(r"([a-z\]\)])([a-z(])", r"\1*\2", out)
    return out


def _canonical_reaction_side(side: str) -> str:
    parts = [p for p in side.split("+") if p]
    items: list[tuple[str, str]] = []
    for p in parts:
        m = re.match(r"^(\d+(?:\.\d+)?)?([a-z0-9()\[\]\-^]+)$", p)
        if m:
            coef = m.group(1) or "1"
            species = m.group(2)
        else:
            coef = "1"
            species = p
        items.append((species, coef))
    items.sort(key=lambda t: t[0])
    return "+".join(f"{coef}{species}" for species, coef in items)


def canonicalize_reaction(s: str) -> str | None:
    t = _norm(s)
    if not _RE_ARROW.search(t):
        return None
    sides = _RE_ARROW.split(t, maxsplit=1)
    if len(sides) != 2:
        return None
    left, right = sides[0], sides[1]
    if not left or not right:
        return None
    return f"{_canonical_reaction_side(left)}->{_canonical_reaction_side(right)}"


def canonicalize_product_formula(s: str) -> str | None:
    t = _norm(s)
    if "->" in t or "→" in t or "+" in t or "-" in t or "/" in t:
        return None

    if "=" in t:
        lhs, rhs = t.split("=", 1)
        base = rhs if rhs else lhs
    else:
        base = t

    base = _insert_implicit_mul(base)
    factors = [f for f in base.split("*") if f]
    if not factors:
        return None

    coeff = 1.0
    sym_exp: dict[str, float] = {}
    raw_syms: list[str] = []

    for f in factors:
        m = re.match(r"^(.+?)(?:\^([+\-]?\d+(?:\.\d+)?))?$", f)
        if not m:
            return None
        token = m.group(1)
        exp_s = m.group(2) or "1"

        token = token.strip("()")
        if token.startswith("[") and token.endswith("]"):
            token = token[1:-1]

        if _RE_NUM.match(token):
            try:
                coeff *= float(token) ** float(exp_s)
            except Exception:
                return None
            continue

        try:
            exp = float(exp_s)
            sym_exp[token] = sym_exp.get(token, 0.0) + exp
        except Exception:
            raw_syms.append(f"{token}^{exp_s}")

    parts: list[str] = []
    if abs(coeff - 1.0) > 1e-12:
        parts.append(str(int(coeff)) if float(coeff).is_integer() else f"{coeff:.8g}")
    for sym in sorted(sym_exp):
        exp = sym_exp[sym]
        if abs(exp - 1.0) < 1e-12:
            parts.append(sym)
        else:
            parts.append(f"{sym}^{int(exp) if float(exp).is_integer() else f'{exp:.8g}'}")
    parts.extend(sorted(raw_syms))
    return "*".join(parts) if parts else None


def canonical_equivalent(student: str, correct: str) -> bool:
    """Deterministic Phase 1.5 equivalence for common formula/reaction re-orderings."""
    s_rxn = canonicalize_reaction(student)
    c_rxn = canonicalize_reaction(correct)
    if s_rxn is not None and c_rxn is not None:
        return s_rxn == c_rxn

    s_prod = canonicalize_product_formula(student)
    c_prod = canonicalize_product_formula(correct)
    if s_prod is not None and c_prod is not None:
        return s_prod == c_prod

    return False

