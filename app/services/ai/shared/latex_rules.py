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
  CORRECT: $R = 8.314 \\\\text{{ J/(mol·K)}}$  (use unicode · inside \\\\text{{}})
  CORRECT: $8.314 \\\\text{{ J/mol}}\\\\cdot\\\\text{{ K}}$  (\\\\cdot between two separate \\\\text{{}} blocks)
  NEVER: $\\\\text{{ J/(mol\\\\cdotK)}}$ — \\\\cdot is a MATH command; it is INVALID inside \\\\text{{}}.
  NEVER use $\\\\backslash$ before a unit — that prints a stray backslash glyph, not multiplication.
  NEVER write $\\\\text{{cdotK}}$ or $\\\\backslash\\\\text{{cdotK}}$ — that breaks KaTeX.
- **7. THE GAS CONSTANT RULE:** You MUST write the gas constant unit exactly like this:
  $\\\\text{{J/(mol}} \\\\cdot \\\\text{{K)}}$.
  NEVER write $\\\\cdotK$ (glued) or a bare $\\\\cdot K$ for kelvin — KaTeX treats $\\\\cdotK$ as one invalid command.
  Put a space after $\\\\cdot$ and wrap the K in $\\\\text{{...}}$.

### CRITICAL FORMATTING & LATEX RULES ###
- **8. Fractions & Division:** NEVER use a slash (/) for division in formulas, substitutions, or calculations. You MUST use vertical LaTeX fractions: $\\\\frac{{numerator}}{{denominator}}$.
  BAD: $\\\\ln(4.50 \\\\times 10^{{-3}} / 1.20 \\\\times 10^{{-3}}) = E_a / 8.314$
  GOOD: $\\\\ln\\\\left(\\\\frac{{4.50 \\\\times 10^{{-3}}}}{{1.20 \\\\times 10^{{-3}}}}\\\\right) = \\\\frac{{E_a}}{{8.314}}$
- **9. Units vs. Math:** ONLY use a slash (/) when writing units (e.g. $\\\\text{{J/mol}}$ or $\\\\text{{M/s}}$). Everything else must use $\\\\frac{{}}{{}}$. When wrapping fractions in parentheses, ALWAYS use $\\\\left($ and $\\\\right)$ so the parentheses stretch to fit a tall $\\\\frac{{}}{{}}$ (avoid raw parentheses that stay tiny next to a large fraction).
- **10. Multiplication symbol:** NEVER use the letter x or X or an asterisk * for multiplication inside LaTeX equations. You MUST ALWAYS use $\\\\times$.
  BAD: $1.15x10^{{-2}}$ or $1.15 * 10^{{-2}}$
  GOOD: $1.15 \\\\times 10^{{-2}}$

- **11. SPACES IN MATH — English words MUST use \\text{{}}:** In math mode KaTeX ignores all spaces, so bare words run together ("formulaunitstog"). Any English word or phrase inside $...$ MUST be wrapped in $\\\\text{{ }}$ with a leading space.
  WRONG: $3.20 \\\\times 10^{{22}} formula units to g$  ← renders as "formulaunitstog"
  CORRECT: $3.20 \\\\times 10^{{22}} \\\\text{{ formula units to g}}$
  This applies to unit labels, context words, and any English prose inside math.
- **12. DECIMAL LIMITS — intermediate steps max 4 decimal places:** When computing an unrounded intermediate value, NEVER output more than 4 decimal places. Truncate floating-point results (e.g. write $18.1172$, NOT $18.11723679840585$). The student only needs enough precision to round to sig figs in the final step.

- Exponents: always use braces — $10^{{23}}$ not $10^23$
- Electron configurations: write the ENTIRE config in ONE $...$
  CORRECT: "$1s^2 2s^2 2p^6 3s^2 3p^3$"
  WRONG:   "$1s^2$ $2s^2$ $2p^6$" — fragmented per subshell, breaks rendering
  WRONG:   "1s^{{2}} 2s^{{2}} 2p^{{6}}" — bare text without delimiters

BANNED CALCULATOR SYNTAX (any formula the student READS — statement, instruction, explanation, inputFields value/unit):
- NEVER plain-text math: ASCII * for multiply, ln( ) without $...$, or scientific "e" notation (8.10e-3, 1.2E+5).
  WRONG: Ea = 8.314 * ln(8.10e-3/1.20e-3) / (1/298.15 - 1/318.15)  ← renders as ugly monospace, not KaTeX.
- Use $...$ with $\\\\times$, $10^{{-3}}$, and $\\\\ln(...)$ (or $\\\\ln\\\\left(...\\\\right)$ for clarity).
- "correctAnswer" may stay short plain numbers when the UI expects typing — but any displayed setup/substitution line must be LaTeX in $...$.

JSON ESCAPING — every LaTeX backslash MUST be doubled in JSON output:
- CORRECT: \\\\text{{g/mol}}, \\\\frac{{m}}{{M}}, \\\\mathrm{{H_2O}}, \\\\times, \\\\rightarrow, \\\\sum
- WRONG:   \\text{{g/mol}}, \\frac{{m}}{{M}} — \\t is parsed as TAB, \\f as form-feed; the command is lost
- MNEMONIC: think "\\", type "\\\\" in JSON output"""
