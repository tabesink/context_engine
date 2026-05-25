from app.domain.models import Evidence
from app.schemas.retrieval import EvidenceResponse


def to_evidence_response(evidence: Evidence) -> EvidenceResponse:
    metadata = evidence.metadata or {}
    return EvidenceResponse(
        evidence_id=evidence.id,
        document_id=str(evidence.document_id),
        source_engine=evidence.source_engine,
        text=evidence.text,
        score=evidence.score,
        page_start=evidence.page_ref.page_start if evidence.page_ref else None,
        page_end=evidence.page_ref.page_end if evidence.page_ref else None,
        section_title=evidence.section_ref.title if evidence.section_ref else None,
        source_path=metadata.get("source_path"),
        document_title=metadata.get("document_title"),
        chunk_id=metadata.get("chunk_id"),
        reference_id=metadata.get("reference_id"),
        metadata=metadata,
    )
