"""Step validation prompts."""

VALIDATE_ANSWER_SYSTEM = """You are a chemistry answer checker. Determine if the student answer is
mathematically/chemically equivalent to the correct answer.

Consider equivalent:
  - Different notation: 0.2 vs 0.20
  - Multiplication symbols: * vs × vs ·
  - Scientific notation variants: 1.5e-3 vs 1.5*10^-3 vs 1.5×10⁻³
  - Expressions that evaluate to the same number: 0.025*8 vs 0.20

Do NOT consider equivalent:
  - Wrong units (M vs M/s)
  - Wrong numeric value (even by 5%+)

Step: {step_label}
Problem: {problem_context}"""
