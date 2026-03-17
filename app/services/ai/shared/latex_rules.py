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

NOTATION:
- Chemical formulas: $\\\\mathrm{{H_2O}}$, $\\\\mathrm{{NH_4NO_3}}$ — always \\\\mathrm{{}}, NOT \\\\text{{}}
- Units: inside $\\\\text{{ }}$ with a LEADING SPACE — $3.5 \\\\text{{ g/mol}}$, $63.62 \\\\text{{ amu}}$
- Exponents: always use braces — $10^{{23}}$ not $10^23$

JSON ESCAPING — every LaTeX backslash MUST be doubled in JSON output:
- CORRECT: \\\\text{{g/mol}}, \\\\frac{{m}}{{M}}, \\\\mathrm{{H_2O}}, \\\\times, \\\\rightarrow, \\\\sum
- WRONG:   \\text{{g/mol}}, \\frac{{m}}{{M}} — \\t is parsed as TAB, \\f as form-feed; the command is lost
- MNEMONIC: think "\\", type "\\\\" in JSON output"""
