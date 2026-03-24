"""
Deterministic Markdown/LaTeX sanitizer for LLM-generated problem JSON.

Pipeline: LLM → structured JSON → normalize_and_validate_problem() → safe for React/KaTeX.

Fixes applied to every string:
- Mis-written units: \\backslash\\text{cdotK} → \\cdot \\text{K} (LLM confusion vs \\cdot)
- Unbracketed exponents: 10^23 → 10^{23}
- Orphaned \\text: \\textamu → \\text{amu}
- Orphaned \\mathrm: \\mathrmMg → \\mathrm{Mg}, \\mathrmH2O → \\mathrm{H2O}
- Illegal chars: raw tabs, ANSI escape codes, null bytes
- Math wrappers: \\( and \\) → $, $$...$$ → $...$
- KaTeX dry-run: balanced braces in math blocks, no forbidden commands (e.g. \\align)
"""

import re
from typing import Any


# ── String-level fixes ─────────────────────────────────────────────────────

# Unbracketed exponent: 10^23 → 10^{23}, 10^n → 10^{n} (skip if already 10^{...})
_RE_EXP_DIGITS = re.compile(r"(\d+)\^(\d+)(?!\s*\{)")
_RE_EXP_LETTER = re.compile(r"(\d+)\^([a-zA-Z])(?!\s*\{)")
def _fix_unbracketed_exponents(s: str) -> str:
    s = _RE_EXP_DIGITS.sub(r"\1^{\2}", s)
    s = _RE_EXP_LETTER.sub(r"\1^{\2}", s)
    return s


# LLM mistake: \backslash\text{cdotK} or \text{cdotK} instead of \cdot \text{K} (units like J/mol·K)
_RE_BACKSLASH_TEXT_CDOTK = re.compile(
    r"\\backslash\s*\\text\{cdot\s*K\}",
    re.IGNORECASE,
)
_RE_BACKSLASH_TEXT_CDOTK_COMPACT = re.compile(
    r"\\backslash\s*\\text\{cdotK\}",
    re.IGNORECASE,
)
_RE_TEXT_CDOTK = re.compile(r"\\text\{cdotK\}", re.IGNORECASE)
_RE_TEXT_CDOT_K = re.compile(r"\\text\{cdot\s*K\}", re.IGNORECASE)


def _fix_cdot_unit_garbage(s: str) -> str:
    """
    Fix \backslash\text{cdotK} and similar: models use \\backslash when they mean \\cdot,
    and pack 'cdotK' inside \\text{...} which KaTeX renders as broken / red text.
    """
    s = _RE_BACKSLASH_TEXT_CDOTK.sub(r"\\cdot \\text{K}", s)
    s = _RE_BACKSLASH_TEXT_CDOTK_COMPACT.sub(r"\\cdot \\text{K}", s)
    s = _RE_TEXT_CDOTK.sub(r"\\cdot \\text{K}", s)
    s = _RE_TEXT_CDOT_K.sub(r"\\cdot \\text{K}", s)
    # Rare: \backslash\cdot or \backslash\cdot\text{...}
    s = re.sub(r"\\backslash\s*\\cdot", r"\\cdot", s)
    return s


# Orphaned \text: \textamu → \text{amu} (when not already \text{...})
_RE_ORPHAN_TEXT = re.compile(r"\\text([a-zA-Z][a-zA-Z0-9_]*)")
def _fix_orphan_text(s: str) -> str:
    return _RE_ORPHAN_TEXT.sub(r"\\text{\1}", s)


# Orphaned \mathrm: \mathrmMg → \mathrm{Mg} (when not already \mathrm{...})
_RE_ORPHAN_MATHRM = re.compile(r"\\mathrm([a-zA-Z][a-zA-Z0-9_]*)")
def _fix_orphan_mathrm(s: str) -> str:
    return _RE_ORPHAN_MATHRM.sub(r"\\mathrm{\1}", s)


# Unclosed \mathrm{: $\mathrm{Mg}$ (missing }) → $\mathrm{Mg}$
_RE_UNCLOSED_MATHRM = re.compile(r"\\mathrm\{([a-zA-Z0-9_]+)(?=\$|\Z)")
def _fix_unclosed_mathrm(s: str) -> str:
    return _RE_UNCLOSED_MATHRM.sub(r"\\mathrm{\1}", s)


# ── Tab/form-feed LaTeX recovery ───────────────────────────────────────────
# When the LLM single-escapes a LaTeX command in JSON (e.g. \text instead of \\text),
# the JSON parser interprets \t → TAB (0x09) and \f → FORM FEED (0x0C), silently
# destroying the backslash.  These fixers MUST run before _strip_illegal_chars
# so the raw control chars are still present for matching.
#
# \t (TAB) prefixes: \text, \times, \to, \top, \tilde, \theta, \tau
_RE_TAB_LATEX = re.compile(
    r"\x09(ext|imes|ilde|heta|au|op|o)(?=[^a-zA-Z]|$)"
)
# \f (FORM FEED) prefixes: \frac, \forall
_RE_FF_LATEX = re.compile(r"\x0c(rac|orall)(?=[^a-zA-Z]|$)")

def _recover_tab_corrupted_latex(s: str) -> str:
    s = _RE_TAB_LATEX.sub(r"\\t\1", s)
    s = _RE_FF_LATEX.sub(r"\\f\1", s)
    return s


# ANSI escape and control chars
_RE_ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]?")
_RE_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
def _strip_illegal_chars(s: str) -> str:
    s = s.replace("\t", " ")
    s = _RE_ANSI.sub("", s)
    s = _RE_CONTROL.sub("", s)
    return s


# Normalize \( and \) to $ (inline math)
# Collapse $$...$$ → $...$ (display math renders oversized/centered in the UI)
_RE_DISPLAY_MATH = re.compile(r"\$\$([^$]*?)\$\$", re.DOTALL)
def _normalize_math_wrappers(s: str) -> str:
    s = s.replace("\\(", "$").replace("\\)", "$")
    s = _RE_DISPLAY_MATH.sub(r"$\1$", s)
    # Collapse any remaining orphaned $$ (e.g. trailing "...$$.") → $
    s = s.replace("$$", "$")
    return s


# Fix $X$^{n} / $X$_{n}: superscript or subscript that leaked outside closing $
# e.g. "$2s$^{2}" → "$2s^{2}$", "$k$_{obs}" → "$k_{obs}$"
# This happens when the LLM wraps only the base in $...$ and forgets to include
# the exponent/subscript inside the same delimiters.
_RE_DOLLAR_SPLIT_SUPER = re.compile(r"\$([^$]+)\$\^\{([^}]+)\}")
_RE_DOLLAR_SPLIT_SUB = re.compile(r"\$([^$]+)\$_\{([^}]+)\}")

def _fix_dollar_split_exponents(s: str) -> str:
    s = _RE_DOLLAR_SPLIT_SUPER.sub(r"$\1^{\2}$", s)
    s = _RE_DOLLAR_SPLIT_SUB.sub(r"$\1_{\2}$", s)
    return s


# Bare braced super/subscripts: "1s^{2} 2s^{2} 2p^{6}" → "$1s^{2} 2s^{2} 2p^{6}$"
# Detects ^{...} or _{...} patterns that are outside $...$ delimiters.
# Covers electron configs and any bare LaTeX notation the LLM forgot to wrap.
_RE_BARE_BRACE_NOTATION = re.compile(r"[\^_]\{[^}]+\}")

def _wrap_bare_sub_super(s: str) -> str:
    if not _RE_BARE_BRACE_NOTATION.search(s):
        return s
    if "$" not in s:
        return f"${s}$"
    # Check if the pattern exists OUTSIDE existing $...$ blocks
    non_math = _RE_DOLLAR_SEGMENT.sub("", s)
    if _RE_BARE_BRACE_NOTATION.search(non_math):
        # Partial wrapping: strip delimiters and re-wrap whole string
        stripped = _RE_DOLLAR_SEGMENT.sub(lambda m: m.group(0)[1:-1], s)
        return f"${stripped}$"
    return s


# Auto-wrap bare LaTeX: if a string contains \command but no $ delimiters,
# the LLM forgot to wrap it — enclose the whole string in $...$
# Also handles the partial case: LLM wrapped only part of the expression
# (e.g. "Apply formula: $\text{foo}$ = \frac{...}") — strips the partial
# delimiters and re-wraps the entire string.
_RE_BARE_LATEX_CMD = re.compile(r"\\[a-zA-Z]+")
_RE_DOLLAR_SEGMENT = re.compile(r"\$[^$]*\$")

def _wrap_bare_latex(s: str) -> str:
    if not _RE_BARE_LATEX_CMD.search(s):
        return s  # no LaTeX at all
    if "$" not in s:
        return f"${s}$"  # simple case: no delimiters at all
    # Check whether LaTeX commands exist OUTSIDE existing $...$ blocks
    non_math = _RE_DOLLAR_SEGMENT.sub("", s)
    if _RE_BARE_LATEX_CMD.search(non_math):
        # Partial wrapping: strip $...$ delimiters (keep content) and re-wrap all
        stripped = _RE_DOLLAR_SEGMENT.sub(lambda m: m.group(0)[1:-1], s)
        return f"${stripped}$"
    return s


def _normalize_string(s: str) -> str:
    """Apply all deterministic string fixes. Idempotent-friendly."""
    if not isinstance(s, str) or not s:
        return s
    s = _recover_tab_corrupted_latex(s)
    s = _strip_illegal_chars(s)
    s = _fix_dollar_split_exponents(s)
    s = _fix_cdot_unit_garbage(s)
    s = _fix_unbracketed_exponents(s)
    s = _fix_orphan_text(s)
    s = _fix_orphan_mathrm(s)
    s = _fix_unclosed_mathrm(s)
    s = _normalize_math_wrappers(s)
    s = _wrap_bare_sub_super(s)
    s = _wrap_bare_latex(s)
    return s


# ── Recursive walk ─────────────────────────────────────────────────────────

def _recursive_normalize(obj: Any) -> Any:
    """Recursively process dict/list and normalize every string value."""
    if isinstance(obj, str):
        return _normalize_string(obj)
    if isinstance(obj, dict):
        return {k: _recursive_normalize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_recursive_normalize(item) for item in obj]
    return obj


# ── KaTeX dry-run validator ────────────────────────────────────────────────

# Forbidden commands that often break KaTeX or are display-only
_KATEX_FORBIDDEN = re.compile(
    r"\\(?:align|aligned|begin|end|label|ref|cite|tag)\b",
    re.IGNORECASE,
)

def _balanced_braces(s: str) -> bool:
    """Return True if curly braces are balanced (ignoring escaped and inside $...$ content)."""
    depth = 0
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


def _extract_math_blocks(s: str) -> list[str]:
    """Extract content of $...$ and $$...$$ blocks (non-greedy)."""
    blocks: list[str] = []
    # $$...$$ first (block)
    for m in re.finditer(r"\$\$([^$]*)\$\$", s):
        blocks.append(m.group(1))
    # $...$ (inline)
    for m in re.finditer(r"\$([^$]*)\$", s):
        blocks.append(m.group(1))
    return blocks


def validate_math_blocks(s: str) -> tuple[bool, str]:
    """
    Lightweight KaTeX dry-run: balanced braces and no forbidden commands.
    Returns (ok, message). If ok is False, message describes the issue.
    """
    if not s:
        return True, ""
    for block in _extract_math_blocks(s):
        if not _balanced_braces(block):
            return False, f"Unbalanced braces in math block: ...{block[:50]}..."
        if _KATEX_FORBIDDEN.search(block):
            return False, f"Forbidden LaTeX command in math block: ...{block[:50]}..."
    return True, ""


def _recursive_validate_math(obj: Any, path: str = "") -> tuple[bool, str]:
    """Recursively validate all string values for math blocks."""
    if isinstance(obj, str):
        ok, msg = validate_math_blocks(obj)
        if not ok:
            return False, f"{path}: {msg}"
        return True, ""
    if isinstance(obj, dict):
        for k, v in obj.items():
            ok, msg = _recursive_validate_math(v, f"{path}.{k}" if path else k)
            if not ok:
                return False, msg
        return True, ""
    if isinstance(obj, list):
        for i, item in enumerate(obj):
            ok, msg = _recursive_validate_math(item, f"{path}[{i}]")
            if not ok:
                return False, msg
        return True, ""
    return True, ""


# ── Public API ──────────────────────────────────────────────────────────────

def normalize_strings(obj: Any) -> Any:
    """
    Apply all deterministic string fixes recursively to any JSON-serialisable
    object (dict, list, or scalar).  Safe to call on any LLM output dict.

    Fixes: \\backslash/\\text{cdotK} unit mistakes, unbracketed exponents,
    orphaned \\text/\\mathrm, tabs/ANSI/nulls,
    \\( \\) → $, and $$...$$ → $...$.
    """
    return _recursive_normalize(obj)


def validate_math_strings(obj: Any) -> tuple[bool, str]:
    """
    Recursively validate every string value for well-formed math blocks.
    Returns (True, "") on success or (False, error_message) on the first failure.
    """
    return _recursive_validate_math(obj)


def normalize_and_validate_problem(problem_dict: dict) -> dict:
    """
    Recursively normalize every string in the problem JSON and run a lightweight
    KaTeX dry-run validation. Safe for React Markdown/KaTeX frontend.

    - Fixes unbracketed exponents (10^23 → 10^{23}), orphaned \\text, tabs/ANSI,
      normalizes \\( \\) to $, and collapses $$...$$ → $...$.
    - Validates that math blocks have balanced braces and no forbidden commands.

    Raises ValueError if validation fails.
    Returns the normalized dict (new object; does not mutate input).
    """
    normalized = _recursive_normalize(problem_dict)

    # Optional: trim step labels "Label A | Label B" → "Label A"
    steps = normalized.get("steps") or []
    for step in steps:
        if isinstance(step, dict) and "label" in step and isinstance(step["label"], str):
            if " | " in step["label"]:
                step["label"] = step["label"].split(" | ")[0].strip()

    ok, msg = _recursive_validate_math(normalized)
    if not ok:
        raise ValueError(f"Markdown/LaTeX validation failed: {msg}")

    return normalized
