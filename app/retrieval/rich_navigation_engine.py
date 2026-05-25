from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.document_processing.models import DocumentAsset, DocumentBlock, DocumentPage, DocumentSection, SourceChunk
from app.domain.models import Evidence, PageRef, SectionRef
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository


@dataclass(frozen=True)
class _Candidate:
    evidence: Evidence
    priority: int


class RichNavigationEngine:
    name = "navigation"

    _SOURCE_PRIORITY = {
        "source_chunk": 5,
        "block": 4,
        "section": 3,
        "page": 2,
        "asset": 1,
    }

    def __init__(self, session: Session):
        self.documents = DocumentRepository(session)
        self.processing = DocumentProcessingRepository(session)

    def retrieve(
        self,
        *,
        query: str,
        document_ids: list[str] | None,
        top_k: int,
        user_id: str,
    ) -> list[Evidence]:
        del user_id
        query_terms = {term.lower() for term in query.split() if len(term) > 2}
        candidates: list[_Candidate] = []
        for document_id in self._target_document_ids(document_ids):
            structure = self.processing.get_structure(document_id)
            if not structure:
                continue
            document_uuid = self._as_uuid(document_id)
            if not document_uuid:
                continue
            section_map = {section.section_id: section for section in structure.sections}
            for chunk in structure.source_chunks:
                candidate = self._chunk_candidate(
                    document_id=document_id,
                    document_uuid=document_uuid,
                    chunk=chunk,
                    section=section_map.get(chunk.section_id),
                    query_terms=query_terms,
                )
                if candidate:
                    candidates.append(candidate)
            for block in structure.blocks:
                candidate = self._block_candidate(
                    document_id=document_id,
                    document_uuid=document_uuid,
                    block=block,
                    section=section_map.get(block.section_id),
                    query_terms=query_terms,
                )
                if candidate:
                    candidates.append(candidate)
            for section in structure.sections:
                candidate = self._section_candidate(
                    document_id=document_id,
                    document_uuid=document_uuid,
                    section=section,
                    query_terms=query_terms,
                )
                if candidate:
                    candidates.append(candidate)
            for page in structure.pages:
                candidate = self._page_candidate(
                    document_id=document_id,
                    document_uuid=document_uuid,
                    page=page,
                    query_terms=query_terms,
                )
                if candidate:
                    candidates.append(candidate)
            for asset in structure.assets:
                candidate = self._asset_candidate(
                    document_id=document_id,
                    document_uuid=document_uuid,
                    asset=asset,
                    section=section_map.get(asset.section_id),
                    query_terms=query_terms,
                )
                if candidate:
                    candidates.append(candidate)

        deduped = self._dedupe(candidates)
        return [
            candidate.evidence
            for candidate in sorted(
                deduped.values(),
                key=lambda item: (item.evidence.score or 0.0, item.priority),
                reverse=True,
            )[:top_k]
        ]

    def _target_document_ids(self, explicit_ids: list[str] | None) -> list[str]:
        if explicit_ids:
            return explicit_ids
        return [document.id for document in self.documents.list_ready()]

    def _score(self, text: str, query_terms: set[str], *, base: float) -> float:
        if not query_terms:
            return base * 0.1
        text_lower = text.lower()
        matches = sum(1 for term in query_terms if term in text_lower)
        if matches == 0:
            return 0.0
        return base + (matches / len(query_terms))

    def _section_ref(self, document_uuid: UUID, section: DocumentSection | None) -> SectionRef | None:
        if not section:
            return None
        return SectionRef(
            document_id=document_uuid,
            section_id=section.section_id,
            title=section.title,
            page_start=section.page_start,
            page_end=section.page_end,
        )

    def _page_ref(
        self,
        document_uuid: UUID,
        *,
        page_start: int | None,
        page_end: int | None = None,
    ) -> PageRef | None:
        if page_start is None and page_end is None:
            return None
        return PageRef(
            document_id=document_uuid,
            page_start=page_start,
            page_end=page_end if page_end is not None else page_start,
        )

    def _chunk_candidate(
        self,
        *,
        document_id: str,
        document_uuid: UUID,
        chunk: SourceChunk,
        section: DocumentSection | None,
        query_terms: set[str],
    ) -> _Candidate | None:
        score = self._score(chunk.text, query_terms, base=3.0)
        if score <= 0:
            return None
        evidence = Evidence(
            id=f"navigation:{document_id}:chunk:{chunk.chunk_id}",
            document_id=document_uuid,
            source_engine=self.name,
            text=chunk.text,
            score=score,
            page_ref=self._page_ref(document_uuid, page_start=chunk.page_start, page_end=chunk.page_end),
            section_ref=self._section_ref(document_uuid, section),
            metadata={"source": "source_chunk", "chunk_id": chunk.chunk_id},
        )
        return _Candidate(evidence=evidence, priority=self._SOURCE_PRIORITY["source_chunk"])

    def _block_candidate(
        self,
        *,
        document_id: str,
        document_uuid: UUID,
        block: DocumentBlock,
        section: DocumentSection | None,
        query_terms: set[str],
    ) -> _Candidate | None:
        text = f"{section.title if section else ''} {block.text}".strip()
        score = self._score(text, query_terms, base=2.0)
        if score <= 0:
            return None
        evidence = Evidence(
            id=f"navigation:{document_id}:block:{block.block_id}",
            document_id=document_uuid,
            source_engine=self.name,
            text=block.text,
            score=score,
            page_ref=self._page_ref(document_uuid, page_start=block.page_start, page_end=block.page_end),
            section_ref=self._section_ref(document_uuid, section),
            metadata={"source": "block", "block_id": block.block_id},
        )
        return _Candidate(evidence=evidence, priority=self._SOURCE_PRIORITY["block"])

    def _section_candidate(
        self,
        *,
        document_id: str,
        document_uuid: UUID,
        section: DocumentSection,
        query_terms: set[str],
    ) -> _Candidate | None:
        score = self._score(section.title, query_terms, base=1.5)
        if score <= 0:
            return None
        evidence = Evidence(
            id=f"navigation:{document_id}:section:{section.section_id}",
            document_id=document_uuid,
            source_engine=self.name,
            text=section.title,
            score=score,
            page_ref=self._page_ref(
                document_uuid,
                page_start=section.page_start,
                page_end=section.page_end,
            ),
            section_ref=self._section_ref(document_uuid, section),
            metadata={"source": "section", "section_id": section.section_id},
        )
        return _Candidate(evidence=evidence, priority=self._SOURCE_PRIORITY["section"])

    def _page_candidate(
        self,
        *,
        document_id: str,
        document_uuid: UUID,
        page: DocumentPage,
        query_terms: set[str],
    ) -> _Candidate | None:
        text = page.text or f"Page {page.page_number}"
        score = self._score(text, query_terms, base=1.0)
        if score <= 0:
            return None
        evidence = Evidence(
            id=f"navigation:{document_id}:page:{page.page_number}",
            document_id=document_uuid,
            source_engine=self.name,
            text=text,
            score=score,
            page_ref=self._page_ref(
                document_uuid,
                page_start=page.page_number,
                page_end=page.page_number,
            ),
            metadata={"source": "page", "page_number": page.page_number, "page_metadata": page.metadata},
        )
        return _Candidate(evidence=evidence, priority=self._SOURCE_PRIORITY["page"])

    def _asset_candidate(
        self,
        *,
        document_id: str,
        document_uuid: UUID,
        asset: DocumentAsset,
        section: DocumentSection | None,
        query_terms: set[str],
    ) -> _Candidate | None:
        description = " ".join(
            part for part in (asset.caption, asset.nearby_text, asset.generated_description) if part
        )
        if not description:
            return None
        score = self._score(description, query_terms, base=0.75)
        if score <= 0:
            return None
        evidence = Evidence(
            id=f"navigation:{document_id}:asset:{asset.asset_id}",
            document_id=document_uuid,
            source_engine=self.name,
            text=description,
            score=score,
            page_ref=self._page_ref(
                document_uuid,
                page_start=asset.page_number,
                page_end=asset.page_number,
            ),
            section_ref=self._section_ref(document_uuid, section),
            metadata={"source": "asset", "asset_id": asset.asset_id},
        )
        return _Candidate(evidence=evidence, priority=self._SOURCE_PRIORITY["asset"])

    def _dedupe(self, candidates: list[_Candidate]) -> dict[tuple, _Candidate]:
        deduped: dict[tuple, _Candidate] = {}
        for candidate in candidates:
            evidence = candidate.evidence
            key = (
                str(evidence.document_id),
                evidence.metadata.get("source"),
                evidence.page_ref.page_start if evidence.page_ref else None,
                evidence.section_ref.section_id if evidence.section_ref else None,
                evidence.text.strip().lower(),
            )
            existing = deduped.get(key)
            if not existing:
                deduped[key] = candidate
                continue
            existing_score = existing.evidence.score or 0.0
            candidate_score = candidate.evidence.score or 0.0
            if candidate.priority > existing.priority or (
                candidate.priority == existing.priority and candidate_score > existing_score
            ):
                deduped[key] = candidate
        return deduped

    def _as_uuid(self, document_id: str) -> UUID | None:
        try:
            return UUID(document_id)
        except ValueError:
            return None
