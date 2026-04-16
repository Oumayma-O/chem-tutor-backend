"""Regression tests for AnalyticsService student standards shaping."""

import uuid
from types import SimpleNamespace

import pytest

from app.services.analytics_service import AnalyticsService


class _DummyThinkingService:
    async def generate_class_insights(self, **kwargs):  # pragma: no cover
        raise AssertionError("Not used in this test")


@pytest.mark.asyncio
async def test_class_scoped_student_standards_defaults_missing_lesson_count(monkeypatch) -> None:
    student_id = uuid.uuid4()
    class_id = uuid.uuid4()

    class _FakeRepo:
        def __init__(self, _db):
            pass

        async def get_student_standards_mastery(self, user_id):
            raise AssertionError("Global path should not be called in this test")

        async def get_student_standards_mastery_for_class(self, user_id, class_id):
            return [
                SimpleNamespace(
                    code="STD-1",
                    title="Stoichiometry",
                    framework="NGSS",
                    avg_mastery=0.62,
                )
            ]

    monkeypatch.setattr("app.services.analytics_service.StandardsMasteryRepository", _FakeRepo)

    svc = AnalyticsService(db=None, thinking_service=_DummyThinkingService())  # type: ignore[arg-type]
    out = await svc.aggregate_student_standards(student_id=student_id, class_id=class_id)

    assert out.student_id == student_id
    assert len(out.standards) == 1
    assert out.standards[0].standard_code == "STD-1"
    assert out.standards[0].lesson_count == 0
