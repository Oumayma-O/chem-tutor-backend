from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.problem_delivery.service import ProblemDeliveryService


def _problem_payload(problem_id: str) -> dict:
    return {
        "id": problem_id,
        "title": "Stoichiometry",
        "statement": "Solve it",
        "lesson": "Chem",
        "difficulty": "medium",
        "level": 2,
        "steps": [
            {
                "id": f"{problem_id}-s1",
                "stepNumber": 1,
                "type": "interactive",
                "is_given": True,
                "category": "conceptual",
                "explanation": "Identify the setup.",
                "label": "Calculate",
                "instruction": "Do math",
                "correctAnswer": "42",
            },
            {
                "id": f"{problem_id}-s2",
                "stepNumber": 2,
                "type": "interactive",
                "is_given": True,
                "category": "procedural",
                "explanation": "Substitute values.",
                "label": "Substitute",
                "instruction": "Plug values in",
                "correctAnswer": "6 x 7",
            },
            {
                "id": f"{problem_id}-s3",
                "stepNumber": 3,
                "type": "interactive",
                "is_given": False,
                "category": "computational",
                "explanation": "Finish the arithmetic.",
                "label": "Answer",
                "instruction": "Compute final answer",
                "correctAnswer": "42",
            },
        ],
    }


@pytest.mark.asyncio
async def test_get_playlist_includes_active_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    playlist = SimpleNamespace(
        problems=[_problem_payload("p-1"), _problem_payload("p-2")],
        current_index=1,
    )
    active_attempt = SimpleNamespace(
        id="attempt-123",
        problem_id="p-2",
        level=2,
        is_complete=True,
        step_log=[{"step_id": "p-2-s3", "answer": "41", "is_correct": False}],
    )

    async def fake_get_most_recent_for_level(self, **kwargs):  # type: ignore[no-untyped-def]
        return playlist

    async def fake_get_latest_for_problem(
        self, user_id, unit_id, lesson_index, level, problem_id
    ):  # type: ignore[no-untyped-def]
        assert problem_id == "p-2"
        return active_attempt

    monkeypatch.setattr(
        "app.services.problem_delivery.service.UserLessonPlaylistRepository.get_most_recent_for_level",
        fake_get_most_recent_for_level,
    )
    monkeypatch.setattr(
        "app.services.problem_delivery.service.AttemptRepository.get_latest_for_problem",
        fake_get_latest_for_problem,
    )

    service = ProblemDeliveryService(db=object(), gen_service=object())  # type: ignore[arg-type]
    result = await service.get_playlist(
        user_id="user-1",  # type: ignore[arg-type]
        unit_id="unit-1",
        lesson_index=0,
        level=2,
        difficulty="medium",
    )

    assert result.total == 2
    assert result.current_index == 1
    assert [problem.id for problem in result.problems] == ["p-1", "p-2"]
    assert result.active_attempt == {
        "attempt_id": "attempt-123",
        "problem_id": "p-2",
        "level": 2,
        "is_complete": True,
        "step_log": [{"step_id": "p-2-s3", "answer": "41", "is_correct": False}],
    }
