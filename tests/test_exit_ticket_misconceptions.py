"""Unit tests for exit ticket misconception rollup helpers."""

from types import SimpleNamespace

from app.services.exit_ticket.misconceptions import (
    aggregate_misconception_tag_counts,
    build_question_option_tag_and_correct_maps,
    per_question_misconception_hits,
)


def test_build_question_maps() -> None:
    q_tag, correct, prompts = build_question_option_tag_and_correct_maps(
        [
            {
                "id": "q1",
                "prompt": "P1",
                "correct_answer": "A",
                "options": ["A", "B"],
                "option_misconception_tags": [None, "confuses_x"],
            }
        ]
    )
    assert correct["q1"] == "A"
    assert prompts["q1"] == "P1"
    assert q_tag["q1"]["B"] == "confuses_x"


def test_aggregate_counts_wrong_answers_only() -> None:
    ticket = SimpleNamespace(
        questions=[
            {
                "id": "q1",
                "correct_answer": "yes",
                "options": ["yes", "no"],
                "option_misconception_tags": [None, "bad_tag"],
            }
        ],
        responses=[
            SimpleNamespace(
                answers=[{"question_id": "q1", "answer": "no"}],
            )
        ],
    )
    counts, total_wrong = aggregate_misconception_tag_counts([ticket])
    assert total_wrong == 1
    assert counts["bad_tag"] == 1


def test_per_question_hits() -> None:
    questions = [
        {
            "id": "q1",
            "prompt": "Q?",
            "options": ["a", "b"],
            "option_misconception_tags": [None, "t1"],
        }
    ]
    responses = [SimpleNamespace(answers=[{"question_id": "q1", "answer": "b"}])]
    agg, prompts = per_question_misconception_hits(questions, responses)
    assert agg["q1"]["t1"] == 1
    assert prompts["q1"] == "Q?"
