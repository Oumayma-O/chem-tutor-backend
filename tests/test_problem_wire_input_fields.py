"""Problem API wire format: steps expose ``input_fields`` only (no ``inputFields``)."""

from __future__ import annotations

from app.domain.schemas.tutor.problems import ProblemOutput


def _minimal_steps(multi_use: str = "inputFields") -> list[dict]:
    """Three steps: two placeholders plus one multi_input with legacy or canonical key."""
    fields = [{"label": "A", "value": "1", "unit": "mol"}]
    multi: dict = {
        "stepNumber": 3,
        "type": "multi_input",
        "label": "L3",
        "instruction": "go",
        "correctAnswer": None,
    }
    if multi_use == "inputFields":
        multi["inputFields"] = fields
    elif multi_use == "labeledValues":
        multi["labeledValues"] = fields
    else:
        multi["input_fields"] = fields
    return [
        {"stepNumber": 1, "type": "interactive", "label": "a", "instruction": "i", "correctAnswer": "1"},
        {"stepNumber": 2, "type": "interactive", "label": "b", "instruction": "i", "correctAnswer": "2"},
        multi,
    ]


def _problem_payload(multi_use: str = "inputFields") -> dict:
    return {
        "id": "p1",
        "title": "t",
        "statement": "s",
        "lesson": "Chem",
        "difficulty": "easy",
        "level": 2,
        "steps": _minimal_steps(multi_use),
    }


def test_problem_output_accepts_input_fields_only_in_dump() -> None:
    p = ProblemOutput.model_validate(_problem_payload("input_fields"))
    blob = p.model_dump(mode="json", by_alias=False)
    step3 = blob["steps"][2]
    assert "input_fields" in step3
    assert step3["input_fields"] == [{"label": "A", "value": "1", "unit": "mol"}]
    assert "inputFields" not in step3
    assert "labeledValues" not in step3


def test_problem_output_coerces_input_fields_from_input_fields_camel() -> None:
    p = ProblemOutput.model_validate(_problem_payload("inputFields"))
    step3 = p.model_dump(mode="json", by_alias=False)["steps"][2]
    assert step3["input_fields"][0]["value"] == "1"
    assert "inputFields" not in step3


def test_problem_output_coerces_input_fields_from_labeled_values() -> None:
    p = ProblemOutput.model_validate(_problem_payload("labeledValues"))
    step3 = p.model_dump(mode="json", by_alias=False)["steps"][2]
    assert step3["input_fields"][0]["label"] == "A"
    assert "labeledValues" not in step3
