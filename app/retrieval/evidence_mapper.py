from app.domain.models import Evidence
from app.schemas.retrieval import EvidenceResponse


def to_evidence_response(evidence: Evidence) -> EvidenceResponse:
    metadata = evidence.metadata or {}
    chunk_id = metadata.get("chunk_id")
    workspace_node_id = metadata.get("workspace_node_id")
    if not workspace_node_id and chunk_id:
        workspace_node_id = f"chunk:{evidence.document_id}:{chunk_id}"
    elif not workspace_node_id and evidence.page_ref and evidence.page_ref.page_start:
        workspace_node_id = f"page:{evidence.document_id}:{evidence.page_ref.page_start}"
    elif not workspace_node_id:
        workspace_node_id = f"document:{evidence.document_id}"

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
        chunk_id=chunk_id,
        reference_id=metadata.get("reference_id"),
        workspace_node_id=workspace_node_id,
        metadata=metadata,
    )
