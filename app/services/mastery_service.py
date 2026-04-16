"""
MasteryService — pure business logic for mastery computation and adaptive progression.

No LLM calls live here. This is deterministic, testable Python.

Design decisions:
  - Band-filling mastery across three practice bands + exit ticket:
      L1 (0 → l1_ceiling), L2 (l1_ceiling → l2_ceiling), L3 (l2_ceiling → l3_ceiling).
      Exit ticket fills the top band (l3_ceiling → 1.0) via mastery_bridge.py.
  - Difficulty adapts from mastery position within the L2 band.
  - At-risk: mastery < 0.4 after at least 3 attempts (unit-level struggle).
  - Level 3 unlock: one perfect L2 attempt (score 1.0) — gate to access L3; score measures practice.
  - should_advance / has_mastered: true when mastery_score >= l3_mastery_ceiling (lesson done).
"""

import asyncio
import uuid
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import get_logger
from app.domain.schemas.dashboards import CategorySnapshot, ClassSummaryStats, MasterySnapshot
from app.domain.schemas.mastery import CategoryScores, MasteryState, ProgressionDecision
from app.infrastructure.database.models import ProblemAttempt, SkillMastery
from app.services.ai.shared.blueprints import (
    LABEL_TO_MASTERY_CATEGORY,
    MASTERY_CATEGORY_KEYS,
    VALID_MASTERY_CATEGORIES,
)
from app.infrastructure.database.repositories.attempt_repo import (
    AttemptRepository,
    MisconceptionRepository,
)
from app.infrastructure.database.repositories.mastery_repo import MasteryRepository

logger = get_logger(__name__)
settings = get_settings()

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
        unit_id: str,
        lesson_index: int,
        problem_id: str,
        difficulty: str = "medium",
        level: int = 2,
        class_id: uuid.UUID | None = None,
    ) -> ProblemAttempt:
        attempt = ProblemAttempt(
            user_id=user_id,
            class_id=class_id,
            unit_id=unit_id,
            lesson_index=lesson_index,
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
        unit_id: str,
        lesson_index: int,
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

        # Pull per-level scores for band-filling computation
        l1_scores, l2_scores, l3_scores = await self._fetch_band_scores(user_id, unit_id, lesson_index)

        # Load or create mastery record
        mastery_record = await self._mastery.get_for_lesson(user_id, unit_id, lesson_index)
        if mastery_record is None:
            mastery_record = _default_skill_mastery(user_id, unit_id, lesson_index)

        # Was L3 already unlocked before this attempt?
        was_already_unlocked = mastery_record.level3_unlocked

        # Aggregate error counts from step_log
        error_counts = _aggregate_errors(step_log, mastery_record.error_counts)

        # Compute per-category scores from step_log
        category_scores = _compute_category_scores(step_log, mastery_record.category_scores)

        # Compute new mastery using band-filling across L1, L2, and L3
        new_mastery = _compute_mastery_banded(l1_scores, l2_scores, l3_scores)
        consecutive = _update_consecutive(mastery_record.consecutive_correct, score)
        new_difficulty = _difficulty_from_mastery(new_mastery)

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
        mastery_record.recent_scores = list(l1_scores + l2_scores + l3_scores)
        mastery_record.level3_unlocked = level3_unlocked
        mastery_record.level3_unlocked_at = level3_unlocked_at
        mastery_record.updated_at = datetime.utcnow()

        saved = await self._mastery.upsert(mastery_record)

        # should_advance: student has filled the L3 band (lesson complete)
        should_advance = new_mastery >= settings.l3_mastery_ceiling

        state = _to_mastery_state(saved, settings.l3_mastery_ceiling)

        logger.info(
            "mastery_updated",
            user=str(user_id),
            unit=unit_id,
            lesson=lesson_index,
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
                new_mastery, score, settings.l3_mastery_ceiling, level3_just_unlocked
            ),
        )

    async def preview_step_progress(
        self,
        attempt_id: uuid.UUID,
        step_log: list[dict],
        *,
        was_revealed: bool = False,
    ) -> tuple[MasteryState, float, int]:
        """
        Persist in-progress step_log and return a live mastery snapshot.

        This does NOT increment attempts_count and does NOT write preview values
        into SkillMastery. Final mastery is committed on complete_attempt().

        When ``was_revealed`` is True (student used teacher-approved answer reveal),
        we still persist ``step_log`` for resume/analytics but return the committed
        mastery snapshot without blending this step into error/category previews
        (anti-inflation).
        """
        attempt = await self._attempts.get(attempt_id)
        if attempt is None:
            raise ValueError("Attempt not found.")
        if attempt.is_complete:
            # Completed attempts should no longer receive incremental updates.
            raise ValueError("Attempt is already complete.")

        await self._attempts.update_step_log(attempt_id, step_log)

        mastery_record = await self._mastery.get_for_lesson(
            attempt.user_id, attempt.unit_id, attempt.lesson_index
        )
        if mastery_record is None:
            mastery_record = _default_skill_mastery(
                attempt.user_id, attempt.unit_id, attempt.lesson_index
            )

        attempt_score, attempted_steps = _compute_attempt_score_from_step_log(step_log)

        if was_revealed:
            state = _to_mastery_state(mastery_record, settings.l3_mastery_ceiling)
            return state, attempt_score, attempted_steps

        # Mastery preview uses only committed (completed) attempts.
        # Blending the in-progress score inflates mastery on partial step data.
        l1_scores, l2_scores, l3_scores = await self._fetch_band_scores(
            attempt.user_id, attempt.unit_id, attempt.lesson_index
        )
        preview_mastery = _compute_mastery_banded(l1_scores, l2_scores, l3_scores)

        preview_error_counts = _aggregate_errors(step_log, mastery_record.error_counts)
        preview_category_scores = _compute_category_scores(step_log, mastery_record.category_scores)
        preview_consecutive = _update_consecutive(
            mastery_record.consecutive_correct, attempt_score
        )
        preview_difficulty = _difficulty_from_mastery(preview_mastery)

        transient = SkillMastery(
            user_id=mastery_record.user_id,
            unit_id=mastery_record.unit_id,
            lesson_index=mastery_record.lesson_index,
            mastery_score=preview_mastery,
            attempts_count=mastery_record.attempts_count,
            consecutive_correct=preview_consecutive,
            current_difficulty=preview_difficulty,
            level3_unlocked=mastery_record.level3_unlocked,
            level3_unlocked_at=mastery_record.level3_unlocked_at,
            category_scores=preview_category_scores,
            error_counts=preview_error_counts,
            recent_scores=list(l1_scores + l2_scores + l3_scores),
            updated_at=datetime.utcnow(),
        )
        state = _to_mastery_state(transient, settings.l3_mastery_ceiling)
        return state, attempt_score, attempted_steps

    # ── Read Mastery ──────────────────────────────────────────

    async def get_mastery(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
    ) -> MasteryState | None:
        record = await self._mastery.get_for_lesson(user_id, unit_id, lesson_index)
        if record is None:
            return None
        return _to_mastery_state(record, settings.l3_mastery_ceiling)

    async def get_mastery_or_default(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
    ) -> MasteryState:
        state = await self.get_mastery(user_id, unit_id, lesson_index)
        if state is not None:
            return state
        return MasteryState(
            user_id=user_id,
            unit_id=unit_id,
            lesson_index=lesson_index,
            mastery_score=0.0,
            attempts_count=0,
            consecutive_correct=0,
            current_difficulty="medium",
            error_counts={},
            recent_scores=[],
            category_scores=CategoryScores(),
            updated_at=datetime.utcnow(),
            has_mastered=False,
            level3_unlocked=False,
            level3_unlocked_at=None,
            should_advance=False,
            recommended_difficulty="medium",
        )

    async def unlock_level3(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
    ) -> None:
        """Permanently latch Level 3 unlocked for a student/lesson. One-way — cannot be reversed."""
        now = datetime.utcnow()
        existing = await self._mastery.get_for_lesson(user_id, unit_id, lesson_index)
        if existing is None:
            await self._mastery.upsert(
                _default_skill_mastery(
                    user_id, unit_id, lesson_index,
                    level3_unlocked=True,
                    level3_unlocked_at=now,
                )
            )
        elif not existing.level3_unlocked:
            existing.level3_unlocked = True
            existing.level3_unlocked_at = now
            await self._mastery.upsert(existing)

    async def _fetch_band_scores(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
    ) -> tuple[list[float], list[float], list[float]]:
        """Fetch recent qualifying scores for L1, L2, and L3 bands in parallel."""
        l1, l2, l3 = await asyncio.gather(
            self._attempts.get_recent_scores_for_level(
                user_id, unit_id, lesson_index,
                level=1,
                window=settings.l1_attempts_to_fill,
                passing_score=settings.mastery_passing_score,
            ),
            self._attempts.get_recent_scores_for_level(
                user_id, unit_id, lesson_index,
                level=2,
                window=settings.l2_attempts_to_fill,
                passing_score=settings.mastery_passing_score,
            ),
            self._attempts.get_recent_scores_for_level(
                user_id, unit_id, lesson_index,
                level=3,
                window=settings.l3_attempts_to_fill,
                passing_score=settings.mastery_passing_score,
            ),
        )
        return l1, l2, l3

    async def get_in_progress_attempt(
        self,
        user_id: uuid.UUID,
        unit_id: str,
        lesson_index: int,
        level: int,
    ):
        """Return the latest incomplete attempt for a lesson/level slot, or None."""
        return await self._attempts.get_in_progress(user_id, unit_id, lesson_index, level)

    async def is_at_risk(self, user_id: uuid.UUID, unit_id: str) -> bool:
        """Returns True if the student is struggling across the unit."""
        records = list(await self._mastery.get_all_for_user(user_id))
        return _is_at_risk_from_records(records, unit_id)

    async def get_student_mastery_snapshot(
        self,
        user_id: uuid.UUID,
        unit_id: str | None,
        *,
        lesson_index: int | None = None,
    ) -> MasterySnapshot:
        """
        Aggregate mastery for one student across lessons.
        When unit_id is set, only lessons in that unit are included (class context).
        When lesson_index is also set, narrows to that single lesson.
        """
        records = list(await self._mastery.get_all_for_user(user_id))
        return _snapshot_from_records(records, unit_id, lesson_index=lesson_index)

    async def get_class_summary_stats(
        self,
        classroom_id: uuid.UUID,
        student_ids: list[uuid.UUID],
        unit_id: str | None,
    ) -> ClassSummaryStats:
        """Class-level aggregates: averages, at-risk count, category breakdown."""
        if not student_ids:
            return ClassSummaryStats(
                classroom_id=classroom_id,
                avg_mastery=0.0,
                total_students=0,
                at_risk_count=0,
                category_breakdown=CategorySnapshot(),
            )

        # Fetch all student records in parallel — one query per student, not two
        all_records = await asyncio.gather(
            *(self._mastery.get_all_for_user(sid) for sid in student_ids)
        )
        snapshots: list[MasterySnapshot] = []
        at_risk = 0
        for sid, records in zip(student_ids, all_records):
            records = list(records)
            snapshots.append(_snapshot_from_records(records, unit_id))
            if unit_id and _is_at_risk_from_records(records, unit_id):
                at_risk += 1

        avg_m = sum(s.overall_mastery for s in snapshots) / len(snapshots)
        cb = CategorySnapshot()
        if snapshots:
            c_vals = [s.category_scores.conceptual for s in snapshots if s.category_scores.conceptual is not None]
            p_vals = [s.category_scores.procedural for s in snapshots if s.category_scores.procedural is not None]
            comp_vals = [s.category_scores.computational for s in snapshots if s.category_scores.computational is not None]
            if c_vals:
                cb.conceptual = round(sum(c_vals) / len(c_vals), 4)
            if p_vals:
                cb.procedural = round(sum(p_vals) / len(p_vals), 4)
            if comp_vals:
                cb.computational = round(sum(comp_vals) / len(comp_vals), 4)

        return ClassSummaryStats(
            classroom_id=classroom_id,
            avg_mastery=round(avg_m, 4),
            total_students=len(student_ids),
            at_risk_count=at_risk,
            category_breakdown=cb,
        )


# ── Pure functions (easy to unit-test) ───────────────────────

def _default_skill_mastery(
    user_id: uuid.UUID,
    unit_id: str,
    lesson_index: int,
    *,
    level3_unlocked: bool = False,
    level3_unlocked_at: datetime | None = None,
) -> SkillMastery:
    """Create a zeroed-out SkillMastery for a new student/lesson slot."""
    return SkillMastery(
        id=uuid.uuid4(),
        user_id=user_id,
        unit_id=unit_id,
        lesson_index=lesson_index,
        mastery_score=0.0,
        attempts_count=0,
        consecutive_correct=0,
        current_difficulty="medium",
        level3_unlocked=level3_unlocked,
        level3_unlocked_at=level3_unlocked_at,
        category_scores={},
        error_counts={},
        recent_scores=[],
        updated_at=datetime.utcnow(),
    )


def _snapshot_from_records(records: list, unit_id: str | None, *, lesson_index: int | None = None) -> MasterySnapshot:
    """Compute a MasterySnapshot from already-fetched SkillMastery records."""
    if unit_id:
        records = [r for r in records if r.unit_id == unit_id]
    if lesson_index is not None:
        records = [r for r in records if r.lesson_index == lesson_index]
    if not records:
        return MasterySnapshot()

    lesson_scores: list[float] = []
    cat_acc: dict[str, float] = {k: 0.0 for k in MASTERY_CATEGORY_KEYS}
    cat_counts: dict[str, int] = {k: 0 for k in MASTERY_CATEGORY_KEYS}
    for r in records:
        eff = _effective_mastery_score(r.mastery_score)
        lesson_scores.append(eff)
        cs = r.category_scores or {}
        for k in MASTERY_CATEGORY_KEYS:
            v = cs.get(k)
            if v is not None:
                cat_acc[k] += float(v)
                cat_counts[k] += 1

    overall = sum(lesson_scores) / len(lesson_scores)
    # Average per-category across only the lessons that have data for that
    # category.  Lessons where the category was never exercised are omitted
    # so they don't pull the average toward zero.
    cat_result: dict[str, float | None] = {
        k: (round(cat_acc[k] / cat_counts[k], 4) if cat_counts[k] > 0 else None)
        for k in MASTERY_CATEGORY_KEYS
    }

    return MasterySnapshot(
        overall_mastery=round(overall, 4),
        category_scores=CategorySnapshot(
            conceptual=cat_result["conceptual"],
            procedural=cat_result["procedural"],
            computational=cat_result["computational"],
        ),
        lessons_with_data=len(records),
    )


def _is_at_risk_from_records(records: list, unit_id: str) -> bool:
    """Determine at-risk status from already-fetched SkillMastery records."""
    chapter_records = [r for r in records if r.unit_id == unit_id]
    if not chapter_records:
        return False
    eligible = [r for r in chapter_records if r.attempts_count >= _AT_RISK_MIN_ATTEMPTS]
    if not eligible:
        return False
    avg = sum(r.mastery_score for r in eligible) / len(eligible)
    return avg < _AT_RISK_THRESHOLD


def _compute_mastery_banded(
    l1_scores: list[float],
    l2_scores: list[float],
    l3_scores: list[float],
) -> float:
    """Band-filling mastery score across three practice bands.

    L1 band (0 → l1_ceiling):              filled by Level 1 attempts (2 to fill).
    L2 band (l1_ceiling → l2_ceiling):     filled by Level 2 attempts (3 to fill).
    L3 band (l2_ceiling → l3_ceiling):     filled by Level 3 attempts (3 to fill).
    Exit ticket fills the remaining band to 1.0 (handled in mastery_bridge.py).

    Each qualifying attempt contributes proportionally within its band, preventing
    a single attempt from instantly maxing out any band.
    """
    s = settings
    if not l1_scores and not l2_scores and not l3_scores:
        return 0.0

    l1_band_width = s.l1_mastery_ceiling
    l2_band_width = s.l2_mastery_ceiling - s.l1_mastery_ceiling
    l3_band_width = s.l3_mastery_ceiling - s.l2_mastery_ceiling

    l1_fill = min(sum(l1_scores) / s.l1_attempts_to_fill, 1.0) if l1_scores else 0.0
    l2_fill = min(sum(l2_scores) / s.l2_attempts_to_fill, 1.0) if l2_scores else 0.0
    l3_fill = min(sum(l3_scores) / s.l3_attempts_to_fill, 1.0) if l3_scores else 0.0

    return round(
        l1_fill * l1_band_width + l2_fill * l2_band_width + l3_fill * l3_band_width,
        4,
    )


def _difficulty_from_mastery(mastery: float) -> str:
    """Map mastery score to the appropriate difficulty for the next problem.

    Thresholds relative to the L2 band:
      < 30% of L2 ceiling  → easy   (student is still struggling)
      30–80% of L2 ceiling → medium (making progress)
      ≥ 80% of L2 ceiling  → hard   (approaching L2 mastery, ready for challenge)
    """
    s = settings
    if mastery < s.l2_mastery_ceiling * 0.3:
        return "easy"
    if mastery < s.l2_mastery_ceiling * 0.8:
        return "medium"
    return "hard"


def _compute_attempt_score_from_step_log(step_log: list[dict]) -> tuple[float, int]:
    """Compute current in-progress attempt score from attempted steps only."""
    attempted = [
        bool(step.get("isCorrect"))
        for step in step_log
        if isinstance(step.get("isCorrect"), bool)
    ]
    if not attempted:
        return 0.0, 0
    correct = sum(1 for ok in attempted if ok)
    return correct / len(attempted), len(attempted)


def _update_consecutive(current: int, score: float) -> int:
    """Increment consecutive correct if score >= 0.8, else reset."""
    return current + 1 if score >= 0.8 else 0


def _aggregate_errors(step_log: list[dict], existing: dict) -> dict:
    """Merge new step errors into the existing error_counts JSONB."""
    counts = dict(existing or {})
    for step in step_log:
        if not step.get("isCorrect") and (cat := step.get("errorCategory")):
            counts[cat] = counts.get(cat, 0) + 1
    return counts


def _compute_category_scores(
    step_log: list[dict],
    existing: dict | None,
) -> dict:
    """
    Update per-category mastery scores from this attempt's step log.

    Each step carries a "category" field set by the LLM (and guaranteed by the
    server guardrail in enforce_step_types). We do a simple rolling update:
    80% existing + 20% new score per step.

    Returns a dict compatible with the CategoryScores schema.
    """

    # Start from existing scores only — never zero-init unseen categories.
    # Zero-initialising unseen categories drags them to "at-risk" even when the
    # student has never encountered that category type.
    existing = existing or {}
    scores: dict[str, float] = {k: float(existing[k]) for k in MASTERY_CATEGORY_KEYS if k in existing}

    for step in step_log:
        # Primary: "category" field set by LLM + server guardrail
        # Fallback: legacy "error_category" from older cached problems
        cat = step.get("category") or step.get("error_category")
        if cat not in VALID_MASTERY_CATEGORIES:
            label_key = (step.get("step_label") or step.get("label") or "").strip()
            inferred = LABEL_TO_MASTERY_CATEGORY.get(label_key)
            if inferred in VALID_MASTERY_CATEGORIES:
                cat = inferred
            else:
                logger.warning("unknown_step_category", category=cat, step_label=label_key or None)
                cat = "procedural"
        is_correct = step.get("is_correct", step.get("isCorrect", False))
        step_score = 1.0 if is_correct else 0.0
        if cat in scores:
            # Exponential moving average: 80% history + 20% new
            scores[cat] = round(0.8 * scores[cat] + 0.2 * step_score, 4)
        else:
            # First time seeing this category — set directly so a correct first
            # attempt isn't penalised by an artificial 0.0 baseline.
            scores[cat] = round(step_score, 4)

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


def _effective_mastery_score(mastery_score: float) -> float:
    """Return the band-based mastery score directly.

    The previous category-average fallback (used when mastery_score == 0) caused a
    bug where a first perfect attempt set all category scores to 1.0, making the
    fallback return 1.0 (100%) instead of the correct band-filled value (~10%).
    """
    return mastery_score


def _to_mastery_state(record: SkillMastery, threshold: float) -> MasteryState:
    cat = record.category_scores or {}
    effective = _effective_mastery_score(record.mastery_score)
    return MasteryState(
        user_id=record.user_id,
        unit_id=record.unit_id,
        lesson_index=record.lesson_index,
        mastery_score=effective,
        attempts_count=record.attempts_count,
        consecutive_correct=record.consecutive_correct,
        current_difficulty=record.current_difficulty,
        error_counts=record.error_counts or {},
        recent_scores=record.recent_scores or [],
        category_scores=CategoryScores(
            conceptual=cat.get("conceptual"),
            procedural=cat.get("procedural"),
            computational=cat.get("computational"),
        ),
        updated_at=record.updated_at,
        has_mastered=effective >= threshold,
        level3_unlocked=record.level3_unlocked,
        level3_unlocked_at=record.level3_unlocked_at,
        should_advance=effective >= threshold,
        recommended_difficulty=record.current_difficulty,
    )
