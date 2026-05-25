from pathlib import Path
from hashlib import sha256

from PIL import Image

from app.document_processing.chunk_builder import StructureAwareChunkBuilder
from app.document_processing.docling_parser import (
    AssetExtractor,
    DoclingParser,
    DoclingAssetPayload,
    DoclingParseResult,
    DocumentStructureBuilder,
)
from app.document_processing.models import (
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
)
from app.document_processing.pipeline import TextDoclingParser
from app.document_processing.storage_paths import DocumentStoragePaths


class FakeLabel:
    def __init__(self, name: str):
        self.name = name


class FakeProv:
    def __init__(self, page_no: int):
        self.page_no = page_no
        self.bbox = None


class FakeProvOptional:
    def __init__(self, page_no: int | None):
        self.page_no = page_no
        self.bbox = None


class FakeItem:
    def __init__(
        self,
        *,
        label: str,
        text: str = "",
        page_no: int = 1,
        image: object | None = None,
    ):
        self.label = FakeLabel(label)
        self.text = text
        self.prov = [FakeProv(page_no)]
        if image is not None:
            self.image = type("ImageRef", (), {"pil_image": image})()

    def caption_text(self, doc: object) -> str:
        del doc
        return self.text


class FakeTableItem(FakeItem):
    def export_to_markdown(self, doc: object) -> str:
        del doc
        return "| Part | Limit |\n| --- | --- |\n| Bolt | 10 Nm |"


class FakeTableImageItem(FakeTableItem):
    def __init__(self, *, page_no: int = 1):
        super().__init__(label="TABLE", page_no=page_no, image=RealFakeImage(width=900, height=400))


class FakeImage:
    def save(self, buffer: object, *, format: str) -> None:
        assert format == "PNG"
        buffer.write(b"fake png")


class RealFakeImage:
    def __init__(self, *, width: int = 1024, height: int = 256):
        self.width = width
        self.height = height

    def save(self, buffer: object, *, format: str) -> None:
        image = Image.new("RGB", (self.width, self.height), color="white")
        image.save(buffer, format=format)


class FakePage:
    size = type("Size", (), {"width": 612, "height": 792})()


class FakeDoclingDocument:
    pages = {1: FakePage()}

    def iterate_items(self):
        return iter(
            [
                (FakeItem(label="SECTION_HEADER", text="Safety", page_no=1), 1),
                (FakeItem(label="TEXT", text="Wear eye protection.", page_no=1), 1),
                (FakeTableItem(label="TABLE", page_no=1), 1),
                (FakeItem(label="PICTURE", text="Figure 1", page_no=1, image=FakeImage()), 1),
            ]
        )


class FakeConversionResult:
    document = FakeDoclingDocument()


class FakeConverter:
    def convert(self, source_path: Path) -> FakeConversionResult:
        assert source_path.name == "manual.pdf"
        return FakeConversionResult()


class FakeNestedDoclingDocument:
    pages = {1: FakePage(), 2: FakePage()}

    def iterate_items(self):
        return iter(
            [
                (FakeItem(label="TITLE", text="Maintenance", page_no=1), 1),
                (FakeItem(label="SECTION_HEADER", text="Hydraulics", page_no=2), 2),
                (FakeItem(label="LIST_ITEM", text="Inspect hoses.", page_no=2), 2),
                (FakeItem(label="CAPTION", text="Figure 2. Hydraulic circuit", page_no=2), 2),
                (FakeItem(label="IMAGE", text="", page_no=2, image=RealFakeImage()), 2),
                (FakeItem(label="PAGE_FOOTER", text="2", page_no=2), 2),
            ]
        )


class FakeNestedConversionResult:
    document = FakeNestedDoclingDocument()


class FakeNestedConverter:
    def convert(self, source_path: Path) -> FakeNestedConversionResult:
        assert source_path.name == "manual.pdf"
        return FakeNestedConversionResult()


class FakeTableImageDoclingDocument:
    pages = {1: FakePage()}

    def iterate_items(self):
        return iter(
            [
                (FakeItem(label="SECTION_HEADER", text="Torque Specs", page_no=1), 1),
                (FakeItem(label="TEXT", text="Use calibrated tools.", page_no=1), 1),
                (FakeTableImageItem(page_no=1), 1),
            ]
        )


class FakeTableImageConversionResult:
    document = FakeTableImageDoclingDocument()


class FakeTableImageConverter:
    def convert(self, source_path: Path) -> FakeTableImageConversionResult:
        assert source_path.name == "manual.pdf"
        return FakeTableImageConversionResult()


class FakeDetachedCaptionImageItem:
    def __init__(self, *, page_no: int):
        self.label = FakeLabel("IMAGE")
        self.text = ""
        self.prov = [FakeProv(page_no)]
        self.image = type("ImageRef", (), {"pil_image": RealFakeImage(width=600, height=300)})()


class FakeDetachedCaptionDoclingDocument:
    pages = {1: FakePage()}

    def iterate_items(self):
        return iter(
            [
                (FakeItem(label="SECTION_HEADER", text="Hydraulics", page_no=1), 1),
                (FakeItem(label="CAPTION", text="Figure 9. Hydraulic manifold", page_no=1), 1),
                (FakeDetachedCaptionImageItem(page_no=1), 1),
            ]
        )


class FakeDetachedCaptionConversionResult:
    document = FakeDetachedCaptionDoclingDocument()


class FakeDetachedCaptionConverter:
    def convert(self, source_path: Path) -> FakeDetachedCaptionConversionResult:
        assert source_path.name == "manual.pdf"
        return FakeDetachedCaptionConversionResult()


class FakeFallbackPageDoclingDocument:
    pages = {3: FakePage()}

    def iterate_items(self):
        heading = FakeItem(label="section-header", text="Electrical", page_no=1)
        heading.prov = [FakeProvOptional(None), FakeProvOptional(3)]
        paragraph = FakeItem(label="TEXT", text="Disconnect battery.", page_no=1)
        paragraph.prov = [FakeProvOptional(None), FakeProvOptional(3)]
        return iter(
            [
                (heading, 1),
                (paragraph, 1),
            ]
        )


class FakeFallbackPageConversionResult:
    document = FakeFallbackPageDoclingDocument()


class FakeFallbackPageConverter:
    def convert(self, source_path: Path) -> FakeFallbackPageConversionResult:
        assert source_path.name == "manual.pdf"
        return FakeFallbackPageConversionResult()


def test_text_docling_parser_builds_rich_document_structure(tmp_path: Path) -> None:
    source = tmp_path / "manual.txt"
    source.write_text("# Safety\nWear eye protection.\n\n# Service\nDisconnect power.", encoding="utf-8")
    parser = TextDoclingParser()

    structure = parser.parse(document_id="11111111-1111-4111-8111-111111111111", source_path=source)

    assert [section.title for section in structure.sections] == ["Safety", "Service"]
    assert structure.source_chunks[0].section_id == structure.sections[0].section_id
    assert structure.pages[0].page_number == 1
    assert structure.pages[0].text.startswith("Safety")
    assert "Disconnect power." in structure.pages[0].text


def test_document_structure_builder_extracts_assets_and_thumbnails(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"pdf")
    asset_bytes = b"fake image bytes"
    document_id = "11111111-1111-4111-8111-111111111111"
    section_id = f"{document_id}-sec-1"
    block_id = f"{document_id}-block-1"

    builder = DocumentStructureBuilder(
        asset_extractor=AssetExtractor(
            storage_paths=DocumentStoragePaths(storage_root=tmp_path),
        )
    )
    structure = builder.build(
        document_id=document_id,
        source_path=source,
        parsed=DoclingParseResult(
            pages=[DocumentPage(page_number=1, text="See figure 1.")],
            sections=[
                DocumentSection(
                    section_id=section_id,
                    document_id=document_id,
                    title="Safety",
                    level=1,
                    page_start=1,
                    page_end=1,
                )
            ],
            blocks=[
                DocumentBlock(
                    block_id=block_id,
                    document_id=document_id,
                    section_id=section_id,
                    type="figure",
                    text="Figure 1. Safety envelope.",
                    page_start=1,
                    page_end=1,
                    asset_ids=[f"{document_id}-asset-1"],
                )
            ],
            assets=[
                DoclingAssetPayload(
                    asset_id=f"{document_id}-asset-1",
                    filename="figure-1.png",
                    bytes_data=asset_bytes,
                    page_number=1,
                    section_id=section_id,
                    block_id=block_id,
                    caption="Figure 1",
                )
            ],
        ),
    )

    asset = structure.assets[0]
    assert asset.content_hash == sha256(asset_bytes).hexdigest()
    assert asset.storage_path == f"documents/{document_id}/assets/figure-1.png"
    assert asset.thumbnail_path == f"documents/{document_id}/assets/figure-1_thumb.png"
    assert (tmp_path / asset.storage_path).read_bytes() == asset_bytes
    assert (tmp_path / asset.thumbnail_path).read_bytes() == asset_bytes
    assert asset.block_id == block_id


def test_asset_extractor_deduplicates_identical_payloads(tmp_path: Path) -> None:
    document_id = "11111111-1111-4111-8111-111111111111"
    asset_bytes = b"same image bytes"
    extractor = AssetExtractor(storage_paths=DocumentStoragePaths(storage_root=tmp_path))

    assets = extractor.extract(
        document_id=document_id,
        assets=[
            DoclingAssetPayload(
                asset_id=f"{document_id}-asset-1",
                filename="figure-1.png",
                bytes_data=asset_bytes,
                block_id=f"{document_id}-block-1",
            ),
            DoclingAssetPayload(
                asset_id=f"{document_id}-asset-2",
                filename="figure-copy.png",
                bytes_data=asset_bytes,
                block_id=f"{document_id}-block-2",
            ),
        ],
    )

    assert [asset.asset_id for asset in assets] == [
        f"{document_id}-asset-1",
        f"{document_id}-asset-2",
    ]
    assert assets[0].storage_path == assets[1].storage_path
    assert assets[0].thumbnail_path == assets[1].thumbnail_path
    assert assets[1].block_id == f"{document_id}-block-2"
    assert len(list((tmp_path / "documents" / document_id / "assets").iterdir())) == 2


def test_docling_parser_converts_document_items_into_structure(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"pdf")
    document_id = "11111111-1111-4111-8111-111111111111"
    parser = DoclingParser(
        builder=DocumentStructureBuilder(
            asset_extractor=AssetExtractor(storage_paths=DocumentStoragePaths(storage_root=tmp_path))
        ),
        converter_factory=FakeConverter,
    )

    structure = parser.parse(document_id=document_id, source_path=source)

    assert structure.sections[0].title == "Safety"
    assert [block.type for block in structure.blocks] == ["heading", "paragraph", "table", "figure"]
    assert structure.blocks[2].text.startswith("| Part | Limit |")
    assert structure.assets[0].caption == "Figure 1"
    assert structure.assets[0].block_id == structure.blocks[3].block_id
    assert (tmp_path / structure.assets[0].storage_path).read_bytes() == b"fake png"
    assert structure.pages[0].width == 612
    assert "Wear eye protection." in structure.pages[0].text


def test_docling_parser_normalizes_labels_hierarchy_and_images(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"pdf")
    document_id = "11111111-1111-4111-8111-111111111111"
    parser = DoclingParser(
        builder=DocumentStructureBuilder(
            asset_extractor=AssetExtractor(storage_paths=DocumentStoragePaths(storage_root=tmp_path))
        ),
        converter_factory=FakeNestedConverter,
    )

    structure = parser.parse(document_id=document_id, source_path=source)

    assert [section.title for section in structure.sections] == ["Maintenance", "Hydraulics"]
    assert structure.sections[1].parent_section_id == structure.sections[0].section_id
    assert structure.sections[0].child_section_ids == [structure.sections[1].section_id]
    assert [block.type for block in structure.blocks] == [
        "heading",
        "heading",
        "list",
        "caption",
        "image",
        "page_footer",
    ]
    assert structure.assets[0].asset_type == "image"
    assert structure.assets[0].nearby_text is not None
    assert "Hydraulics" in structure.assets[0].nearby_text
    thumbnail = Image.open(tmp_path / structure.assets[0].thumbnail_path)
    assert thumbnail.width <= 512


def test_docling_parser_extracts_table_snapshot_assets(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"pdf")
    document_id = "11111111-1111-4111-8111-111111111111"
    parser = DoclingParser(
        builder=DocumentStructureBuilder(
            asset_extractor=AssetExtractor(storage_paths=DocumentStoragePaths(storage_root=tmp_path))
        ),
        converter_factory=FakeTableImageConverter,
    )

    structure = parser.parse(document_id=document_id, source_path=source)

    assert structure.blocks[2].type == "table"
    assert structure.blocks[2].asset_ids == [structure.assets[0].asset_id]
    assert structure.assets[0].asset_type == "table_image"
    assert structure.assets[0].section_id == structure.sections[0].section_id
    assert structure.assets[0].nearby_text == "Torque Specs\nUse calibrated tools."


def test_docling_parser_associates_detached_caption_with_following_image(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"pdf")
    document_id = "11111111-1111-4111-8111-111111111111"
    parser = DoclingParser(
        builder=DocumentStructureBuilder(
            asset_extractor=AssetExtractor(storage_paths=DocumentStoragePaths(storage_root=tmp_path))
        ),
        converter_factory=FakeDetachedCaptionConverter,
    )

    structure = parser.parse(document_id=document_id, source_path=source)

    assert structure.blocks[1].type == "caption"
    assert structure.blocks[2].type == "image"
    assert structure.assets[0].caption == "Figure 9. Hydraulic manifold"
    assert structure.assets[0].block_id == structure.blocks[2].block_id


def test_docling_parser_normalizes_hyphenated_labels_and_uses_provenance_fallback(tmp_path: Path) -> None:
    source = tmp_path / "manual.pdf"
    source.write_bytes(b"pdf")
    document_id = "11111111-1111-4111-8111-111111111111"
    parser = DoclingParser(
        builder=DocumentStructureBuilder(
            asset_extractor=AssetExtractor(storage_paths=DocumentStoragePaths(storage_root=tmp_path))
        ),
        converter_factory=FakeFallbackPageConverter,
    )

    structure = parser.parse(document_id=document_id, source_path=source)

    assert structure.sections[0].title == "Electrical"
    assert structure.sections[0].page_start == 3
    assert structure.blocks[0].type == "heading"
    assert structure.blocks[0].page_start == 3
    assert structure.blocks[1].page_start == 3


def test_structure_aware_chunk_builder_keeps_sections_and_inherits_assets() -> None:
    document_id = "11111111-1111-4111-8111-111111111111"
    safety_id = f"{document_id}-sec-1"
    service_id = f"{document_id}-sec-2"
    structure = DocumentStructure(
        document_id=document_id,
        source_file="manual.pdf",
        sections=[
            DocumentSection(
                section_id=safety_id,
                document_id=document_id,
                title="Safety",
                level=1,
                page_start=1,
                page_end=1,
            ),
            DocumentSection(
                section_id=service_id,
                document_id=document_id,
                title="Service",
                level=1,
                page_start=2,
                page_end=2,
            ),
        ],
        blocks=[
            DocumentBlock(
                block_id=f"{document_id}-block-1",
                document_id=document_id,
                section_id=safety_id,
                type="paragraph",
                text="Wear eye protection.",
                page_start=1,
                page_end=1,
                reading_order=1,
                asset_ids=[f"{document_id}-asset-1"],
            ),
            DocumentBlock(
                block_id=f"{document_id}-block-2",
                document_id=document_id,
                section_id=service_id,
                type="paragraph",
                text="Disconnect power.",
                page_start=2,
                page_end=2,
                reading_order=2,
            ),
        ],
        assets=[
            {
                "asset_id": f"{document_id}-asset-1",
                "document_id": document_id,
                "asset_type": "figure",
                "storage_path": "documents/doc/assets/figure.png",
                "content_hash": "hash-1",
                "block_id": f"{document_id}-block-1",
            }
        ],
    )

    updated = StructureAwareChunkBuilder(max_chars=200).build(structure)

    assert [chunk.section_id for chunk in updated.source_chunks] == [safety_id, service_id]
    assert updated.source_chunks[0].asset_ids == [f"{document_id}-asset-1"]
    assert updated.assets[0].chunk_id == f"{document_id}-source-chunk-1"
    assert updated.source_chunks[0].page_start == 1
    assert updated.source_chunks[1].page_start == 2
    assert updated.source_chunks[0].metadata["section_title"] == "Safety"
    assert updated.source_chunks[0].metadata["section_path"] == ["Safety"]
    assert updated.source_chunks[0].text.startswith("Section: Safety")


def test_structure_aware_chunk_builder_splits_large_sections_deterministically() -> None:
    document_id = "11111111-1111-4111-8111-111111111111"
    section_id = f"{document_id}-sec-1"
    structure = DocumentStructure(
        document_id=document_id,
        source_file="manual.pdf",
        sections=[
            DocumentSection(
                section_id=section_id,
                document_id=document_id,
                title="Safety",
                level=1,
            )
        ],
        blocks=[
            DocumentBlock(
                block_id=f"{document_id}-block-1",
                document_id=document_id,
                section_id=section_id,
                type="paragraph",
                text="A" * 10,
                reading_order=1,
            ),
            DocumentBlock(
                block_id=f"{document_id}-block-2",
                document_id=document_id,
                section_id=section_id,
                type="paragraph",
                text="B" * 10,
                reading_order=2,
            ),
        ],
    )

    updated = StructureAwareChunkBuilder(max_chars=12).build(structure)

    assert [chunk.chunk_id for chunk in updated.source_chunks] == [
        f"{document_id}-source-chunk-1",
        f"{document_id}-source-chunk-2",
    ]
    assert [chunk.block_ids for chunk in updated.source_chunks] == [
        [f"{document_id}-block-1"],
        [f"{document_id}-block-2"],
    ]


def test_structure_aware_chunk_builder_records_nested_section_path() -> None:
    document_id = "11111111-1111-4111-8111-111111111111"
    parent_id = f"{document_id}-sec-1"
    child_id = f"{document_id}-sec-2"
    structure = DocumentStructure(
        document_id=document_id,
        source_file="manual.pdf",
        sections=[
            DocumentSection(
                section_id=parent_id,
                document_id=document_id,
                title="Maintenance",
                level=1,
                child_section_ids=[child_id],
            ),
            DocumentSection(
                section_id=child_id,
                document_id=document_id,
                title="Hydraulic Service",
                level=2,
                parent_section_id=parent_id,
            ),
        ],
        blocks=[
            DocumentBlock(
                block_id=f"{document_id}-block-1",
                document_id=document_id,
                section_id=child_id,
                type="paragraph",
                text="Inspect the hydraulic circuit.",
            )
        ],
    )

    updated = StructureAwareChunkBuilder(max_chars=200).build(structure)

    assert updated.source_chunks[0].metadata["section_title"] == "Hydraulic Service"
    assert updated.source_chunks[0].metadata["section_path"] == [
        "Maintenance",
        "Hydraulic Service",
    ]
    assert updated.source_chunks[0].text.startswith("Section: Maintenance > Hydraulic Service")


def test_structure_aware_chunk_builder_uses_asset_caption_for_asset_only_chunk() -> None:
    document_id = "11111111-1111-4111-8111-111111111111"
    section_id = f"{document_id}-sec-1"
    asset_id = f"{document_id}-asset-1"
    structure = DocumentStructure(
        document_id=document_id,
        source_file="manual.pdf",
        sections=[
            DocumentSection(
                section_id=section_id,
                document_id=document_id,
                title="Electrical",
                level=1,
            )
        ],
        blocks=[
            DocumentBlock(
                block_id=f"{document_id}-block-1",
                document_id=document_id,
                section_id=section_id,
                type="figure",
                text="",
                asset_ids=[asset_id],
            )
        ],
        assets=[
            {
                "asset_id": asset_id,
                "document_id": document_id,
                "asset_type": "figure",
                "storage_path": "documents/doc/assets/figure.png",
                "content_hash": "hash-1",
                "caption": "Figure 6. Main controller wiring diagram",
            }
        ],
    )

    updated = StructureAwareChunkBuilder(max_chars=200).build(structure)

    assert updated.source_chunks[0].text == (
        "Section: Electrical\n\nFigure 6. Main controller wiring diagram"
    )
