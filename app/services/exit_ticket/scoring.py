"""Scoring for student exit ticket submissions.

Uses StepValidationService (the same hybrid pipeline as /validate-step) so that numeric
tolerance, canonical formula matching, and LLM equivalence are applied consistently.
All questions are validated in parallel via asyncio.gather.

MCQ questions store the selected option index/letter as both student and correct answer,
so they always resolve on Phase 1's normalised string match — no LLM call is made.
"""

from __future__ import annotations

import asyncio
import math
import time

from app.core.logging import get_logger
from app.services.ai.step_validation.service import StepValidationService

logger = get_logger(__name__)


async def score_exit_ticket_submission(
    questions: list,
    answers: dict[str, str],
) -> tuple[float | None, dict[str, bool]]:
    """Validate every answer and return ``(score_percent, per_question_correct)``.

    * ``score_percent`` — weighted 0–100 rounded to 4 dp; ``None`` if nothing was gradable.
    * ``per_question_correct`` — ``{question_id: is_correct}`` for every question that has a
      ``correct_answer``. Questions without a canonical answer are omitted.

    Validation is done via :class:`StepValidationService` (Phase 1 local + Phase 2 LLM),
    the same pipeline used by ``POST /problems/validate-step``.  All questions are
    validated concurrently to keep submission latency low.
    """
    service = StepValidationService()

    gradable: list[tuple[str, float, str, str, str]] = []  # (qid, pts, sa, ca, prompt)
    ungradable_pts = 0.0

    for raw in questions or []:
        if not isinstance(raw, dict):
            continue
        try:
            pts = float(raw.get("points", 1.0) or 1.0)
        except (TypeError, ValueError):
            pts = 1.0
        if not math.isfinite(pts) or pts < 0:
            pts = 1.0

        qid = str(raw.get("id", ""))
        ca = (raw.get("correct_answer") or "").strip()
        sa = (answers.get(qid) or "").strip()
        prompt = (raw.get("prompt") or raw.get("question_text") or "exit ticket question").strip()

        if not ca:
            ungradable_pts += pts
            continue

        gradable.append((qid, pts, sa, ca, prompt))

    total = sum(pts for _, pts, *_ in gradable) + ungradable_pts
    if total <= 0:
        return None, {}

    if not gradable:
        return 0.0, {}

    async def _validate_one(qid: str, pts: float, sa: str, ca: str, prompt: str) -> tuple[str, bool, float]:
        t0 = time.monotonic()
        try:
            out = await service.validate(
                student_answer=sa,
                correct_answer=ca,
                step_label=prompt,
                step_type="final_answer",
                problem_context=prompt,
            )
            elapsed = time.monotonic() - t0
            logger.debug("exit_ticket_question_scored", qid=qid, is_correct=out.is_correct, elapsed_s=round(elapsed, 3))
            return qid, out.is_correct, pts if out.is_correct else 0.0
        except Exception as exc:
            elapsed = time.monotonic() - t0
            logger.warning("exit_ticket_question_score_failed", qid=qid, error=str(exc), elapsed_s=round(elapsed, 3))
            return qid, False, 0.0

    results = await asyncio.gather(*[_validate_one(*args) for args in gradable])

    per_question: dict[str, bool] = {qid: correct for qid, correct, _ in results}
    earned = sum(pts_earned for _, _, pts_earned in results)

    raw_score = round(100.0 * earned / total, 4)
    score = raw_score if math.isfinite(raw_score) else None
    return score, per_question
