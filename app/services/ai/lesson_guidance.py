"""Shared lesson context → prompt text formatting. Used by problem generation, hints, and exit tickets."""


def build_lesson_guidance_block(lesson_context: dict | None) -> str:
    """Return lesson guidance lines for prompt injection.

    Expects lesson_context with keys: equations, key_rules, misconceptions
    (same shape as ProblemDeliveryService._build_lesson_context).
    """
    if not lesson_context:
        return ""
    lines = []
    if equations := lesson_context.get("equations"):
        lines.append(f"KEY EQUATIONS: {'; '.join(equations)}")
    if key_rules := lesson_context.get("key_rules"):
        lines.append(f"KEY RULES: {'; '.join(key_rules)}")
    if misconceptions := lesson_context.get("misconceptions"):
        lines.append(f"COMMON MISCONCEPTIONS TO AVOID: {'; '.join(misconceptions)}")
    return "\n".join(lines)
