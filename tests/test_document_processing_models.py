from app.document_processing.models import (
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
    SourceChunk,
    StructureQuality,
)


def test_document_structure_serializes_source_chunks_without_semantic_ownership() -> None:
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[DocumentPage(page_number=1, text="Safety overview")],
        sections=[
            DocumentSection(
                section_id="sec-1",
                document_id="doc-1",
                title="Safety",
                level=1,
                page_start=1,
                page_end=1,
                block_ids=["block-1"],
            )
        ],
        blocks=[
            DocumentBlock(
                block_id="block-1",
                document_id="doc-1",
                section_id="sec-1",
                type="paragraph",
                text="Wear eye protection before servicing.",
                page_start=1,
                page_end=1,
                asset_ids=["asset-1"],
            )
        ],
        source_chunks=[
            SourceChunk(
                chunk_id="source-chunk-1",
                document_id="doc-1",
                section_id="sec-1",
                block_ids=["block-1"],
                text="Wear eye protection before servicing.",
                page_start=1,
                page_end=1,
                asset_ids=["asset-1"],
            )
        ],
        assets=[
            DocumentAsset(
                asset_id="asset-1",
                document_id="doc-1",
                asset_type="figure",
                storage_path="documents/doc-1/assets/asset-1.png",
                content_hash="hash-1",
                page_number=1,
                section_id="sec-1",
                block_id="block-1",
                chunk_id="source-chunk-1",
                caption="Safety glasses diagram",
            )
        ],
        quality=StructureQuality(block_count=1, section_count=1, asset_count=1, score=0.9),
    )

    payload = structure.model_dump()

    assert payload["source_chunks"][0]["chunk_id"] == "source-chunk-1"
    assert payload["source_chunks"][0]["asset_ids"] == ["asset-1"]
    assert "semantic_chunks" not in payload
    assert structure.source_chunks[0].metadata["semantic_owner"] == "lightrag"
