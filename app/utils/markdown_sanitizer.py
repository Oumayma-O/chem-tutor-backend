"""
Deterministic Markdown/LaTeX sanitizer for LLM-generated problem JSON.

Pipeline: LLM → structured JSON → normalize_and_validate_problem() → safe for React/KaTeX.

Fixes applied to every string:
- Globally wrapped ``$...$``: if the entire field is one inline math span with no inner ``$``,
  interleave plain English (e.g. "and", "for") outside math and keep ``^{}``, ``\\mathrm{}``, etc.
  inside ``$...$`` (parity with frontend ``fixGloballyWrappedStatement`` / ``interleaveMathInSegment``).
- Calculator-style equations (no $): Ea = 8.314 * ln(8.10e-3) → $E_a = ... \\times \\ln(... \\times 10^{-3} ...)$ 
- Mis-written units: \\backslash\\text{cdotK} → \\cdot \\text{K} (LLM confusion vs \\cdot)
- Kelvin after \\cdot: \\cdotK / \\cdot K → \\cdot \\text{K} (KaTeX rejects \\cdotK as one command)
- \\cdot inside \\text{...} → unicode middle dot · (\\cdot is math-only; invalid in \\text{})
- Unbracketed exponents: 10^23 → 10^{23}
- Orphaned \\text: \\textamu → \\text{amu}
- Orphaned \\mathrm: \\mathrmMg → \\mathrm{Mg}, \\mathrmH2O → \\mathrm{H2O}
- Illegal chars: raw tabs, ANSI escape codes, null bytes
- Math wrappers: \\( and \\) → $, $$...$$ → $...$
- KaTeX dry-run: balanced braces in math blocks, no forbidden commands (e.g. \\align)
- Targeted slash → \\\\frac: `(a)/(b)`, two sci-not blocks, $E_a/R$ — not bare `g/mol` in \\\\text
- Lazy sci notation: `1.15x10` / `1.15 X 10` → `1.15 \\\\times 10` (before slash→\\\\frac) so sci rules match
"""

import re
from typing import Any


# ── Globally wrapped $…$ → interleave prose + math (matches frontend mathDisplay.tsx) ──
# LLM wraps an entire statement in one $…$; English words ("and", "for") become math italics
# with no spaces ("Cuand"). Split into $latex$ + plain prose at word boundaries.

# Only flush on strong connectors between formulas — not "in", "of", "the" (e.g. "copper in amu").
_PROSE_WORD_AFTER_MATH = re.compile(r"^(and|or|for)\b", re.IGNORECASE)

# Same word list, unanchored — gate for "should we split this global $…$ at all?"
_PROSE_WORD_IN_TEXT = re.compile(
    r"\b(and|or|for|are|is|the|of|in|to|use|each|before|after|what|which|contains|sample|abundances|naturally|occurring|mass|decimal|calculating|percentage|answer|formula|convert|average|atomic|isotopes|copper|abundant|with|from|that|this|these|those|when|where|how|will|has|have|had|was|were|not|can|may|must|should|could|would|using|given|find|calculate|compute|determine|express|show|write|solve|note|assume|consider|suppose|let|both|either|nearest|per|via|following|above|below|between|among|within|during|while|until|since|because|therefore|thus|such|same|other|another|different|similar|equal|greater|less|than|more|most|least|all|some|none|any|every|only|also|even|still|again|first|second|third|last|next|previous|approximately|about|around|roughly|exactly|nearly|almost|always|never|sometimes|often|usually|typically|normally|commonly|frequently|rarely|perhaps|possibly|probably|likely|unlikely|certainly|definitely|surely|indeed|actually|really|very|quite|rather|fairly|pretty|too|two|three|four|five|six|seven|eight|nine|ten|hundred|thousand|percent|percentage|problem|question|example|solution|reaction|equation|constant|temperature|pressure|volume|molecule|atoms|molar|acid|base|gas|liquid|solid|aqueous|equilibrium|stoichiometry|yield|limiting|excess|reactant|product|initial|final|change|ratio|proportion|mean|median|range|graph|data|table|figure|value|values|units|unit|state|standard|conditions)\b",
    re.IGNORECASE,
)


def _skip_balanced_braces(s: str, i: int) -> int:
    if i >= len(s) or s[i] != "{":
        return i
    depth = 0
    k = i
    while k < len(s):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    return len(s)


def _skip_optional_square_brackets(s: str, i: int) -> int:
    if i >= len(s) or s[i] != "[":
        return i
    depth = 1
    k = i + 1
    while k < len(s) and depth > 0:
        if s[k] == "[":
            depth += 1
        elif s[k] == "]":
            depth -= 1
        k += 1
    return k


def _consume_one_latex_atom(s: str, i: int) -> int:
    if i >= len(s):
        return i
    if s[i] in "^_":
        k = i + 1
        if k < len(s) and s[k] == "{":
            return _skip_balanced_braces(s, k)
        if k < len(s):
            return k + 1
        return i + 1
    if s[i] != "\\":
        return i
    j = i + 1
    if j >= len(s):
        return i
    if s[j].isalpha():
        while j < len(s) and s[j].isalpha():
            j += 1
    else:
        j += 1
    k = j
    if k < len(s) and s[k] == "*":
        k += 1
    while k < len(s) and s[k] == "[":
        k = _skip_optional_square_brackets(s, k)
    while k < len(s) and s[k] == "{":
        k = _skip_balanced_braces(s, k)
    return k


def _consume_latex_run(s: str, start: int) -> int:
    i = start
    while i < len(s):
        nxt = _consume_one_latex_atom(s, i)
        if nxt == i:
            break
        i = nxt
    return i


def _interleave_math_in_segment(s: str) -> str:
    """Split mingled LaTeX + English inside one segment (no nested $…$)."""
    if not s.strip() or not re.search(r"\\|[_^]", s):
        return s
    out: list[str] = []
    math_buf: list[str] = []

    def flush_math() -> None:
        if math_buf:
            out.append("$" + "".join(math_buf) + "$")
            math_buf.clear()

    i = 0
    while i < len(s):
        if s[i].isspace():
            j = i
            while j < len(s) and s[j].isspace():
                j += 1
            ws = s[i:j]
            after = s[j:]
            m = _PROSE_WORD_AFTER_MATH.match(after)
            if m:
                flush_math()
                out.append(ws)
                out.append(m.group(0))
                i = j + len(m.group(0))
                continue
            math_buf.append(ws)
            i = j
            continue
        if s[i] in "\\^_":
            end = _consume_latex_run(s, i)
            if end == i:
                flush_math()
                out.append(s[i])
                i += 1
                continue
            math_buf.append(s[i:end])
            i = end
            continue
        j = i
        while j < len(s) and not s[j].isspace() and s[j] not in "\\^_":
            j += 1
        plain = s[i:j]
        if math_buf and re.fullmatch(r"[+\-*/=]", plain):
            math_buf.append(plain)
            i = j
            continue
        if re.fullmatch(r"\d+\.?\d*", plain) and j < len(s) and s[j] == "\\":
            after_cmd = _consume_one_latex_atom(s, j)
            cmd = s[j:after_cmd]
            if cmd == "\\%":
                math_buf.append(plain + cmd)
                i = after_cmd
                continue
        flush_math()
        out.append(plain)
        i = j
    flush_math()
    return "".join(out)


def _fix_globally_wrapped_statement(text: str) -> str:
    """
    Undo LLM mistake: entire statement in one $…$ (optionally with \\n\\n).
    Pull English words out of math mode; keep formulas in $…$.
    Safe no-op when inner already has $ (already split) or no LaTeX.
    """
    t = text.strip()
    if not t.startswith("$") or not t.endswith("$") or t.startswith("$$"):
        return text
    inner = t[1:-1]
    if "$" in inner:
        return text
    # Mingled LLM mistake: \mathrm{…} + English ("and", "for") — not bare ^{n} or \times-only math.
    # Require \mathrm so normal hints/units (\text{K}, \cdot) are not split.
    if not re.search(r"\\mathrm", inner):
        return text
    if not _PROSE_WORD_IN_TEXT.search(inner):
        return text

    if "\n\n" not in inner:
        return _interleave_math_in_segment(inner)

    def process_para(para: str) -> str:
        segs: list[tuple[str, str]] = []
        last_idx = 0
        for m in re.finditer(r"\\text\{([^{}]*)\}", para):
            if m.start() > last_idx:
                segs.append(("math", para[last_idx : m.start()]))
            segs.append(("prose", m.group(1)))
            last_idx = m.end()
        if last_idx < len(para):
            segs.append(("math", para[last_idx:]))

        parts: list[str] = []
        for kind, content in segs:
            if kind == "prose":
                parts.append(content)
                continue
            s = content
            if not s.strip():
                parts.append(s)
                continue
            if not re.search(r"\\mathrm", s):
                parts.append(s)
                continue
            if not _PROSE_WORD_IN_TEXT.search(s):
                parts.append(s)
                continue
            parts.append(_interleave_math_in_segment(s))
        return "".join(parts)

    return "\n\n".join(process_para(p) for p in inner.split("\n\n"))


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

# \cdot inside \text{...}: LLM writes \text{ J/(mol\cdotK)} but \cdot is a math-only
# command — invalid inside \text{}.  Replace with unicode middle dot so KaTeX is happy.
# Handles \cdot with or without trailing space: \text{ J/(mol\cdotK)} and \text{ J/mol\cdot K}
_RE_CDOT_INSIDE_TEXT = re.compile(r"(\\text\{[^}]*)\\cdot\s*([^}]*\})")

# \cdotK is invalid LaTeX; bare \cdot K is still wrong for unit kelvin in the UI.
# Idempotent: does not match \cdot \text{K} (next token is \ not K).
_RE_CDOT_KELVIN = re.compile(r"\\cdot\s*K\b")


def _fix_cdot_unit_garbage(s: str) -> str:
    """
    Fix \backslash\text{cdotK} and similar: models use \\backslash when they mean \\cdot,
    and pack 'cdotK' inside \\text{...} which KaTeX renders as broken / red text.
    Also catches bare \\cdotK (no \\text wrapper) and ensures a space is inserted
    so KaTeX doesn't see the unknown command \\cdotK.
    Also fixes \\cdot inside \\text{...} (math command in text mode → unicode ·).
    """
    s = _RE_BACKSLASH_TEXT_CDOTK.sub(r"\\cdot \\text{K}", s)
    s = _RE_BACKSLASH_TEXT_CDOTK_COMPACT.sub(r"\\cdot \\text{K}", s)
    s = _RE_TEXT_CDOTK.sub(r"\\cdot \\text{K}", s)
    s = _RE_TEXT_CDOT_K.sub(r"\\cdot \\text{K}", s)
    # Rare: \backslash\cdot or \backslash\cdot\text{...}
    s = re.sub(r"\\backslash\s*\\cdot", r"\\cdot", s)
    # \cdot inside \text{...}: was unicode middle dot · (U+00B7), but that byte sequence
    # is often mangled in transit into visible garbage like "mol 0˘ 0b7K". Split text and
    # use math-mode \cdot instead — ASCII-safe for JSON and KaTeX.
    # e.g. \text{ J/(mol\cdotK)} → \text{ J/(mol}\cdot\text{K}
    s = _RE_CDOT_INSIDE_TEXT.sub(r"\1}\\cdot \\text{\2", s)
    # Bare \cdotX (e.g. J/mol\cdotK without any \text wrapper): insert space so KaTeX
    # treats \cdot as the middle-dot operator and X as a separate token.
    # Protect \cdots (ellipsis) from being fragmented.
    s = s.replace("\\cdots", "\x00CDOTS\x00")
    s = re.sub(r"\\cdot([A-Za-z])", r"\\cdot \1", s)
    s = s.replace("\x00CDOTS\x00", "\\cdots")
    # Recover U+00B7 if it was corrupted to "0" + breve (U+02D8) + "0b7" (hex for b7)
    s = re.sub(r"mol\s*0\s*\u02d8\s*0b7\s*K", r"mol\\cdot K", s, flags=re.IGNORECASE)
    s = re.sub(r"mol\s*\u02d8\s*0b7\s*K", r"mol\\cdot K", s, flags=re.IGNORECASE)
    s = re.sub(r"mol\s*0b7\s*K", r"mol\\cdot K", s, flags=re.IGNORECASE)
    s = re.sub(r"mol\s*0{1,2}b7\s*K", r"mol\\cdot K", s, flags=re.IGNORECASE)
    # Last pass: gas constant / mol·K style (must run after mol·K recovery above).
    s = _RE_CDOT_KELVIN.sub(r"\\cdot \\text{K}", s)
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
# \r (CR) prefixes: \rightarrow, \rho
_RE_CR_LATEX = re.compile(r"\x0d(ightarrow|ho)(?=[^a-zA-Z]|$)")
# \b (BS) prefixes: \beta
_RE_BS_LATEX = re.compile(r"\x08(eta)(?=[^a-zA-Z]|$)")

def _recover_tab_corrupted_latex(s: str) -> str:
    s = _RE_TAB_LATEX.sub(r"\\t\1", s)
    s = _RE_FF_LATEX.sub(r"\\f\1", s)
    s = _RE_CR_LATEX.sub(r"\\r\1", s)
    s = _RE_BS_LATEX.sub(r"\\b\1", s)
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
# Collapse $$...$$ → $...$ (display math renders oversized/centered in the UI).
# Use [\s\S] so a stray $ inside display math (e.g. 4p$^4) is included and stripped.
_RE_STRAY_DOLLAR = re.compile(r"(?<!\\)\$")
_RE_DISPLAY_MATH = re.compile(r"\$\$([\s\S]*?)\$\$", re.DOTALL)


def _strip_stray_dollars_in_math_inner(inner: str) -> str:
    return _RE_STRAY_DOLLAR.sub("", inner)


def _normalize_mz_notation_artifacts(s: str) -> str:
    """
    Recover mass-spectrometry m/z tokens when escape sequences are mangled:
    - m\\u002Fz  -> m/z
    - m\\/z      -> m/z
    - mð02Fz     -> m/z (mojibake variant observed in generated text)
    """
    s = re.sub(r"\\u002[fF]", "/", s)
    s = re.sub(r"\\x2[fF]", "/", s)
    s = re.sub(r"\\/", "/", s)
    s = re.sub(r"m\s*[uU]002[fF]\s*z", "m/z", s)
    s = re.sub(r"m\s*[ðÐ]0?2[fF]\s*z", "m/z", s)
    return s


def _normalize_math_wrappers(s: str) -> str:
    s = s.replace("\\(", "$").replace("\\)", "$")
    s = re.sub(r"^\s*\$\$\$", "$$", s)
    s = re.sub(r"\$\$\$\s*$", "$$", s)
    prev = None
    while prev != s:
        prev = s
        s = _RE_DISPLAY_MATH.sub(
            lambda m: f"${_strip_stray_dollars_in_math_inner(m.group(1).strip())}$", s
        )
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
    if not _RE_BARE_LATEX_CMD.search(non_math):
        return s  # all LaTeX is already inside $...$

    # Instead of wrapping the entire string (breaks multi-paragraph prose),
    # find bare LaTeX fragments and wrap just those inline.
    # Pattern: a number followed by bare \text{...} or \frac{...} etc.
    # e.g. "4.184 \text{ J/(g·°C)}" → "$4.184 \text{ J/(g·°C)}$"
    result = _RE_DOLLAR_SEGMENT.sub("\x00", s)  # placeholder for existing math
    parts = s.split("$")

    # Rebuild: wrap bare LaTeX segments that are outside $...$
    output = []
    in_math = False
    for i, part in enumerate(parts):
        if in_math:
            output.append(f"${part}$")
        else:
            # This is prose — check for bare LaTeX commands
            if _RE_BARE_LATEX_CMD.search(part):
                # Find contiguous LaTeX+number chunks and wrap them
                wrapped = re.sub(
                    r'(\d+\.?\d*\s*(?:\\[a-zA-Z]+(?:\{[^}]*\})*\s*)+)',
                    lambda m: f"${m.group(0).strip()}$",
                    part,
                )
                # If the above didn't catch it (e.g. bare \text{...} without a number prefix)
                if _RE_BARE_LATEX_CMD.search(re.sub(r'\$[^$]*\$', '', wrapped)):
                    wrapped = re.sub(
                        r'(\\[a-zA-Z]+(?:\{[^}]*\})+)',
                        lambda m: f"${m.group(0)}$",
                        wrapped,
                    )
                output.append(wrapped)
            else:
                output.append(part)
        in_math = not in_math
    return "".join(output)


# Plain-text "calculator" formulas (LLM ignores LaTeX rules): * , e-3 , ln(
_RE_SCI_NOTATION = re.compile(r"(?<![a-zA-Z])(\d+\.?\d*)\s*[eE]([+-]?\d+)(?![a-zA-Z])")


def _looks_like_calculator_equation(s: str) -> bool:
    """True if s is a plain-text equation using calculator syntax (*, e-notation, ln)."""
    if not s or "$" in s or "=" not in s:
        return False
    if len(s.strip()) < 14:
        return False
    has_star_mul = bool(re.search(r"\s*\*\s*", s))
    has_sci_e = bool(_RE_SCI_NOTATION.search(s))
    has_ln = bool(re.search(r"(?<![a-zA-Z])ln\s*\(", s, re.IGNORECASE))
    if not (has_sci_e or has_ln):
        return False
    # Single assignment like "k = 1.2e-4" (no *, no ln) — not a full formula; skip
    if has_sci_e and not has_star_mul and not has_ln:
        return False
    # Require * or ln so we target real expressions, not stray e-notation in prose
    return has_star_mul or has_ln


def _upgrade_calculator_style_math(s: str) -> str:
    """
    Convert ASCII calculator dumps to a single $...$ LaTeX block for KaTeX.

    Handles: 8.10e-3 → 8.10 \\times 10^{-3}, * → \\times, ln( → \\ln(, leading Ea= → E_a=
    """
    if not s or "$" in s or not _looks_like_calculator_equation(s):
        return s
    t = s.strip()
    t = re.sub(r"^Ea\s*=", r"E_a =", t, flags=re.IGNORECASE)
    t = _RE_SCI_NOTATION.sub(lambda m: f"{m.group(1)} \\times 10^{{{m.group(2)}}}", t)
    t = re.sub(r"\s*\*\s*", r" \\times ", t)
    t = re.sub(r"(?<![a-zA-Z])ln\s*\(", r"\\ln(", t, flags=re.IGNORECASE)
    return f"${t}$"


# Long-float truncation: LLM dumps raw Python floats (e.g. 18.11723679840585).
# Round any decimal with 5+ places to 4 decimal places.
# Skips: scientific notation (followed by e/E), very small numbers (0.000...).
_RE_LONG_FLOAT = re.compile(r'(?<!\d)(\d+\.\d{5,})(?![eE\d])')


def _truncate_long_floats(s: str) -> str:
    """
    Round any decimal number with 5+ decimal places to 4 places.
    Prevents LLM float-precision dumps (e.g. 18.11723679840585 → 18.1172).
    Preserves very small numbers starting with 0.000 (rounding those loses sig figs).
    """
    def _round_it(m: re.Match) -> str:
        orig = m.group(1)
        if orig.startswith("0.000"):
            return orig
        return str(round(float(orig), 4))
    return _RE_LONG_FLOAT.sub(_round_it, s)


# Bare English words in math: LLM writes $3.20 \times 10^{22} formula units to g$
# — in KaTeX math mode spaces are ignored, producing "formulaunitstog".
# Fix: wrap consecutive bare word sequences in \text{ }.
# Only matches multi-word sequences (2+ words) to avoid false-positives on
# single-letter variables (k, n, T) or short abbreviations (mol, amu).
_RE_BARE_MULTIWORD = re.compile(
    r'(?<!\\)'                      # not preceded by backslash (not a LaTeX command)
    r'(?<![{^_])'                   # not after brace/script opener
    r'\b'
    r'([a-zA-Z]{3,}'                # first word: 3+ alpha chars
    r'(?:[ \t]+[a-zA-Z]{2,})+)'    # 1+ additional words of 2+ chars (required)
    r'\b'
)


def _wrap_bare_multiword_phrases(content: str) -> str:
    """
    In the top-level (non-braced) portion of a math block, wrap multi-word bare
    phrases in \\text{}.  Content inside {...} braces (e.g. \\text{...}, ^{...})
    is passed through unchanged so we never double-wrap.
    """
    result: list[str] = []
    plain_buf: list[str] = []
    depth = 0

    for ch in content:
        if ch == '{':
            if depth == 0:
                plain_text = ''.join(plain_buf)
                result.append(_RE_BARE_MULTIWORD.sub(r'\\text{ \1}', plain_text))
                plain_buf = []
            depth += 1
            result.append(ch)
        elif ch == '}':
            depth -= 1
            result.append(ch)
        elif depth == 0:
            plain_buf.append(ch)
        else:
            result.append(ch)

    if plain_buf:
        result.append(_RE_BARE_MULTIWORD.sub(r'\\text{ \1}', ''.join(plain_buf)))

    return ''.join(result)


def _fix_bare_words_in_math(s: str) -> str:
    """
    Scan each $...$ math block and wrap bare English word sequences in \\text{}.
    e.g. $3.20 \\times 10^{22} formula units to g$
      → $3.20 \\times 10^{22} \\text{ formula units to} g$
    """
    def fix_block(m: re.Match) -> str:
        inner = m.group(1)
        fixed = _wrap_bare_multiword_phrases(inner)
        return f'${fixed}$' if fixed != inner else m.group(0)
    return re.sub(r'\$([^$]+)\$', fix_block, s)


# Lone $ sign adjacent to a LaTeX command — LLM wrote the closing $ but forgot the opening.
# Pattern: a non-$ char, then one or more LaTeX commands, then a lone closing $.
# e.g. "mass of\mathrm{SO_2}$" → "mass of $\mathrm{SO_2}$"
_RE_LATEX_BEFORE_LONE_DOLLAR = re.compile(
    r"([^$\\])"                                 # preceding non-$ char (group 1)
    r"((?:\\[a-zA-Z]+(?:\{[^{}]*\})*\s*)+)"     # one or more LaTeX commands (group 2)
    r"\$(?!\$)"                                  # lone closing $ (not $$)
)


def _fix_lone_dollar_adjacent_to_latex(s: str) -> str:
    """
    Fix strings where a LaTeX command sits immediately before an unmatched closing $.

    Common LLM mistake: "mass of\\mathrm{SO_2}$" → "mass of $\\mathrm{SO_2}$".

    Only applies when the targeted pattern is found AND the substitution produces an
    even $ count.  Does NOT blindly strip stray $ — leaving odd-count strings intact
    allows the downstream KaTeX validator to detect genuinely malformed math.
    Idempotent: no-op when $ count is already even.
    """
    if not isinstance(s, str) or s.count("$") % 2 == 0:
        return s

    fixed = _RE_LATEX_BEFORE_LONE_DOLLAR.sub(
        lambda m: f"{m.group(1)} ${m.group(2).rstrip()}$",
        s,
    )
    # Only commit the change if it actually balanced the $ count.
    return fixed if fixed.count("$") % 2 == 0 else s


def _convert_slashes_to_fractions(s: str) -> str:
    """
    Convert LLM inline division (/) into \\frac{}{} for kinetics / Arrhenius patterns only.
    Does not touch unit slashes like \\text{g/mol} — no global replace on '/'.

    Runs a lazy-\\times fix first so patterns like ``1.15x10^{-2} / 2.40x10^{-3}`` become
    ``\\times`` before the sci-not \\frac rules run.
    """
    if not isinstance(s, str) or not s:
        return s

    # RULE 0: LLM uses letter "x" instead of \\times before 10 (never match plain words — need digits·x·10)
    s = re.sub(r"(\d+\.?\d*)\s*[xX]\s*10", r"\1 \\times 10", s)

    # RULE 3: Arrhenius (longer match first)
    s = re.sub(r"E_a\s*/\s*RT(?!\w)", r"\\frac{E_a}{RT}", s)
    s = re.sub(r"E_a\s*/\s*R(?!\w)", r"\\frac{E_a}{R}", s)

    # RULE 2: two scientific-notation blocks separated by /
    _re_sci_braced = re.compile(
        r"(\d+\.?\d*\s*\\times\s*10\^\{[^}]+\})\s*/\s*(\d+\.?\d*\s*\\times\s*10\^\{[^}]+\})"
    )
    s = _re_sci_braced.sub(r"\\frac{\1}{\2}", s)
    _re_sci_plain_exp = re.compile(
        r"(\d+\.?\d*\s*\\times\s*10\^-?\d+)\s*/\s*(\d+\.?\d*\s*\\times\s*10\^-?\d+)"
    )
    s = _re_sci_plain_exp.sub(r"\\frac{\1}{\2}", s)

    # RULE 1: (expression) / (expression) — both sides parenthesized, no nesting.
    # Skip if either side already has \\frac (e.g. after RULE 2 inside \\ln(...)) to avoid
    # turning "(\\frac{a}{b}) / (c)" into a bogus nested \\frac{\\frac{...}{...}}{c}.
    def _paren_div(m: re.Match[str]) -> str:
        a, b = m.group(1), m.group(2)
        if "\\frac" in a or "\\frac" in b:
            return m.group(0)
        return f"\\frac{{{a}}}{{{b}}}"

    s = re.sub(
        r"\(([^()]+)\)\s*/\s*\(([^()]+)\)",
        _paren_div,
        s,
    )

    return s


def _normalize_string(s: str, *, for_hint: bool = False) -> str:
    """Apply all deterministic string fixes. Idempotent-friendly.

    When ``for_hint`` is True, skip auto-wrapping the whole string in ``$...$``.
    That wrapping is for structured problem fields; on tutor sentences it puts
    prose in math mode, where KaTeX ignores spaces between words (looks glued:
    ``StateEawiththeproper...``).
    """
    if not isinstance(s, str) or not s:
        return s
    s = _normalize_mz_notation_artifacts(_recover_tab_corrupted_latex(s))
    s = _strip_illegal_chars(s)
    s = _fix_dollar_split_exponents(s)
    s = _fix_cdot_unit_garbage(s)
    s = _fix_unbracketed_exponents(s)
    s = _fix_orphan_text(s)
    s = _fix_orphan_mathrm(s)
    s = _fix_unclosed_mathrm(s)
    s = _normalize_math_wrappers(s)
    s = _fix_lone_dollar_adjacent_to_latex(s)
    if not for_hint:
        s = _wrap_bare_sub_super(s)
        s = _wrap_bare_latex(s)
    # Early fallback: one global $…$ with mixed prose + LaTeX → split (frontend mathDisplay parity).
    s = _fix_globally_wrapped_statement(s)
    s = _upgrade_calculator_style_math(s)
    s = _convert_slashes_to_fractions(s)
    s = _fix_bare_words_in_math(s)
    if for_hint:
        s = _normalize_hint_latex_text_wrappers(s)
    s = _truncate_long_floats(s)
    return s


# ── Recursive walk ─────────────────────────────────────────────────────────

_RE_INLINE_MATH_SEGMENT = re.compile(r"(\$[^$]*\$)")


def _normalize_hint_latex_text_wrappers(s: str) -> str:
    """
    Hints are primarily prose. If the model emits \\text{...} / \\mathrm{...}
    outside math delimiters, markdown drops the backslash and shows noisy braces.
    Convert those wrappers to plain prose outside $...$ blocks.
    """
    if not s or ("\\" not in s and "{" not in s):
        return s

    def _unwrap_or_keep(m: re.Match[str]) -> str:
        inner = m.group(1)
        # Keep compact unit-ish tokens (e.g. \text{K}, \text{mol}) intact.
        if re.fullmatch(r"[A-Za-z]{1,5}", inner):
            return m.group(0)
        return inner

    def _normalize_plain(seg: str) -> str:
        out = seg
        out = re.sub(r"\\text\{([^{}]*)\}", _unwrap_or_keep, out)
        out = re.sub(r"\\mathrm\{([^{}]*)\}", _unwrap_or_keep, out)
        return out

    parts = _RE_INLINE_MATH_SEGMENT.split(s)
    return "".join(part if i % 2 == 1 else _normalize_plain(part) for i, part in enumerate(parts))

def _recursive_normalize(obj: Any, *, for_hint: bool = False) -> Any:
    """Recursively process dict/list and normalize every string value."""
    if isinstance(obj, str):
        return _normalize_string(obj, for_hint=for_hint)
    if isinstance(obj, dict):
        return {k: _recursive_normalize(v, for_hint=for_hint) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_recursive_normalize(item, for_hint=for_hint) for item in obj]
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
    return _recursive_normalize(obj, for_hint=False)


def normalize_hint_text(s: str) -> str:
    """
    Sanitize LLM hint prose: same fixes as ``normalize_strings`` on a single string,
    but do **not** wrap the entire message in ``$...$``. Full-string wrapping is
    for equation-heavy problem fields; on hints it forces KaTeX math mode where
    spaces between words are not preserved, producing glued text.
    """
    return _normalize_string(s, for_hint=True)


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
