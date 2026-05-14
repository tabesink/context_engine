from app.domain.models import Evidence


class AnswerComposer:
    min_evidence_score = 0.2

    def compose(
        self,
        *,
        query: str,
        evidence: list[Evidence],
        allow_general_fallback: bool,
    ) -> str:
        if not evidence and not allow_general_fallback:
            return "I do not have enough indexed evidence to answer that question."
        if not evidence:
            return "No indexed evidence was found. General fallback is allowed, but no LLM provider is configured."
        if self._is_weak_evidence(evidence) and not allow_general_fallback:
            return "I do not have enough strong indexed evidence to answer that question."

        lines = [f"Answer based on {len(evidence)} evidence item(s):"]
        for index, item in enumerate(evidence[:3], start=1):
            citation = f"[{item.id}]"
            snippet = " ".join(item.text.split())[:300]
            lines.append(f"{index}. {snippet} {citation}")
        return "\n".join(lines)

    def _is_weak_evidence(self, evidence: list[Evidence]) -> bool:
        scores = [item.score for item in evidence]
        return all(score is not None and score < self.min_evidence_score for score in scores)

