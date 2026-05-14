from app.domain.models import ParsedDocument


class NavigationIndexBuilder:
    def build(self, parsed: ParsedDocument) -> list[dict]:
        tree: list[dict] = []
        for page in parsed.pages:
            title = page.metadata.get("section_title") or f"Page {page.number}"
            tree.append(
                {
                    "section_id": f"page-{page.number}",
                    "title": title,
                    "page_start": page.number,
                    "page_end": page.number,
                    "summary": page.text[:240],
                }
            )
        return tree

