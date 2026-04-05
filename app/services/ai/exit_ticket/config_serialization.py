"""Serialize ORM ExitTicket rows to API ExitTicketConfig (robust to JSON shape drift)."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.domain.schemas.dashboards import ExitTicketConfig, ExitTicketQuestion
from app.infrastructure.database.models import ExitTicket


def _normalize_question_dict(raw: dict[str, Any]) -> dict[str, Any]:
    d = dict(raw)
    prompt = d.get("prompt")
    if not (isinstance(prompt, str) and prompt.strip()):
        alt = d.get("question")
        d["prompt"] = str(alt if alt is not None else "").strip()
    if not d.get("prompt"):
        d["prompt"] = f"Question {d.get('id', '')}".strip() or "Question"
    qid = d.get("id")
    d["id"] = str(qid).strip() if qid is not None else "q"
    d["question_type"] = str(d.get("question_type") or "short_answer")
    opts_in = d.get("options") or []
    out_opts: list[str] = []
    for o in opts_in:
        if isinstance(o, str):
            out_opts.append(o)
        elif isinstance(o, dict):
            out_opts.append(str(o.get("text") or o.get("label") or o.get("value") or ""))
        else:
            out_opts.append(str(o))
    d["options"] = out_opts
    ca = d.get("correct_answer")
    if ca is None:
        d["correct_answer"] = None
    else:
        d["correct_answer"] = str(ca).strip()
    try:
        d["points"] = float(d.get("points", 1.0) or 1.0)
    except (TypeError, ValueError):
        d["points"] = 1.0
    tags = d.get("option_misconception_tags")
    if tags is not None and isinstance(tags, list):
        d["option_misconception_tags"] = [None if t is None else str(t) for t in tags]
    else:
        d.pop("option_misconception_tags", None)
    return d


def exit_ticket_row_to_config(row: ExitTicket) -> ExitTicketConfig:
    questions: list[ExitTicketQuestion] = []
    for raw in row.questions or []:
        if not isinstance(raw, dict):
            continue
        nd = _normalize_question_dict(raw)
        try:
            questions.append(ExitTicketQuestion.model_validate(nd))
        except ValidationError:
            questions.append(
                ExitTicketQuestion(
                    id=str(nd.get("id") or "q"),
                    prompt=str(nd.get("prompt") or "(Question unavailable)"),
                    question_type=str(nd.get("question_type") or "short_answer"),
                    options=list(nd.get("options") or []),
                    option_misconception_tags=nd.get("option_misconception_tags"),
                    correct_answer=nd.get("correct_answer"),
                    points=float(nd.get("points", 1.0) or 1.0),
                )
            )
    return ExitTicketConfig(
        id=row.id,
        class_id=row.class_id,
        teacher_id=row.teacher_id,
        unit_id=row.unit_id,
        lesson_index=row.lesson_index,
        difficulty=row.difficulty,
        time_limit_minutes=row.time_limit_minutes,
        is_active=row.is_active,
        questions=questions,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
