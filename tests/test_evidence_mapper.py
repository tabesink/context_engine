from uuid import uuid4

from app.domain.models import Evidence, PageRef, SectionRef
from app.retrieval.evidence_mapper import to_evidence_response


def test_evidence_mapper_preserves_page_and_section_metadata() -> None:
    document_id = uuid4()
    evidence = Evidence(
        id="evidence-1",
        document_id=document_id,
        source_engine="navigation",
        text="Page evidence.",
        score=0.8,
        page_ref=PageRef(document_id=document_id, page_start=2, page_end=3),
        section_ref=SectionRef(
            document_id=document_id,
            section_id="install",
            title="Installation",
            page_start=2,
            page_end=3,
        ),
        metadata={"source": "manual"},
    )

    response = to_evidence_response(evidence)

    assert response.evidence_id == "evidence-1"
    assert response.document_id == str(document_id)
    assert response.page_start == 2
    assert response.page_end == 3
    assert response.section_title == "Installation"
    assert response.metadata == {"source": "manual"}


def test_evidence_mapper_projects_display_metadata() -> None:
    document_id = uuid4()
    evidence = Evidence(
        id="evidence-1",
        document_id=document_id,
        source_engine="lightrag",
        text="Source evidence.",
        metadata={
            "source_path": "manual.pdf",
            "document_title": "Service Manual",
            "chunk_id": "chunk-001",
            "reference_id": "ref-001",
        },
    )

    response = to_evidence_response(evidence)

    assert response.source_path == "manual.pdf"
    assert response.document_title == "Service Manual"
    assert response.chunk_id == "chunk-001"
    assert response.reference_id == "ref-001"
    assert response.metadata == {
        "source_path": "manual.pdf",
        "document_title": "Service Manual",
        "chunk_id": "chunk-001",
        "reference_id": "ref-001",
    }
