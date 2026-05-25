from app.document_processing.models import (
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
)
from app.document_processing.refinement import (
    PageOffsetResolver,
    SectionRangeAssigner,
    StructureQualityScorer,
    TocJsonExtractor,
    TocPageDetector,
    TocRefiner,
)


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


def test_toc_refiner_extracts_candidates_assigns_blocks_and_reports_calls() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[
            DocumentPage(page_number=1, text="Table of contents\nSafety .... 2"),
            DocumentPage(page_number=2, text="Safety"),
        ],
        blocks=[
            DocumentBlock(
                block_id="block-1",
                document_id="doc-1",
                type="paragraph",
                text="Wear eye protection.",
                page_start=2,
                page_end=2,
            )
        ],
        assets=[
            DocumentAsset(
                asset_id="asset-1",
                document_id="doc-1",
                asset_type="figure",
                storage_path="documents/doc-1/assets/figure.png",
                content_hash="hash-1",
                block_id="block-1",
                page_number=2,
            )
        ],
    )

    result = TocRefiner(
        extractor=TocJsonExtractor(
            candidate_sections=[
                {
                    "title": "Safety",
                    "page_start": 1,
                    "page_end": 1,
                    "physical_page_start": 2,
                }
            ]
        )
    ).refine(structure)

    assert TocPageDetector().detect(structure) == [1]
    assert result.accepted is True
    assert result.logical_to_physical_offset == 1
    assert result.llm_call_count == 1
    assert result.structure.sections[0].page_start == 2
    assert result.structure.blocks[0].section_id == "toc-sec-1"
    assert result.structure.assets[0].section_id == "toc-sec-1"


def test_toc_json_extractor_parses_common_toc_line_formats() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[
            DocumentPage(
                page_number=1,
                text="Table of contents\n1 Safety .... 2\n1.1 PPE  3\nAppendix A .... 9",
            )
        ],
    )

    sections = TocJsonExtractor().extract(structure=structure, toc_pages=[1])

    assert sections == [
        {"title": "Safety", "level": 1, "page_start": 2},
        {"title": "PPE", "level": 2, "page_start": 3},
        {"title": "Appendix A", "level": 1, "page_start": 9},
    ]


def test_toc_refiner_uses_extracted_toc_text_when_candidates_are_not_injected() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[
            DocumentPage(page_number=1, text="Table of contents\n1 Safety .... 2\n1.1 PPE .... 3"),
            DocumentPage(page_number=2, text="Safety"),
            DocumentPage(page_number=3, text="PPE"),
        ],
        blocks=[
            DocumentBlock(
                block_id="block-1",
                document_id="doc-1",
                type="paragraph",
                text="Wear eye protection.",
                page_start=3,
                page_end=3,
            )
        ],
    )

    result = TocRefiner(extractor=TocJsonExtractor()).refine(structure)

    assert result.accepted is True
    assert result.llm_call_count == 1
    assert [section.title for section in result.structure.sections] == ["Safety", "PPE"]
    assert result.structure.sections[1].parent_section_id == "toc-sec-1"
    assert result.structure.blocks[0].section_id == "toc-sec-2"


def test_page_offset_resolver_matches_titles_to_physical_pages() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[
            DocumentPage(page_number=1, text="Table of contents\nSafety .... 1\nMaintenance .... 2"),
            DocumentPage(page_number=5, text="Safety\nWear eye protection."),
            DocumentPage(page_number=6, text="Maintenance\nInspect hoses."),
        ],
    )

    offset = PageOffsetResolver().resolve(
        structure=structure,
        candidate_sections=[
            {"title": "Safety", "page_start": 1},
            {"title": "Maintenance", "page_start": 2},
        ],
    )

    assert offset == 4


def test_toc_refiner_applies_title_matched_page_offset() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[
            DocumentPage(page_number=1, text="Table of contents\nSafety .... 1"),
            DocumentPage(page_number=5, text="Safety\nWear eye protection."),
        ],
        blocks=[
            DocumentBlock(
                block_id="block-1",
                document_id="doc-1",
                type="paragraph",
                text="Wear eye protection.",
                page_start=5,
                page_end=5,
            )
        ],
    )

    result = TocRefiner(
        extractor=TocJsonExtractor(candidate_sections=[{"title": "Safety", "page_start": 1}]),
        minimum_validation_accuracy=1.0,
    ).refine(structure)

    assert result.accepted is True
    assert result.logical_to_physical_offset == 4
    assert result.structure.sections[0].page_start == 5
    assert result.structure.blocks[0].section_id == "toc-sec-1"


def test_toc_refiner_rejects_sections_when_title_is_not_on_start_page() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[
            DocumentPage(page_number=1, text="Table of contents\nSafety .... 2"),
            DocumentPage(page_number=2, text="Maintenance overview"),
        ],
    )

    result = TocRefiner(
        extractor=TocJsonExtractor(
            candidate_sections=[{"title": "Safety", "page_start": 2, "page_end": 2}]
        ),
        minimum_validation_accuracy=1.0,
    ).refine(structure)

    assert result.accepted is False
    assert result.reason == "section start validation failed"
    assert result.validation_accuracy == 0.0
    assert result.structure is structure


def test_toc_refiner_accepts_sections_when_title_matches_normalized_page_text() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[
            DocumentPage(page_number=1, text="Table of contents\nHydraulic-Service .... 2"),
            DocumentPage(page_number=2, text="Hydraulic Service\nInspect hoses."),
        ],
    )

    result = TocRefiner(
        extractor=TocJsonExtractor(
            candidate_sections=[{"title": "Hydraulic-Service", "page_start": 2, "page_end": 2}]
        ),
        minimum_validation_accuracy=1.0,
    ).refine(structure)

    assert result.accepted is True
    assert result.validation_accuracy == 1.0
    assert result.structure.sections[0].title == "Hydraulic-Service"


def test_toc_refiner_enforces_max_llm_calls() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[DocumentPage(page_number=1, text="Table of contents\nSafety .... 1")],
    )

    result = TocRefiner(
        extractor=TocJsonExtractor(
            candidate_sections=[{"title": "Safety", "page_start": 1, "page_end": 1}]
        ),
        max_llm_calls=0,
    ).refine(structure)

    assert result.accepted is False
    assert result.reason == "max llm calls exceeded"
    assert result.structure is structure


def test_toc_refiner_preserves_nested_sections_and_assigns_deepest_match() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[DocumentPage(page_number=1, text="Maintenance\nHydraulics")],
        blocks=[
            DocumentBlock(
                block_id="block-1",
                document_id="doc-1",
                type="paragraph",
                text="Inspect hydraulic hoses.",
                page_start=1,
                page_end=1,
            )
        ],
        assets=[
            DocumentAsset(
                asset_id="asset-1",
                document_id="doc-1",
                asset_type="figure",
                storage_path="documents/doc-1/assets/figure.png",
                content_hash="hash-1",
                block_id="block-1",
                page_number=1,
            )
        ],
    )

    result = TocRefiner().refine(
        structure,
        candidate_sections=[
            {"title": "Maintenance", "level": 1, "page_start": 1, "page_end": 1},
            {"title": "Hydraulics", "level": 2, "page_start": 1, "page_end": 1},
        ],
    )

    assert result.accepted is True
    assert result.structure.sections[1].parent_section_id == "toc-sec-1"
    assert result.structure.sections[0].child_section_ids == ["toc-sec-2"]
    assert result.structure.blocks[0].section_id == "toc-sec-2"
    assert result.structure.assets[0].section_id == "toc-sec-2"
    assert result.structure.sections[1].block_ids == ["block-1"]


def test_section_range_assigner_keeps_children_inside_parent_range() -> None:
    sections = SectionRangeAssigner().assign(
        [
            DocumentSection(
                section_id="toc-sec-1",
                document_id="doc-1",
                title="Maintenance",
                level=1,
                page_start=1,
            ),
            DocumentSection(
                section_id="toc-sec-2",
                document_id="doc-1",
                title="Hydraulics",
                level=2,
                page_start=2,
            ),
            DocumentSection(
                section_id="toc-sec-3",
                document_id="doc-1",
                title="Electrical",
                level=1,
                page_start=5,
            ),
        ]
    )

    assert sections[0].page_end == 4
    assert sections[1].page_end == 4
    assert sections[2].page_end == 5
