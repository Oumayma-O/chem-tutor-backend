"""Serialize ORM ExitTicket rows to API ExitTicketConfig (robust to JSON shape drift)."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.domain.schemas.dashboards import ExitTicketConfig, ExitTicketQuestion, MCQOptionOut
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
    out_opts: list[dict] = []
    tags = d.get("option_misconception_tags") or []
    for i, o in enumerate(opts_in):
        if isinstance(o, dict):
            # New format: already structured
            out_opts.append({
                "text": str(o.get("text") or o.get("label") or o.get("value") or ""),
                "is_correct": bool(o.get("is_correct", False)),
                "misconception_tag": o.get("misconception_tag"),
            })
        elif isinstance(o, str):
            # Legacy format: plain string + parallel tags array
            tag = tags[i] if i < len(tags) and tags[i] else None
            ca = d.get("correct_answer")
            out_opts.append({
                "text": o,
                "is_correct": (o == ca) if ca else False,
                "misconception_tag": str(tag) if tag else None,
            })
        else:
            out_opts.append({"text": str(o), "is_correct": False, "misconception_tag": None})
    d["options"] = out_opts
    d.pop("option_misconception_tags", None)
    ca = d.get("correct_answer")
    if ca is None:
        d["correct_answer"] = None
    else:
        d["correct_answer"] = str(ca).strip()
    try:
        d["points"] = float(d.get("points", 1.0) or 1.0)
    except (TypeError, ValueError):
        d["points"] = 1.0
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
                    options=[MCQOptionOut(**o) for o in nd.get("options", []) if isinstance(o, dict)],
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
        lesson_id=getattr(row, "lesson_id", None),
        difficulty=row.difficulty,
        time_limit_minutes=row.time_limit_minutes,
        is_active=row.is_active,
        questions=questions,
        published_at=row.published_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
