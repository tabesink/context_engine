from app.domain.models import Evidence


class AnswerComposer:
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

        lines = [f"Answer based on {len(evidence)} evidence item(s):"]
        for index, item in enumerate(evidence[:3], start=1):
            citation = f"[{item.id}]"
            snippet = " ".join(item.text.split())[:300]
            lines.append(f"{index}. {snippet} {citation}")
        return "\n".join(lines)

