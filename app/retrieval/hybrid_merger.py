import hashlib

from app.domain.models import Evidence


class HybridMerger:
    def merge(self, evidence: list[Evidence], *, top_k: int) -> list[Evidence]:
        deduped: dict[tuple[str, int | None, int | None, str], Evidence] = {}
        for item in evidence:
            text_hash = hashlib.sha1(item.text.strip().lower().encode("utf-8")).hexdigest()
            key = (
                str(item.document_id),
                item.page_ref.page_start if item.page_ref else None,
                item.page_ref.page_end if item.page_ref else None,
                text_hash,
            )
            existing = deduped.get(key)
            if existing is None or self._rank_value(item) > self._rank_value(existing):
                deduped[key] = item
        return sorted(deduped.values(), key=self._rank_value, reverse=True)[:top_k]

    def _rank_value(self, evidence: Evidence) -> float:
        score = evidence.score if evidence.score is not None else 0.5
        if evidence.page_ref or evidence.section_ref:
            score += 0.05
        return score

