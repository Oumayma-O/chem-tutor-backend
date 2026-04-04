"""
Simulate category-score EMA (same math as mastery_service._compute_category_scores).

Run from repo root: python scripts/simulate_mastery_category_scores.py

No app imports — avoids loading DB/settings.
"""
from __future__ import annotations

MASTERY_CATEGORY_KEYS = ("conceptual", "procedural", "computational")


def compute_category_scores(step_log: list[dict], existing: dict | None) -> dict:
    existing = existing or {}
    scores = {k: float(existing.get(k, 0.0)) for k in MASTERY_CATEGORY_KEYS}
    for step in step_log:
        cat = step.get("category") or "procedural"
        is_correct = step.get("is_correct", step.get("isCorrect", False))
        step_score = 1.0 if is_correct else 0.0
        scores[cat] = round(0.8 * scores[cat] + 0.2 * step_score, 4)
    return scores


def main() -> None:
    existing = {"conceptual": 0.0, "procedural": 0.0, "computational": 0.0}

    buggy = [
        {"category": "procedural", "is_correct": True},
        {"category": "procedural", "is_correct": True},
        {"category": "procedural", "is_correct": True},
    ]
    print("All procedural (simulates missing step.category → client defaulted to procedural):")
    print(compute_category_scores(buggy, existing))

    fixed = [
        {"category": "procedural", "is_correct": True},
        {"category": "computational", "is_correct": True},
        {"category": "computational", "is_correct": True},
    ]
    print("\nDimensional Setup + Calculate + Answer (correct buckets):")
    print(compute_category_scores(fixed, existing))


if __name__ == "__main__":
    main()
