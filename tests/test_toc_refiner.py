from app.document_processing.models import DocumentPage, DocumentStructure
from app.document_processing.refinement import StructureQualityScorer, TocRefiner


def test_structure_quality_requests_toc_refiner_for_weak_sectioning() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[DocumentPage(page_number=1, text="Table of contents\n1 Safety .... 4")],
        blocks=[],
        sections=[],
    )

    quality = StructureQualityScorer().score(structure)

    assert quality.has_toc is True
    assert quality.should_run_toc_refiner is True
    assert "no sections detected" in quality.reasons


def test_toc_refiner_accepts_valid_sections_and_rejects_invalid_output() -> None:
    structure = DocumentStructure(document_id="doc-1", source_file="manual.pdf")
    accepted = TocRefiner().refine(
        structure,
        candidate_sections=[{"title": "Safety", "page_start": 1, "page_end": 3}],
    )
    rejected = TocRefiner().refine(
        structure,
        candidate_sections=[{"title": "", "page_start": 3, "page_end": 1}],
    )

    assert accepted.accepted is True
    assert accepted.structure.sections[0].source == "toc_refiner"
    assert rejected.accepted is False
    assert rejected.structure is structure
