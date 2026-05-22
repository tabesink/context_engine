from dataclasses import dataclass

from app.document_processing.models import DocumentSection, DocumentStructure, StructureQuality


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
            should_run_toc_refiner=bool(reasons),
            reasons=reasons,
        )


@dataclass(frozen=True)
class TocRefinementResult:
    structure: DocumentStructure
    accepted: bool
    reason: str
    validation_accuracy: float
    warnings: list[str]


class TocRefiner:
    def refine(
        self,
        structure: DocumentStructure,
        *,
        candidate_sections: list[dict],
    ) -> TocRefinementResult:
        sections: list[DocumentSection] = []
        for index, item in enumerate(candidate_sections, start=1):
            title = str(item.get("title") or "").strip()
            page_start = item.get("page_start")
            page_end = item.get("page_end")
            if not title or not isinstance(page_start, int) or not isinstance(page_end, int):
                return self._rejected(structure, "invalid section fields")
            if page_start < 1 or page_end < page_start:
                return self._rejected(structure, "invalid page range")
            sections.append(
                DocumentSection(
                    section_id=f"toc-sec-{index}",
                    document_id=structure.document_id,
                    title=title,
                    level=int(item.get("level") or 1),
                    page_start=page_start,
                    page_end=page_end,
                    source="toc_refiner",
                    confidence=0.8,
                )
            )

        if not sections:
            return self._rejected(structure, "no sections returned")

        refined = structure.model_copy(update={"sections": sections})
        return TocRefinementResult(
            structure=refined,
            accepted=True,
            reason="accepted",
            validation_accuracy=1.0,
            warnings=[],
        )

    def _rejected(self, structure: DocumentStructure, reason: str) -> TocRefinementResult:
        return TocRefinementResult(
            structure=structure,
            accepted=False,
            reason=reason,
            validation_accuracy=0.0,
            warnings=[reason],
        )
