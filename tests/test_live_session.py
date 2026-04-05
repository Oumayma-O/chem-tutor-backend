"""Live session JSONB normalization (lesson_index from JSON may be float)."""

import uuid

from app.services.classroom.live_session import _to_out


def test_to_out_coerces_float_lesson_index_from_jsonb() -> None:
    cid = uuid.uuid4()
    out = _to_out(
        cid,
        {
            "session_phase": "exit_ticket",
            "active_exit_ticket_id": str(uuid.uuid4()),
            "lesson_index": 2.0,
            "unit_id": "ap-unit-1",
            "timed_mode_active": False,
        },
    )
    assert out.lesson_index == 2


def test_to_out_coerces_float_timed_practice_minutes() -> None:
    cid = uuid.uuid4()
    out = _to_out(
        cid,
        {
            "session_phase": "timed_practice",
            "timed_practice_minutes": 10.0,
            "lesson_index": 0,
        },
    )
    assert out.timed_practice_minutes == 10
