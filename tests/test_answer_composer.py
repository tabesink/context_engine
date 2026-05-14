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
        allow_general_fallback=False,
    )

    assert answer == "I do not have enough indexed evidence to answer that question."


def test_answer_composer_refuses_weak_scored_evidence_without_fallback() -> None:
    answer = AnswerComposer().compose(
        query="what changed?",
        evidence=[evidence_with_score(0.1)],
        allow_general_fallback=False,
    )

    assert answer == "I do not have enough strong indexed evidence to answer that question."


def test_answer_composer_uses_weak_evidence_when_fallback_allowed() -> None:
    answer = AnswerComposer().compose(
        query="what changed?",
        evidence=[evidence_with_score(0.1)],
        allow_general_fallback=True,
    )

    assert "evidence item" in answer


def test_answer_composer_does_not_treat_unscored_evidence_as_weak() -> None:
    answer = AnswerComposer().compose(
        query="what changed?",
        evidence=[evidence_with_score(None)],
        allow_general_fallback=False,
    )

    assert "evidence item" in answer
