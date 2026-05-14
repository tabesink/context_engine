from app.domain.models import Evidence
from app.schemas.query import EvidenceResponse


def to_evidence_response(evidence: Evidence) -> EvidenceResponse:
    return EvidenceResponse(
        evidence_id=evidence.id,
        document_id=str(evidence.document_id),
        source_engine=evidence.source_engine,
        text=evidence.text,
        score=evidence.score,
        page_start=evidence.page_ref.page_start if evidence.page_ref else None,
        page_end=evidence.page_ref.page_end if evidence.page_ref else None,
        section_title=evidence.section_ref.title if evidence.section_ref else None,
        metadata=evidence.metadata,
    )
