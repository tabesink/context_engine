from dataclasses import dataclass
import re

from app.document_processing.models import (
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
    StructureQuality,
)


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
    logical_to_physical_offset: int | None = None
    llm_call_count: int = 0


class TocPageDetector:
    def detect(self, structure: DocumentStructure) -> list[int]:
        pages: list[int] = []
        for page in structure.pages:
            text = (page.text or "").lower()
            if "table of contents" in text or text.strip().startswith("contents"):
                pages.append(page.page_number)
        return pages


class TocJsonExtractor:
    def __init__(self, candidate_sections: list[dict] | None = None):
        self.candidate_sections = candidate_sections or []
        self.call_count = 0

    def extract(self, *, structure: DocumentStructure, toc_pages: list[int]) -> list[dict]:
        self.call_count += 1
        if self.candidate_sections:
            return self.candidate_sections
        toc_page_numbers = set(toc_pages)
        candidates: list[dict] = []
        for page in structure.pages:
            if page.page_number not in toc_page_numbers:
                continue
            for line in (page.text or "").splitlines():
                candidate = self._candidate_from_line(line)
                if candidate is not None:
                    candidates.append(candidate)
        return candidates

    def _candidate_from_line(self, line: str) -> dict | None:
        raw_value = line.strip()
        normalized_value = " ".join(raw_value.split())
        if not normalized_value:
            return None
        if normalized_value.lower() in {"contents", "table of contents"}:
            return None
        match = re.match(
            r"^(?:(?P<number>\d+(?:\.\d+)*)\s+)?(?P<title>.+?)\s*(?:\.{2,}|\s{2,})\s*(?P<page>\d+)$",
            raw_value,
        )
        if not match:
            return None
        title = " ".join(match.group("title").strip(" .").split())
        page_start = int(match.group("page"))
        if not title:
            return None
        number = match.group("number") or ""
        return {
            "title": title,
            "level": number.count(".") + 1 if number else 1,
            "page_start": page_start,
        }


class PageOffsetResolver:
    def resolve(self, *, structure: DocumentStructure, candidate_sections: list[dict]) -> int:
        pairs = self._explicit_pairs(candidate_sections)
        if not pairs:
            pairs = self._title_matched_pairs(structure=structure, candidate_sections=candidate_sections)
        if not pairs:
            return 0
        offsets = [physical - logical for logical, physical in pairs]
        return max(set(offsets), key=lambda offset: (offsets.count(offset), -abs(offset)))

    def _explicit_pairs(self, candidate_sections: list[dict]) -> list[tuple[int, int]]:
        logical_starts = [item.get("page_start") for item in candidate_sections]
        physical_starts = [item.get("physical_page_start") for item in candidate_sections]
        return [
            (logical, physical)
            for logical, physical in zip(logical_starts, physical_starts, strict=False)
            if isinstance(logical, int) and isinstance(physical, int)
        ]

    def _title_matched_pairs(
        self,
        *,
        structure: DocumentStructure,
        candidate_sections: list[dict],
    ) -> list[tuple[int, int]]:
        page_text_by_number = {
            page.page_number: self._normalize(page.text or "")
            for page in structure.pages
            if page.text and not self._is_toc_page(page.text)
        }
        pairs: list[tuple[int, int]] = []
        for item in candidate_sections:
            logical = item.get("page_start")
            title = self._normalize(str(item.get("title") or ""))
            if not isinstance(logical, int) or not title:
                continue
            for page_number, page_text in page_text_by_number.items():
                if title in page_text:
                    pairs.append((logical, page_number))
                    break
        return pairs

    def _normalize(self, value: str) -> str:
        return " ".join(value.lower().replace("-", " ").split())

    def _is_toc_page(self, value: str) -> bool:
        normalized = self._normalize(value)
        return "table of contents" in normalized or normalized.startswith("contents ")


class SectionStartValidator:
    def validate(self, *, structure: DocumentStructure, sections: list[DocumentSection]) -> float:
        if not sections:
            return 0.0
        pages_by_number = {page.page_number: page for page in structure.pages}
        if not pages_by_number:
            return 1.0
        valid = sum(1 for section in sections if self._section_start_is_valid(section, pages_by_number))
        return valid / len(sections)

    def _section_start_is_valid(
        self,
        section: DocumentSection,
        pages_by_number: dict[int, DocumentPage],
    ) -> bool:
        if section.page_start is None:
            return False
        page = pages_by_number.get(section.page_start)
        if page is None:
            return False
        page_text = self._normalize(page.text or "")
        if not page_text:
            return True
        title = self._normalize(section.title)
        return bool(title and title in page_text)

    def _normalize(self, value: str) -> str:
        return " ".join(value.lower().replace("-", " ").split())


class SectionRangeAssigner:
    def assign(self, sections: list[DocumentSection]) -> list[DocumentSection]:
        assigned: list[DocumentSection] = []
        for index, section in enumerate(sections):
            page_end = section.page_end
            next_peer = self._next_peer_or_ancestor_section(
                sections=sections,
                index=index,
                section=section,
            )
            if page_end is None and next_peer and next_peer.page_start:
                page_end = max(next_peer.page_start - 1, section.page_start or 1)
            if page_end is None:
                page_end = self._last_descendant_page_end(sections=sections, index=index, section=section)
            assigned.append(section.model_copy(update={"page_end": page_end}))
        return assigned

    def _next_peer_or_ancestor_section(
        self,
        *,
        sections: list[DocumentSection],
        index: int,
        section: DocumentSection,
    ) -> DocumentSection | None:
        for candidate in sections[index + 1 :]:
            if candidate.level <= section.level:
                return candidate
        return None

    def _last_descendant_page_end(
        self,
        *,
        sections: list[DocumentSection],
        index: int,
        section: DocumentSection,
    ) -> int | None:
        page_end = section.page_start
        for candidate in sections[index + 1 :]:
            if candidate.level <= section.level:
                break
            page_end = candidate.page_end or candidate.page_start or page_end
        return page_end


class BlockSectionAssigner:
    def assign(
        self,
        *,
        blocks: list[DocumentBlock],
        sections: list[DocumentSection],
    ) -> list[DocumentBlock]:
        updated: list[DocumentBlock] = []
        for block in blocks:
            section = self._section_for_page(block.page_start, sections)
            updated.append(
                block.model_copy(update={"section_id": section.section_id if section else block.section_id})
            )
        return updated

    def _section_for_page(
        self,
        page_number: int | None,
        sections: list[DocumentSection],
    ) -> DocumentSection | None:
        if page_number is None:
            return None
        matches: list[DocumentSection] = []
        for section in sections:
            if section.page_start is None:
                continue
            page_end = section.page_end or section.page_start
            if section.page_start <= page_number <= page_end:
                matches.append(section)
        if not matches:
            return None
        return sorted(matches, key=lambda section: (section.level, section.page_start or 0))[-1]


class AssetSectionAssigner:
    def assign(
        self,
        *,
        assets: list[DocumentAsset],
        sections: list[DocumentSection],
        blocks: list[DocumentBlock],
    ) -> list[DocumentAsset]:
        section_by_block = {block.block_id: block.section_id for block in blocks}
        updated: list[DocumentAsset] = []
        for asset in assets:
            section_id = (
                section_by_block.get(asset.block_id)
                if asset.block_id
                else self._section_id_for_page(asset.page_number, sections)
            )
            updated.append(asset.model_copy(update={"section_id": section_id or asset.section_id}))
        return updated

    def _section_id_for_page(
        self,
        page_number: int | None,
        sections: list[DocumentSection],
    ) -> str | None:
        if page_number is None:
            return None
        for section in sections:
            if section.page_start is None:
                continue
            page_end = section.page_end or section.page_start
            if section.page_start <= page_number <= page_end:
                return section.section_id
        return None


class StructureMerger:
    def __init__(
        self,
        *,
        block_assigner: BlockSectionAssigner | None = None,
        asset_assigner: AssetSectionAssigner | None = None,
    ):
        self.block_assigner = block_assigner or BlockSectionAssigner()
        self.asset_assigner = asset_assigner or AssetSectionAssigner()

    def merge(
        self,
        *,
        structure: DocumentStructure,
        sections: list[DocumentSection],
    ) -> DocumentStructure:
        blocks = self.block_assigner.assign(blocks=structure.blocks, sections=sections)
        block_ids_by_section: dict[str, list[str]] = {section.section_id: [] for section in sections}
        for block in blocks:
            if block.section_id in block_ids_by_section:
                block_ids_by_section[block.section_id].append(block.block_id)
        merged_sections = [
            section.model_copy(update={"block_ids": block_ids_by_section.get(section.section_id, [])})
            for section in sections
        ]
        assets = self.asset_assigner.assign(assets=structure.assets, sections=merged_sections, blocks=blocks)
        return structure.model_copy(update={"sections": merged_sections, "blocks": blocks, "assets": assets})


class TocRefiner:
    def __init__(
        self,
        *,
        page_detector: TocPageDetector | None = None,
        extractor: TocJsonExtractor | None = None,
        offset_resolver: PageOffsetResolver | None = None,
        range_assigner: SectionRangeAssigner | None = None,
        start_validator: SectionStartValidator | None = None,
        merger: StructureMerger | None = None,
        minimum_validation_accuracy: float = 0.6,
        max_llm_calls: int = 8,
    ):
        self.page_detector = page_detector or TocPageDetector()
        self.extractor = extractor
        self.offset_resolver = offset_resolver or PageOffsetResolver()
        self.range_assigner = range_assigner or SectionRangeAssigner()
        self.start_validator = start_validator or SectionStartValidator()
        self.merger = merger or StructureMerger()
        self.minimum_validation_accuracy = minimum_validation_accuracy
        self.max_llm_calls = max_llm_calls

    def refine(
        self,
        structure: DocumentStructure,
        *,
        candidate_sections: list[dict] | None = None,
    ) -> TocRefinementResult:
        toc_pages = self.page_detector.detect(structure)
        extractor = self.extractor
        if candidate_sections is None:
            if extractor is None:
                return self._rejected(structure, "toc refinement extractor not configured")
            if extractor.call_count >= self.max_llm_calls:
                return self._rejected(structure, "max llm calls exceeded")
            candidate_sections = extractor.extract(structure=structure, toc_pages=toc_pages)
            if extractor.call_count > self.max_llm_calls:
                return self._rejected(structure, "max llm calls exceeded")
        logical_to_physical_offset = self.offset_resolver.resolve(
            structure=structure,
            candidate_sections=candidate_sections,
        )
        sections: list[DocumentSection] = []
        section_ids_by_level: dict[int, str] = {}
        for index, item in enumerate(candidate_sections, start=1):
            title = str(item.get("title") or "").strip()
            page_start = item.get("page_start")
            page_end = item.get("page_end")
            if not title or not isinstance(page_start, int):
                return self._rejected(structure, "invalid section fields")
            if page_end is not None and not isinstance(page_end, int):
                return self._rejected(structure, "invalid section fields")
            if page_start < 1 or (isinstance(page_end, int) and page_end < page_start):
                return self._rejected(structure, "invalid page range")
            level = int(item.get("level") or 1)
            section_id = f"toc-sec-{index}"
            parent_section_id = self._parent_section_id(
                sections_by_level=section_ids_by_level,
                level=level,
            )
            sections.append(
                DocumentSection(
                    section_id=section_id,
                    document_id=structure.document_id,
                    title=title,
                    level=level,
                    parent_section_id=parent_section_id,
                    page_start=page_start + logical_to_physical_offset,
                    page_end=page_end + logical_to_physical_offset if page_end is not None else None,
                    source="toc_refiner",
                    confidence=0.8,
                )
            )
            if parent_section_id:
                sections = self._append_child_section_id(
                    sections=sections,
                    parent_section_id=parent_section_id,
                    child_section_id=section_id,
                )
            section_ids_by_level = {
                existing_level: existing_section_id
                for existing_level, existing_section_id in section_ids_by_level.items()
                if existing_level < level
            }
            section_ids_by_level[level] = section_id

        if not sections:
            return self._rejected(structure, "no sections returned")

        sections = self.range_assigner.assign(sections)
        validation_accuracy = self.start_validator.validate(structure=structure, sections=sections)
        if validation_accuracy < self.minimum_validation_accuracy:
            return TocRefinementResult(
                structure=structure,
                accepted=False,
                reason="section start validation failed",
                validation_accuracy=validation_accuracy,
                logical_to_physical_offset=logical_to_physical_offset,
                llm_call_count=extractor.call_count if extractor else 0,
                warnings=["section start validation failed"],
            )

        refined = self.merger.merge(structure=structure, sections=sections)
        return TocRefinementResult(
            structure=refined,
            accepted=True,
            reason="accepted",
            validation_accuracy=validation_accuracy,
            logical_to_physical_offset=logical_to_physical_offset,
            llm_call_count=extractor.call_count if extractor else 0,
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

    def _parent_section_id(
        self,
        *,
        sections_by_level: dict[int, str],
        level: int,
    ) -> str | None:
        parent_levels = [item for item in sections_by_level if item < level]
        if not parent_levels:
            return None
        return sections_by_level[max(parent_levels)]

    def _append_child_section_id(
        self,
        *,
        sections: list[DocumentSection],
        parent_section_id: str,
        child_section_id: str,
    ) -> list[DocumentSection]:
        updated: list[DocumentSection] = []
        for section in sections:
            if section.section_id != parent_section_id:
                updated.append(section)
                continue
            child_ids = list(section.child_section_ids)
            if child_section_id not in child_ids:
                child_ids.append(child_section_id)
            updated.append(section.model_copy(update={"child_section_ids": child_ids}))
        return updated
