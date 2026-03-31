"""
Safe math expression evaluator.

Uses the stdlib `ast` module only — NO eval(), NO exec().

Handles:
  - Plain numbers:          0.20, 0.2, 1.5e-3
  - Arithmetic expressions: 0.025 * 8, 0.80 - 0.40, (0.025)(8)
  - Scientific notation:    1.5e-3, 1.5*10^-3, 1.5*10**-3
  - Unicode math symbols:   × → *, · → *, − → -, ^ → **
  - Trailing units:         "0.45 M" → numeric 0.45, unit "M"

Used by StepValidationService to avoid LLM calls for numeric steps.
"""

import ast
import math
import random
import re
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

    Returns:
      True  — definitely equal (within tolerance)
      False — definitely not equal
      None  — cannot determine numerically (e.g. non-numeric answers)

    rtol: relative tolerance (default 1%)
    atol: absolute tolerance for near-zero values
    """
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

    if cn == 0:
        return abs(sn) <= atol

    return abs(sn - cn) / abs(cn) <= rtol


def unit_equivalent(student: str, correct: str) -> bool:
    """
    Check whether two unit strings are equivalent (case-insensitive, whitespace-insensitive).

    Handles common aliases: molar → M, seconds → s, etc.
    """
    _ALIASES: dict[str, str] = {
        "molar": "m",
        "mol/l": "m",
        "mol/L": "m",
        "seconds": "s",
        "sec": "s",
        "minutes": "min",
        "kj": "kJ",
        "kj/mol": "kJ/mol",
    }

    def normalise(u: str) -> str:
        u = u.strip()
        return _ALIASES.get(u.lower(), u.lower().replace(" ", ""))

    su = extract_unit(student)
    cu = extract_unit(correct)

    # If correct answer has no unit, we don't require one
    if not cu:
        return True

    return normalise(su) == normalise(cu)
