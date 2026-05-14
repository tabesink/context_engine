from uuid import UUID

from app.domain.models import Evidence, PageRef, SectionRef


class PageIndexAdapter:
    """Adapter for PageIndex-style page and section navigation."""

    def retrieve_sections(
        self,
        *,
        query: str,
        document_id: str,
        pages: list[dict],
        tree: list[dict],
        top_k: int,
    ) -> list[Evidence]:
        query_terms = {term.lower() for term in query.split() if len(term) > 2}
        results: list[Evidence] = []
        for page in pages:
            text = page.get("text", "")
            title = page.get("metadata", {}).get("section_title") or f"Page {page.get('number')}"
            score = self._score(query_terms, f"{title} {text}")
            if score <= 0 and query_terms:
                continue
            section = self._section_for_page(tree, page.get("number"))
            results.append(
                Evidence(
                    id=f"navigation:{document_id}:{page.get('number')}",
                    document_id=UUID(document_id),
                    source_engine="navigation",
                    text=text,
                    score=score,
                    page_ref=PageRef(
                        document_id=UUID(document_id),
                        page_start=page.get("number"),
                        page_end=page.get("number"),
                    ),
                    section_ref=SectionRef(
                        document_id=UUID(document_id),
                        section_id=section.get("section_id", f"page-{page.get('number')}"),
                        title=section.get("title", title),
                        page_start=section.get("page_start", page.get("number")),
                        page_end=section.get("page_end", page.get("number")),
                    ),
                    metadata={"section": section},
                )
            )
        return sorted(results, key=lambda item: item.score or 0.0, reverse=True)[:top_k]

    def _score(self, query_terms: set[str], text: str) -> float:
        if not query_terms:
            return 0.5
        text_lower = text.lower()
        matches = sum(1 for term in query_terms if term in text_lower)
        return matches / len(query_terms)

    def _section_for_page(self, tree: list[dict], page_number: int | None) -> dict:
        for node in tree:
            if node.get("page_start") == page_number:
                return node
        return {}

