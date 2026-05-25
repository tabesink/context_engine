from app.document_processing.models import DocumentStructure, StructureQuality


class StructureQualityScorer:
    def score(self, structure: DocumentStructure) -> StructureQuality:
        page_text = "\n".join(page.text or "" for page in structure.pages).lower()
        has_toc = "table of contents" in page_text or "\ncontents" in page_text
        reasons: list[str] = []
        if not structure.sections:
            reasons.append("no sections detected")
        if has_toc and not structure.sections:
            reasons.append("toc present without section ranges")

        score = 1.0
        if not structure.sections:
            score -= 0.5
        if has_toc and not structure.sections:
            score -= 0.25

        return StructureQuality(
            heading_count=sum(1 for block in structure.blocks if block.type == "heading"),
            section_count=len(structure.sections),
            block_count=len(structure.blocks),
            asset_count=len(structure.assets),
            has_toc=has_toc,
            has_page_ranges=any(section.page_start is not None for section in structure.sections),
            score=max(score, 0.0),
            should_run_toc_refiner=False,
            reasons=reasons,
        )
