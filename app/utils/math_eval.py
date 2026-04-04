"""
Safe math expression evaluator.

Uses the stdlib `ast` module only — NO eval(), NO exec().

Handles:
  - Plain numbers:          0.20, 0.2, 1.5e-3
  - Arithmetic expressions: 0.025 * 8, 0.80 - 0.40, (0.025)(8)
  - Scientific notation:    1.5e-3, 1.5*10^-3, 1.5*10**-3
  - Unicode math symbols:   × → *, · → *, − → -, ^ → **
  - LaTeX-style input:      ``latex_to_python_math`` maps ``\\times``, ``\\cdot``, ``^{}``, etc.
    to Python operators. Decimal points (.) are never treated as multiplication; only the LaTeX
    command ``\\cdot`` becomes ``*``.
  - Trailing units:         "0.45 M" → numeric 0.45, unit "M"
  - SI / prefix scaling:    ``pint`` compares magnitudes in base units (same dimension only).

Used by StepValidationService to avoid LLM calls for numeric steps.
"""

import ast
import math
import re
from functools import lru_cache
from typing import Tuple


# ── Constants available inside expressions ────────────────────
_SAFE_NAMES: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
}

_ALLOWED_AST_TYPES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    # Binary operators
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.FloorDiv, ast.Mod,
    # Unary operators
    ast.USub, ast.UAdd,
    # Names (only pi, e)
    ast.Name,
)



class _SafeVisitor(ast.NodeVisitor):
    """Walk an AST and evaluate numeric expressions only."""

    def visit_Expression(self, node: ast.Expression) -> float:
        return self.visit(node.body)

    def visit_BinOp(self, node: ast.BinOp) -> float:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.Div):
            if right == 0:
                raise ZeroDivisionError("Division by zero in student expression")
            return left / right
        if isinstance(op, ast.Pow):
            return left ** right
        if isinstance(op, ast.FloorDiv):
            if right == 0:
                raise ZeroDivisionError
            return float(int(left) // int(right))
        if isinstance(op, ast.Mod):
            if right == 0:
                raise ZeroDivisionError
            return left % right
        raise ValueError(f"Unsupported operator: {type(op).__name__}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> float:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError(f"Unsupported unary: {type(node.op).__name__}")

    def visit_Constant(self, node: ast.Constant) -> float:
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Non-numeric constant: {node.value!r}")

    def visit_Name(self, node: ast.Name) -> float:
        if node.id in _SAFE_NAMES:
            return _SAFE_NAMES[node.id]
        raise ValueError(f"Unknown name: {node.id!r}")

    def generic_visit(self, node: ast.AST) -> float:  # type: ignore[override]
        raise ValueError(f"Disallowed AST node: {type(node).__name__}")


_FRAC_SIMPLE = re.compile(r"\\frac\{([^{}]+)\}\{([^{}]+)\}")
_POW_BRACED = re.compile(r"\^\{([^{}]+)\}")


def latex_to_python_math(text: str) -> str:
    """Map common LaTeX math surface syntax to Python-evaluable text.

    Only replaces explicit LaTeX commands (``\\times``, ``\\cdot``, ``\\frac``, ``^{...}``).
    ASCII decimal points in numbers (e.g. ``0.0065``) are left unchanged; multiplication is
    ``\\cdot`` / ``\\times`` / Unicode ``×``, not the period between integer and fractional parts.
    """
    if not text:
        return text
    s = text.strip()
    s = re.sub(r"\$+", "", s).strip()

    s = re.sub(r"\\left\s*\(", "(", s)
    s = re.sub(r"\\right\s*\)", ")", s)
    s = re.sub(r"\\left\s*\[", "[", s)
    s = re.sub(r"\\right\s*\]", "]", s)

    for _ in range(24):
        s2 = _FRAC_SIMPLE.sub(r"((\1)/(\2))", s)
        if s2 == s:
            break
        s = s2

    s = re.sub(r"\\times", "*", s)
    s = re.sub(r"\\cdot", "*", s)
    s = re.sub(r"\\div", "/", s)

    for _ in range(24):
        s2 = re.sub(r"\\(?:mathrm|text)\{([^{}]*)\}", r"\1", s)
        if s2 == s:
            break
        s = s2

    for _ in range(24):
        s2 = _POW_BRACED.sub(r"**(\1)", s)
        if s2 == s:
            break
        s = s2

    # Single-digit exponent without braces: 10^4 → **(4) (digits only to limit false positives)
    s = re.sub(r"\^(\d)", r"**(\1)", s)

    return s.strip()


def _preprocess(expr: str) -> str:
    """Normalise an expression before parsing."""
    # Unicode math aliases
    expr = expr.replace("×", "*").replace("·", "*").replace("−", "-")
    expr = expr.replace("–", "-").replace("—", "-")

    # Caret exponent to Python power
    expr = expr.replace("^", "**")

    # Scientific notation: 1.5*10^-3 or 1.5×10^-3 already handled above
    # Also support 1.5e-3 (Python handles this natively)

    # Implicit multiplication: (a)(b)  →  (a)*(b)
    # e.g. (0.025)(8) → (0.025)*(8)
    expr = re.sub(r"\)\s*\(", ")*(", expr)

    # Implicit multiplication: 2(x) → 2*(x)
    expr = re.sub(r"(\d)\s*\(", r"\1*(", expr)

    return expr.strip()


def _strip_unit(text: str) -> Tuple[str, str]:
    """
    Split a value+unit string into (numeric_part, unit_part).

    Examples:
      "0.45 M"    → ("0.45",  "M")
      "20 s"      → ("20",    "s")
      "0.020 M/s" → ("0.020", "M/s")
      "0.45"      → ("0.45",  "")
    """
    text = text.strip()
    # Match number (possibly expression) followed by optional unit
    # Unit pattern: letters, /, digits, ^, ° (e.g. M, M/s, kJ/mol, s^-1)
    m = re.match(
        r"^([+\-]?[\d\.\*\+\-\(\)\^eE\s×·]+?)\s*([A-Za-z°%][A-Za-z°%/^·\d\-]*)?\s*$",
        text,
    )
    if m:
        return m.group(1).strip(), (m.group(2) or "").strip()
    return text, ""


def safe_eval(expr: str) -> float | None:
    """
    Safely evaluate a mathematical expression string.

    Returns the float result, or None if the expression is not a valid
    numeric expression (e.g. it contains units, text, or disallowed constructs).

    Never raises — returns None on any error.
    """
    try:
        processed = _preprocess(expr)
        tree = ast.parse(processed, mode="eval")

        # Security check: only allow safe node types
        for node in ast.walk(tree):
            if not isinstance(node, _ALLOWED_AST_TYPES):
                return None
            if isinstance(node, ast.Name) and node.id not in _SAFE_NAMES:
                return None

        result = _SafeVisitor().visit(tree)
        return float(result)
    except Exception:
        return None


def extract_numeric(text: str) -> float | None:
    """
    Try to extract a single float from a student answer that may include units.

    Examples:
      "0.45 M"    → 0.45
      "0.020 M/s" → 0.020
      "20"        → 20.0
      "0.80 - 0.40 = 0.40 M"  → 0.40  (last numeric segment)
    """
    text = text.strip()

    # Direct float
    try:
        return float(text)
    except ValueError:
        pass

    # Strip unit suffix
    num_part, _ = _strip_unit(text)
    result = safe_eval(num_part)
    if result is not None:
        return result

    # Try extracting last numeric token (for "= 0.40 M" style answers)
    tokens = re.findall(r"[+\-]?[\d]+\.?[\d]*(?:e[+\-]?\d+)?", text, re.IGNORECASE)
    if tokens:
        try:
            return float(tokens[-1])
        except ValueError:
            pass

    return None


def extract_unit(text: str) -> str:
    """
    Extract the unit from a student answer string.

    Returns the unit string (e.g. "M", "M/s", "s") or "" if none found.
    Intended for Phase 1 numeric paths; LaTeX-rich strings may not parse here.
    """
    _, unit = _strip_unit(text.strip())
    return unit


@lru_cache(maxsize=1)
def _get_pint_registry():
    import pint

    return pint.UnitRegistry()


# Case-sensitive molarity (chem): M ≠ m, nM ≠ nm, mM ≠ mm.
_PINT_MOLARITY_UNIT: dict[str, str] = {
    "M": "mol / liter",
    "mM": "mmol / liter",
    "μM": "micromole / liter",
    "uM": "micromole / liter",
    "nM": "nmol / liter",
    "pM": "pmol / liter",
}

# Single-token aliases → Pint (keys lowercased; μ → u before lookup).
_UNIT_TOKEN_TO_PINT: dict[str, str] = {
    "ns": "nanosecond",
    "us": "microsecond",
    "ms": "millisecond",
    "s": "second",
    "sec": "second",
    "secs": "second",
    "second": "second",
    "seconds": "second",
    "min": "minute",
    "mins": "minute",
    "minute": "minute",
    "minutes": "minute",
    "h": "hour",
    "hr": "hour",
    "hrs": "hour",
    "hour": "hour",
    "hours": "hour",
    "pm": "picometer",
    "nm": "nanometer",
    "um": "micrometer",
    "mm": "millimeter",
    "cm": "centimeter",
    "m": "meter",
    "meter": "meter",
    "meters": "meter",
    "km": "kilometer",
    "mg": "milligram",
    "g": "gram",
    "gram": "gram",
    "grams": "gram",
    "kg": "kilogram",
    "ul": "microliter",
    "ml": "milliliter",
    "l": "liter",
    "liter": "liter",
    "litre": "liter",
    "liters": "liter",
    "litres": "liter",
    "j": "joule",
    "kj": "kilojoule",
    "pa": "pascal",
    "kpa": "kilopascal",
    "mpa": "megapascal",
}


def _unit_token_to_pint_expression(unit: str) -> str | None:
    """Map a single-token unit label to a string Pint accepts. None if compound/unknown."""
    raw = unit.strip()
    if not raw or "/" in raw or "^" in raw:
        return None
    if raw in _PINT_MOLARITY_UNIT:
        return _PINT_MOLARITY_UNIT[raw]
    key = raw.lower().replace("μ", "u").replace(" ", "")
    return _UNIT_TOKEN_TO_PINT.get(key)


def _pint_quantity(magnitude: float, unit_token: str):
    expr = _unit_token_to_pint_expression(unit_token)
    if not expr:
        return None
    try:
        return _get_pint_registry().Quantity(magnitude, expr)
    except Exception:
        return None


def si_units_same_dimension(student_unit: str, correct_unit: str) -> bool:
    """True if Pint assigns both tokens the same dimension (e.g. ms and s)."""
    es = _unit_token_to_pint_expression(student_unit)
    ec = _unit_token_to_pint_expression(correct_unit)
    if not es or not ec:
        return False
    try:
        qs = _get_pint_registry().Quantity(1.0, es)
        qc = _get_pint_registry().Quantity(1.0, ec)
        return qs.dimensionality == qc.dimensionality
    except Exception:
        return False


def _numeric_within_rtol(a: float, b: float, rtol: float, atol: float) -> bool:
    if abs(b) <= atol:
        return abs(a) <= atol
    return abs(a - b) / abs(b) <= rtol


def _values_equivalent_with_si_scaling(
    sn: float,
    cn: float,
    student_unit: str,
    correct_unit: str,
    rtol: float,
    atol: float,
) -> bool:
    """Compare magnitudes in SI base units using Pint (same dimension only)."""
    qs = _pint_quantity(sn, student_unit)
    qc = _pint_quantity(cn, correct_unit)
    if qs is None or qc is None:
        return False
    if qs.dimensionality != qc.dimensionality:
        return False
    try:
        qb_s = qs.to_base_units()
        qb_c = qc.to_base_units()
    except Exception:
        return False
    return _numeric_within_rtol(float(qb_s.magnitude), float(qb_c.magnitude), rtol, atol)


def _strip_equation_lhs(text: str) -> str:
    """
    If text looks like 'Symbol = expression' (e.g. '[A]t = 2.5 - 0.05*20'),
    return just the RHS expression ('2.5 - 0.05*20').
    Only strips when the LHS contains non-numeric characters (letters/brackets),
    indicating it's a variable label rather than a numeric value.
    """
    idx = text.find("=")
    if idx < 0:
        return text
    lhs = text[:idx].strip()
    rhs = text[idx + 1:].strip()
    if rhs and re.search(r"[A-Za-z\[\]]", lhs):
        return rhs
    return text


def _eval_chemistry_expr(text: str) -> float | None:
    """
    Evaluate a chemistry answer that may be a plain number, an arithmetic
    expression, or an equation like '[A]t = 2.5 - 0.05*20'.

    Tries each candidate (original, then equation-RHS if present) with and
    without a trailing unit.  Returns None if nothing evaluates cleanly.
    """
    text = text.strip()
    candidates = [text]
    rhs = _strip_equation_lhs(text)
    if rhs != text:
        candidates.append(rhs)

    for candidate in candidates:
        result = safe_eval(_preprocess(candidate))
        if result is not None:
            return result
        num_part, _ = _strip_unit(candidate)
        if num_part != candidate:
            result = safe_eval(_preprocess(num_part))
            if result is not None:
                return result
    return None


def numeric_equivalent(
    student: str,
    correct: str,
    rtol: float = 0.01,
    atol: float = 1e-9,
) -> bool | None:
    """
    Check whether two answer strings are numerically equivalent.

    After a direct numeric comparison, also tries Pint SI scaling when both sides use a
    mapped single-token unit in the same dimension (e.g. ``ms`` vs ``s``).

    Returns:
      True  — definitely equal (within tolerance)
      False — definitely not equal
      None  — cannot determine numerically (e.g. non-numeric answers)

    rtol: relative tolerance (default 1%)
    atol: absolute tolerance for near-zero values
    """
    student = latex_to_python_math(student or "")
    correct = latex_to_python_math(correct or "")

    # Try chemistry-aware expression evaluation (handles "[A]t = expr" form)
    sn = _eval_chemistry_expr(student) if student else None
    cn = _eval_chemistry_expr(correct) if correct else None

    # Last-resort fallback: only use extract_numeric when BOTH sides fail
    # expression evaluation. Mixing one evaluated value with one last-number
    # extraction (e.g. student writes "ln(2.00)-1.00", correct has "0.693-1.00")
    # produces wrong comparisons — better to return None and let LLM decide.
    if sn is None and cn is None:
        sn = extract_numeric(student)
        cn = extract_numeric(correct)

    if sn is None or cn is None:
        return None

    su = extract_unit(student)
    cu = extract_unit(correct)
    psu = _unit_token_to_pint_expression(su) if su else None
    pcu = _unit_token_to_pint_expression(cu) if cu else None

    # Both sides map to Pint: compare in SI base only (prefix scaling + dimension check).
    if su and cu and psu is not None and pcu is not None:
        try:
            qs = _get_pint_registry().Quantity(1.0, psu)
            qc = _get_pint_registry().Quantity(1.0, pcu)
            if qs.dimensionality != qc.dimensionality:
                return False
        except Exception:
            return False
        return _values_equivalent_with_si_scaling(sn, cn, su, cu, rtol, atol)

    if _numeric_within_rtol(sn, cn, rtol, atol):
        return True

    if su and cu and _values_equivalent_with_si_scaling(sn, cn, su, cu, rtol, atol):
        return True

    return False


# Single source of truth for string-based unit equality (used by ``unit_equivalent`` and checkers).
UNIT_ALIAS_CANONICAL: dict[str, str] = {
    "molar": "m",
    "mol/l": "m",
    "mol/L": "m",
    "seconds": "s",
    "sec": "s",
    "minutes": "min",
    "kj": "kJ",
    "kj/mol": "kJ/mol",
    "s-1": "s^-1",
    "s**-1": "s^-1",
    "m/s2": "m/s^2",
    "m/s**2": "m/s^2",
}


def normalise_unit_string(u: str) -> str:
    """Normalise a bare unit label for equality (aliases, Unicode, LaTeX braces, spacing)."""
    u = u.strip()
    u = u.replace("\u2212", "-")
    u = u.replace("{", "").replace("}", "")
    u = u.replace("\u00b7", " ")
    u = u.replace(".", " ")
    u = re.sub(r"\s+", " ", u).strip()
    u = u.lower()
    return UNIT_ALIAS_CANONICAL.get(u, u.replace(" ", ""))


def unit_equivalent(student: str, correct: str) -> bool:
    """
    Check whether two answer strings carry equivalent trailing units.

    Uses ``extract_unit`` then ``normalise_unit_string`` (shared with multi-input checkers).
    """
    su = extract_unit(student)
    cu = extract_unit(correct)

    # If correct answer has no unit, we don't require one
    if not cu:
        return True

    return normalise_unit_string(su) == normalise_unit_string(cu)
