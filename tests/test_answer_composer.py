from uuid import uuid4

from app.domain.models import Evidence
from app.retrieval.answer_composer import AnswerComposer


def evidence_with_score(score: float | None) -> Evidence:
    return Evidence(
        id="evidence-1",
        document_id=uuid4(),
        source_engine="semantic",
        text="Indexed evidence text.",
        score=score,
    )


def test_answer_composer_refuses_empty_evidence_without_fallback() -> None:
    answer = AnswerComposer().compose(
        query="what changed?",
        evidence=[],
    )

    assert answer == "I do not have enough indexed evidence to answer that question."


def test_answer_composer_refuses_weak_scored_evidence_without_fallback() -> None:
    answer = AnswerComposer().compose(
        query="what changed?",
        evidence=[evidence_with_score(0.1)],
    )

    assert answer == "I do not have enough strong indexed evidence to answer that question."


def test_answer_composer_refuses_weak_evidence_when_no_strong_signals() -> None:
    answer = AnswerComposer().compose(
        query="what changed?",
        evidence=[evidence_with_score(0.1)],
    )

    assert answer == "I do not have enough strong indexed evidence to answer that question."


def test_answer_composer_does_not_treat_unscored_evidence_as_weak() -> None:
    answer = AnswerComposer().compose(
        query="what changed?",
        evidence=[evidence_with_score(None)],
    )

    assert "evidence item" in answer
