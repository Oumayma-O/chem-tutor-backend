from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.domain.schemas.tutor import GenerateProblemRequest
from app.services.problem_delivery.playlist_coordinator import PlaylistCoordinator


@pytest.mark.asyncio
async def test_try_resume_uses_most_recent_playlist_for_level(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"most_recent": 0}

    async def fake_get_most_recent_for_level(self, **kwargs):  # type: ignore[no-untyped-def]
        calls["most_recent"] += 1
        return None

    async def fail_get(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("difficulty-scoped get() should not be used for resume")

    monkeypatch.setattr(
        "app.services.problem_delivery.playlist_coordinator.UserLessonPlaylistRepository.get_most_recent_for_level",
        fake_get_most_recent_for_level,
    )
    monkeypatch.setattr(
        "app.services.problem_delivery.playlist_coordinator.UserLessonPlaylistRepository.get",
        fail_get,
    )

    coordinator = PlaylistCoordinator(db=object())  # type: ignore[arg-type]
    req = GenerateProblemRequest(
        user_id=uuid.uuid4(),
        unit_id="u1",
        lesson_index=1,
        lesson_name="Stoichiometry",
        level=2,
    )

    result = await coordinator.try_resume(req, effective_difficulty="medium", max_problems=5)
    assert result is None
    assert calls["most_recent"] == 1


@pytest.mark.asyncio
async def test_previous_problem_summaries_use_most_recent_playlist(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"most_recent": 0}

    async def fake_get_most_recent_for_level(self, **kwargs):  # type: ignore[no-untyped-def]
        calls["most_recent"] += 1
        return SimpleNamespace(
            problems=[
                {"title": "Problem A", "statement": "First sentence. second sentence."},
                {"title": "Problem B", "statement": "Only one line"},
            ]
        )

    async def fail_get(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("difficulty-scoped get() should not be used for summaries")

    monkeypatch.setattr(
        "app.services.problem_delivery.playlist_coordinator.UserLessonPlaylistRepository.get_most_recent_for_level",
        fake_get_most_recent_for_level,
    )
    monkeypatch.setattr(
        "app.services.problem_delivery.playlist_coordinator.UserLessonPlaylistRepository.get",
        fail_get,
    )

    coordinator = PlaylistCoordinator(db=object())  # type: ignore[arg-type]
    summaries = await coordinator.get_previous_problem_summaries(
        user_id=uuid.uuid4(),
        unit_id="u1",
        lesson_index=1,
        level=2,
        difficulty="hard",
    )

    assert calls["most_recent"] == 1
    assert summaries == ["Problem A: First sentence", "Problem B: Only one line"]
