"""At-risk detection thresholds and per-record helper.

Shared across mastery_service, analytics_service, and aggregate_repo so the
thresholds cannot drift between layers.

L1 phase (attempts < 3, not unlocked): never at-risk — passive viewing.
L2 phase (attempts >= 3, not unlocked): at-risk if mastery < 0.30.
L3 phase (level3_unlocked): at-risk if mastery < 0.40.
"""

AT_RISK_THRESHOLD_L2: float = 0.30   # stuck in L2 after min attempts
AT_RISK_THRESHOLD_L3: float = 0.40   # no meaningful L3 progress after unlock
AT_RISK_MIN_ATTEMPTS: int = 3


def is_record_at_risk(record) -> bool:
    """Level-aware at-risk check for a single SkillMastery-like record."""
    if record.level3_unlocked:
        return record.mastery_score < AT_RISK_THRESHOLD_L3
    if record.attempts_count >= AT_RISK_MIN_ATTEMPTS:
        return record.mastery_score < AT_RISK_THRESHOLD_L2
    return False


# Band ceilings — kept here so aggregate_repo can import without touching Settings.
L1_MASTERY_CEIL: float = 0.20
L2_MASTERY_CEIL: float = 0.50
L3_MASTERY_CEIL: float = 0.80


def calculate_risk_score(mastery: float, total_attempts: int) -> float:
    """Continuous risk score [0.0, 1.0].

    mastery_risk  (70% weight): how far below ceiling mastery is.
    attempt_risk  (30% weight): many attempts with low outcome = frustration signal.
    """
    mastery_risk = min(max(1.0 - mastery, 0.0), 1.0)
    attempt_risk = min(total_attempts / 10.0, 1.0)
    return round(min(0.7 * mastery_risk + 0.3 * attempt_risk, 1.0), 4)


def level_fill_fractions(mastery_score: float) -> tuple[float, float, float]:
    """Return (l1_fill, l2_fill, l3_fill) — each a fraction in [0, 1]."""
    l1 = min(mastery_score / L1_MASTERY_CEIL, 1.0)
    l2 = max(0.0, min((mastery_score - L1_MASTERY_CEIL) / (L2_MASTERY_CEIL - L1_MASTERY_CEIL), 1.0))
    l3 = max(0.0, min((mastery_score - L2_MASTERY_CEIL) / (L3_MASTERY_CEIL - L2_MASTERY_CEIL), 1.0))
    return l1, l2, l3
