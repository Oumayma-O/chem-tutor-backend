"""Pure helpers for exit ticket misconception analytics (MCQ option tags)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any


def build_question_option_tag_and_correct_maps(
    questions_json: list | None,
) -> tuple[dict[str, dict[str, str | None]], dict[str, str | None], dict[str, str]]:
    """
    From stored ticket ``questions`` JSON, build:
    - ``qid -> (option text -> misconception tag or None)``
    - ``qid -> correct_answer``
    - ``qid -> prompt`` (for per-question display)

    Handles both formats:
    - New: options = [{text, is_correct, misconception_tag}, ...]
    - Legacy: options = ["A", "B"], option_misconception_tags = [null, "sign_error"]
    """
    q_tag_map: dict[str, dict[str, str | None]] = {}
    correct_map: dict[str, str | None] = {}
    prompt_map: dict[str, str] = {}
    for q_dict in questions_json or []:
        if not isinstance(q_dict, dict):
            continue
        qid = str(q_dict.get("id") or "")
        correct_map[qid] = q_dict.get("correct_answer")
        prompt_map[qid] = str(q_dict.get("prompt") or "")

        opts = q_dict.get("options") or []
        if opts and isinstance(opts[0], dict):
            # New format: structured option objects
            q_tag_map[qid] = {
                str(opt.get("text") or ""): opt.get("misconception_tag")
                for opt in opts
                if isinstance(opt, dict)
            }
        else:
            # Legacy format: parallel arrays
            tags = q_dict.get("option_misconception_tags") or []
            q_tag_map[qid] = {
                str(opt): (str(tags[j]) if j < len(tags) and tags[j] else None)
                for j, opt in enumerate(opts)
            }
    return q_tag_map, correct_map, prompt_map


def aggregate_misconception_tag_counts(
    tickets: Iterable[Any],
) -> tuple[dict[str, int], int]:
    """
    Across many tickets, count how often each misconception tag was chosen on *wrong* MCQ answers.

    Each ticket-like object must have ``questions`` (JSON list) and ``responses`` (ORM rows with ``answers`` JSON).
    """
    tag_counts: dict[str, int] = defaultdict(int)
    total_wrong = 0

    for ticket in tickets:
        q_tag_map, correct_map, _ = build_question_option_tag_and_correct_maps(list(ticket.questions or []))

        for response in ticket.responses or []:
            for ans in response.answers or []:
                if not isinstance(ans, dict):
                    continue
                qid = str(ans.get("question_id") or ans.get("id") or "")
                chosen = str(ans.get("answer") or ans.get("value") or "")
                correct = correct_map.get(qid)
                if correct is not None and chosen == str(correct):
                    continue
                tag = q_tag_map.get(qid, {}).get(chosen)
                if tag:
                    tag_counts[tag] += 1
                    total_wrong += 1

    return dict(tag_counts), total_wrong


def per_question_misconception_hits(
    questions_json: list | None,
    responses: Iterable[Any],
) -> tuple[dict[str, dict[str, int]], dict[str, str]]:
    """
    For one ticket, aggregate counts per (question_id, misconception_tag) when a tagged option was chosen.

    Returns ``(hits_per_question, question_id -> prompt)``.
    """
    q_tag_map, _, prompt_map = build_question_option_tag_and_correct_maps(questions_json)
    agg: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for response in responses:
        for ans in response.answers or []:
            if not isinstance(ans, dict):
                continue
            qid = str(ans.get("question_id") or ans.get("id") or "")
            chosen = str(ans.get("answer") or ans.get("value") or "")
            tag = q_tag_map.get(qid, {}).get(chosen)
            if tag:
                agg[qid][tag] += 1

    return {qid: dict(tags) for qid, tags in agg.items()}, prompt_map
