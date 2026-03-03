"""
MasteryService — pure business logic for mastery computation and adaptive progression.

No LLM calls live here. This is deterministic, testable Python.

Design decisions:
  - Rolling window average (configurable, default 5) rather than EWMA to make
    the threshold transparent to teachers.
  - Difficulty adapts one level at a time to avoid oscillation.
  - At-risk threshold is set at mastery < 0.4 after at least 3 attempts.
  - Level 3 unlock: permanent once a student scores 1.0 (all steps correct) on
    a single Level 2 attempt.  Stored as a one-way latch in SkillMastery.level3_unlocked.
"""

import uuid
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.mastery import CategoryScores, MasteryState, ProgressionDecision
from app.infrastructure.database.models import ProblemAttempt, SkillMastery
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository

logger = get_logger(__name__)
settings = get_settings()

_DIFFICULTY_LADDER = ["easy", "medium", "hard"]
_AT_RISK_THRESHOLD = 0.4
_AT_RISK_MIN_ATTEMPTS = 3


class MasteryService:
    def __init__(
        self,
        mastery_repo: MasteryRepository,
        attempt_repo: AttemptRepository,
        misconception_repo: MisconceptionRepository,
    ) -> None:
        self._mastery = mastery_repo
        self._attempts = attempt_repo
        self._misconceptions = misconception_repo

    # ── Start Attempt ─────────────────────────────────────────

    async def start_attempt(
        self,
        user_id: uuid.UUID,
        chapter_id: str,
        topic_index: int,
        problem_id: str,
        difficulty: str = "medium",
        level: int = 2,
        class_id: uuid.UUID | None = None,
    ) -> ProblemAttempt:
        attempt = ProblemAttempt(
            user_id=user_id,
            class_id=class_id,
            chapter_id=chapter_id,
            topic_index=topic_index,
            problem_id=problem_id,
            difficulty=difficulty,
            level=level,
            step_log=[],
        )
        return await self._attempts.add(attempt)

    # ── Complete Attempt & Recompute Mastery ──────────────────

    async def complete_attempt(
        self,
        attempt_id: uuid.UUID,
        user_id: uuid.UUID,
        chapter_id: str,
        topic_index: int,
        score: float,
        step_log: list[dict],
        level: int = 2,
    ) -> ProgressionDecision:
        """
        Called when a student finishes a problem.
        1. Persists the completed attempt.
        2. Recomputes mastery from recent scores.
        3. Adapts difficulty.
        4. Checks and persists Level 3 unlock (one-way latch).
        5. Returns a ProgressionDecision.
        """
        await self._attempts.mark_complete(attempt_id, score, step_log)

        # Pull recent scores from DB (includes this attempt)
        recent = await self._attempts.get_recent_scores(
            user_id, chapter_id, topic_index, window=settings.mastery_window
        )

        # Load or create mastery record
        mastery_record = await self._mastery.get_for_topic(user_id, chapter_id, topic_index)
        if mastery_record is None:
            mastery_record = SkillMastery(
                user_id=user_id,
                chapter_id=chapter_id,
                topic_index=topic_index,
            )

        # Was L3 already unlocked before this attempt?
        was_already_unlocked = mastery_record.level3_unlocked

        # Aggregate error counts from step_log
        error_counts = _aggregate_errors(step_log, mastery_record.error_counts)

        # Compute per-category scores from step_log
        category_scores = _compute_category_scores(step_log, mastery_record.category_scores)

        # Compute new mastery
        new_mastery = _compute_mastery(recent)
        consecutive = _update_consecutive(mastery_record.consecutive_correct, score)
        new_difficulty = _adapt_difficulty(
            current=mastery_record.current_difficulty,
            mastery=new_mastery,
            consecutive=consecutive,
            threshold=settings.mastery_threshold,
        )

        # Determine Level 3 unlock
        # Condition: student answers ALL steps correctly in a single Level 2 attempt
        # (score == 1.0 at level 2).  Once true, the flag is permanent (one-way latch).
        qualifies_for_l3 = (score >= 1.0 and level == 2)
        level3_unlocked = was_already_unlocked or qualifies_for_l3
        level3_just_unlocked = level3_unlocked and not was_already_unlocked
        level3_unlocked_at = mastery_record.level3_unlocked_at
        if level3_just_unlocked:
            level3_unlocked_at = datetime.utcnow()

        # Persist
        mastery_record.mastery_score = new_mastery
        mastery_record.attempts_count = mastery_record.attempts_count + 1
        mastery_record.consecutive_correct = consecutive
        mastery_record.current_difficulty = new_difficulty
        mastery_record.error_counts = error_counts
        mastery_record.category_scores = category_scores
        mastery_record.recent_scores = list(recent)
        mastery_record.level3_unlocked = level3_unlocked
        mastery_record.level3_unlocked_at = level3_unlocked_at
        mastery_record.updated_at = datetime.utcnow()

        saved = await self._mastery.upsert(mastery_record)

        # should_advance: student is ready to move to the next topic
        # (rolling mastery >= threshold, independent of level)
        should_advance = new_mastery >= settings.mastery_threshold

        state = _to_mastery_state(saved, settings.mastery_threshold)

        logger.info(
            "mastery_updated",
            user=str(user_id),
            chapter=chapter_id,
            topic=topic_index,
            mastery=f"{new_mastery:.2%}",
            difficulty=new_difficulty,
            level3_unlocked=level3_unlocked,
            level3_just_unlocked=level3_just_unlocked,
            should_advance=should_advance,
        )

        return ProgressionDecision(
            mastery=state,
            attempt_score=score,
            should_advance=should_advance,
            level3_just_unlocked=level3_just_unlocked,
            recommended_next_difficulty=new_difficulty,
            feedback_message=_feedback_message(
                new_mastery, score, settings.mastery_threshold, level3_just_unlocked
            ),
        )

    # ── Read Mastery ──────────────────────────────────────────

    async def get_mastery(
        self,
        user_id: uuid.UUID,
        chapter_id: str,
        topic_index: int,
    ) -> MasteryState | None:
        record = await self._mastery.get_for_topic(user_id, chapter_id, topic_index)
        if record is None:
            return None
        return _to_mastery_state(record, settings.mastery_threshold)

    async def is_at_risk(self, user_id: uuid.UUID, chapter_id: str) -> bool:
        """Returns True if the student is struggling across the chapter."""
        records = await self._mastery.get_all_for_user(user_id)
        chapter_records = [r for r in records if r.chapter_id == chapter_id]
        if not chapter_records:
            return False
        eligible = [
            r for r in chapter_records
            if r.attempts_count >= _AT_RISK_MIN_ATTEMPTS
        ]
        if not eligible:
            return False
        avg = sum(r.mastery_score for r in eligible) / len(eligible)
        return avg < _AT_RISK_THRESHOLD


# ── Pure functions (easy to unit-test) ───────────────────────

def _compute_mastery(recent_scores: list[float]) -> float:
    """Rolling window average. Returns 0.0 if no data — progress bars start empty."""
    if not recent_scores:
        return 0.0
    return sum(recent_scores) / len(recent_scores)


def _update_consecutive(current: int, score: float) -> int:
    """Increment consecutive correct if score >= 0.8, else reset."""
    return current + 1 if score >= 0.8 else 0


def _adapt_difficulty(
    current: str,
    mastery: float,
    consecutive: int,
    threshold: float,
) -> str:
    idx = _DIFFICULTY_LADDER.index(current) if current in _DIFFICULTY_LADDER else 1

    if mastery >= threshold and consecutive >= 2:
        # Level up, but not past hard
        return _DIFFICULTY_LADDER[min(idx + 1, len(_DIFFICULTY_LADDER) - 1)]
    elif mastery < threshold - 0.15:
        # Level down, but not past easy
        return _DIFFICULTY_LADDER[max(idx - 1, 0)]

    return current


def _aggregate_errors(step_log: list[dict], existing: dict) -> dict:
    """Merge new step errors into the existing error_counts JSONB."""
    counts = dict(existing or {})
    for step in step_log:
        if not step.get("isCorrect") and (cat := step.get("errorCategory")):
            counts[cat] = counts.get(cat, 0) + 1
    return counts


def _compute_category_scores(
    step_log: list[dict],
    existing: dict,
) -> dict:
    """
    Update per-category mastery scores from this attempt's step log.

    Each step may carry a "reasoningPattern" key (set by ThinkingAnalysisService
    after classification). We do a simple rolling update: 80% existing + 20% new.

    Returns a dict compatible with the CategoryScores schema.
    """
    _PATTERN_TO_CATEGORY = {
        "Conceptual": "conceptual",
        "Procedural": "procedural",
        "Substitution": "procedural",
        "Arithmetic": "computational",
        "Units": "computational",
        "Symbolic": "representation",
    }

    # Start from existing scores (or defaults of 0.0 for new users)
    scores = {
        "conceptual":     existing.get("conceptual", 0.0),
        "procedural":     existing.get("procedural", 0.0),
        "computational":  existing.get("computational", 0.0),
        "representation": existing.get("representation", 0.0),
    }

    for step in step_log:
        pattern = step.get("reasoningPattern")
        cat = _PATTERN_TO_CATEGORY.get(pattern) if pattern else None
        if cat is None:
            continue
        is_correct = step.get("isCorrect", False)
        step_score = 1.0 if is_correct else 0.0
        # Exponential moving average: 80% history + 20% new
        scores[cat] = round(0.8 * scores[cat] + 0.2 * step_score, 4)

    return scores


def _feedback_message(
    mastery: float,
    score: float,
    threshold: float,
    level3_just_unlocked: bool,
) -> str:
    if level3_just_unlocked:
        return "Level 3 unlocked! You've demonstrated mastery — time for independent practice."
    if score >= 1.0:
        return "Perfect! Every step correct."
    if score >= 0.8:
        return "Great work — nearly there!"
    if mastery >= threshold:
        return f"You've reached mastery ({mastery:.0%}). Ready to advance!"
    remaining = threshold - mastery
    return f"Keep going — you need {remaining:.0%} more to advance."


def _to_mastery_state(record: SkillMastery, threshold: float) -> MasteryState:
    cat = record.category_scores or {}
    return MasteryState(
        user_id=record.user_id,
        chapter_id=record.chapter_id,
        topic_index=record.topic_index,
        mastery_score=record.mastery_score,
        attempts_count=record.attempts_count,
        consecutive_correct=record.consecutive_correct,
        current_difficulty=record.current_difficulty,
        error_counts=record.error_counts or {},
        recent_scores=record.recent_scores or [],
        category_scores=CategoryScores(
            conceptual=cat.get("conceptual", 0.0),
            procedural=cat.get("procedural", 0.0),
            computational=cat.get("computational", 0.0),
            representation=cat.get("representation", 0.0),
        ),
        updated_at=record.updated_at,
        has_mastered=record.mastery_score >= threshold,
        level3_unlocked=record.level3_unlocked,
        level3_unlocked_at=record.level3_unlocked_at,
        should_advance=record.mastery_score >= threshold,
        recommended_difficulty=record.current_difficulty,
    )
