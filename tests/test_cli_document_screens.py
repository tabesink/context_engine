from cli.screens.documents import (
    build_document_chunk_screen,
    build_document_section_screen,
    build_document_structure_screen,
)


def test_document_structure_screen_summarizes_canonical_structure() -> None:
    screen = build_document_structure_screen(
        {
            "document_id": "doc-1",
            "source": "document_structure",
            "tree": [{"title": "Safety", "level": 1, "page_start": 1, "page_end": 2}],
            "sections": [{"section_id": "sec-1"}],
            "source_chunks": [{"chunk_id": "chunk-1"}, {"chunk_id": "chunk-2"}],
            "assets": [{"asset_id": "asset-1"}],
        }
    )

    assert screen.summary["source"] == "document_structure"
    assert screen.summary["sections"] == 1
    assert screen.summary["source_chunks"] == 2
    assert screen.summary["assets"] == 1


def test_document_structure_screen_renders_canonical_page_ranges() -> None:
    screen = build_document_structure_screen(
        {
            "document_id": "doc-1",
            "source": "document_structure",
            "tree": [
                {"title": "Safety", "level": 1, "page_start": 1, "page_end": 2},
                {"title": "Single Page", "level": 1, "page_start": 3, "page_end": 3},
            ],
        }
    )

    rows = screen.sections[0].rows
    assert rows[0]["pages"] == "1-2"
    assert rows[1]["pages"] == "3"


def test_document_section_screen_renders_linked_blocks_chunks_and_assets() -> None:
    screen = build_document_section_screen(
        {
            "document_id": "doc-1",
            "section": {
                "section_id": "sec-1",
                "title": "Safety",
                "level": 1,
                "page_start": 1,
                "page_end": 2,
            },
            "blocks": [{"block_id": "block-1", "type": "paragraph", "text": "Wear eye protection."}],
            "source_chunks": [{"chunk_id": "chunk-1", "page_start": 1, "page_end": 1}],
            "assets": [{"asset_id": "asset-1", "asset_type": "figure", "caption": "PPE diagram"}],
        }
    )

    assert screen.title == "Document Section"
    assert screen.summary["document_id"] == "doc-1"
    assert screen.summary["section_id"] == "sec-1"
    assert screen.sections[0].rows[0]["field"] == "Title"
    assert screen.sections[0].rows[0]["value"] == "Safety"
    assert screen.sections[1].title == "Blocks"
    assert screen.sections[1].rows[0]["text"] == "Wear eye protection."
    assert screen.sections[2].title == "Source Chunks"
    assert screen.sections[2].rows[0]["pages"] == "1"
    assert screen.sections[3].title == "Assets"
    assert screen.sections[3].rows[0]["caption"] == "PPE diagram"


def test_document_chunk_screen_renders_chunk_metadata_and_text() -> None:
    screen = build_document_chunk_screen(
        {
            "document_id": "doc-1",
            "chunk_id": "chunk-1",
            "section_id": "sec-1",
            "block_ids": ["block-1", "block-2"],
            "page_start": 2,
            "page_end": 4,
            "asset_ids": ["asset-1"],
            "text": "Wear eye protection before servicing.",
            "metadata": {"semantic_owner": "lightrag", "section_path": ["Safety"]},
        }
    )

    assert screen.title == "Source Chunk"
    assert screen.summary["document_id"] == "doc-1"
    assert screen.summary["chunk_id"] == "chunk-1"
    assert screen.sections[0].rows[0]["field"] == "Section ID"
    assert screen.sections[0].rows[0]["value"] == "sec-1"
    assert screen.sections[0].rows[1]["value"] == "2-4"
    assert screen.sections[0].rows[2]["value"] == "block-1, block-2"
    assert screen.sections[0].rows[3]["value"] == "asset-1"
    assert screen.sections[1].title == "Text"
    assert screen.sections[1].text == "Wear eye protection before servicing."
    assert screen.sections[2].title == "Metadata"
    assert screen.sections[2].rows[1]["field"] == "section_path"
    assert screen.sections[2].rows[1]["value"] == "Safety"
