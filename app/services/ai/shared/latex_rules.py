"""
Shared LaTeX & JSON escaping rules injected into every LLM system prompt.

This string is a Python format-template fragment (uses {{...}} for literal braces)
so it can be safely embedded into any prompt that calls .format() later.

Usage:
    from app.services.ai.shared.latex_rules import SHARED_LATEX_RULES

    MY_PROMPT = "...preamble..." + SHARED_LATEX_RULES + "...more rules..."
    final = MY_PROMPT.format(placeholder=value, ...)
"""

SHARED_LATEX_RULES = """\
### LATEX & JSON ESCAPING (apply to every string field — violations break the student UI) ###

MATH DELIMITERS — use ONLY $...$ (inline math):
- NEVER $$...$$ (display math — renders oversized/centered) and NEVER \\( \\)
- EVERY LaTeX command (\\text, \\frac, \\mathrm, \\sum, \\times, \\rightarrow, etc.)
  MUST be inside $...$. A bare LaTeX command outside delimiters renders as raw broken text.
  CORRECT: $\\\\text{{Avg Atomic Mass}} = \\\\sum (\\\\text{{mass}} \\\\times \\\\text{{abundance}})$
  WRONG:   \\\\text{{Avg Atomic Mass}} = \\\\sum (...)  ← renders literally as "\\text{{...}}"

VARIABLES & EQUATIONS — ALL math must be inside $...$:
- Single variable names used mathematically: $k$, $n$, $T$, $P$, $V$, $R^2$
- Superscripts/subscripts: ALWAYS $R^2$, $k_1$, $[A]_t$ — NEVER bare R^{{2}}, k_1, [A]_t
  WRONG: R^{{2}}= 0.998; for ln|X| vs. time, R^{{2}}= 0.962  ← breaks into multiple lines
  CORRECT: $R^2 = 0.998$; for $\\\\ln|X|$ vs. time, $R^2 = 0.962$
- Full equations belong in one $...$: $R^2 = 0.998$, $[A]_t = [A]_0 e^{{-kt}}$
- Integrated rate law expressions: $[A]_t = [A]_0 - kt$ (zero), $\\\\ln[A]_t = \\\\ln[A]_0 - kt$ (first),
  $\\\\frac{{1}}{{[A]_t}} = \\\\frac{{1}}{{[A]_0}} + kt$ (second)

NOTATION:
- Chemical formulas: $\\\\mathrm{{H_2O}}$, $\\\\mathrm{{NH_4NO_3}}$ — always \\\\mathrm{{}}, NOT \\\\text{{}}
- Units: inside $\\\\text{{ }}$ with a LEADING SPACE — $3.5 \\\\text{{ g/mol}}$, $63.62 \\\\text{{ amu}}$
- Compound units (e.g. gas constant $R$): prefer ONE unit chunk
  CORRECT: $R = 8.314 \\\\text{{ J/(mol·K)}}$  OR  $8.314 \\\\text{{ J/mol}}\\\\cdot\\\\text{{ K}}$ (use $\\\\cdot$ for the dot between factors).
  NEVER use $\\\\backslash$ before a unit — that prints a stray backslash glyph, not multiplication.
  NEVER write $\\\\text{{cdotK}}$ or $\\\\backslash\\\\text{{cdotK}}$ — that breaks KaTeX; use $\\\\cdot\\\\text{{ K}}$ or combine into $\\\\text{{ J/(mol·K)}}$.
- Exponents: always use braces — $10^{{23}}$ not $10^23$
- Electron configurations: write the ENTIRE config in ONE $...$
  CORRECT: "$1s^2 2s^2 2p^6 3s^2 3p^3$"
  WRONG:   "$1s^2$ $2s^2$ $2p^6$" — fragmented per subshell, breaks rendering
  WRONG:   "1s^{{2}} 2s^{{2}} 2p^{{6}}" — bare text without delimiters

JSON ESCAPING — every LaTeX backslash MUST be doubled in JSON output:
- CORRECT: \\\\text{{g/mol}}, \\\\frac{{m}}{{M}}, \\\\mathrm{{H_2O}}, \\\\times, \\\\rightarrow, \\\\sum
- WRONG:   \\text{{g/mol}}, \\frac{{m}}{{M}} — \\t is parsed as TAB, \\f as form-feed; the command is lost
- MNEMONIC: think "\\", type "\\\\" in JSON output"""
