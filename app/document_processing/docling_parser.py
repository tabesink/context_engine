from collections.abc import Callable
from dataclasses import dataclass, field
from importlib import import_module
from io import BytesIO
from pathlib import Path
from shutil import copyfile
from hashlib import sha256
from typing import Any

from app.document_processing.models import (
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
)
from app.document_processing.storage_paths import DocumentStoragePaths


@dataclass(frozen=True)
class DoclingAssetPayload:
    asset_id: str
    filename: str
    bytes_data: bytes | None = None
    source_path: Path | None = None
    asset_type: str = "figure"
    mime_type: str = "image/png"
    page_number: int | None = None
    section_id: str | None = None
    block_id: str | None = None
    caption: str | None = None
    nearby_text: str | None = None
    bbox: dict | None = None


@dataclass(frozen=True)
class DoclingParseResult:
    pages: list[DocumentPage] = field(default_factory=list)
    sections: list[DocumentSection] = field(default_factory=list)
    blocks: list[DocumentBlock] = field(default_factory=list)
    assets: list[DoclingAssetPayload] = field(default_factory=list)
    parser_version: str | None = None
    warnings: list[str] = field(default_factory=list)


class ThumbnailGenerator:
    """Creates bounded thumbnails, falling back to a copy for non-image test payloads."""

    def __init__(self, *, max_width: int = 512):
        self.max_width = max_width

    def generate(self, *, source_path: Path, thumbnail_path: Path) -> Path:
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            image_module = import_module("PIL.Image")
            image = image_module.open(source_path)
            image.thumbnail((self.max_width, self.max_width))
            image.save(thumbnail_path)
        except Exception:
            copyfile(source_path, thumbnail_path)
        return thumbnail_path


class AssetExtractor:
    def __init__(
        self,
        *,
        storage_paths: DocumentStoragePaths | None = None,
        thumbnail_generator: ThumbnailGenerator | None = None,
    ):
        self.storage_paths = storage_paths or DocumentStoragePaths()
        self.thumbnail_generator = thumbnail_generator or ThumbnailGenerator()

    def extract(self, *, document_id: str, assets: list[DoclingAssetPayload]) -> list[DocumentAsset]:
        extracted: list[DocumentAsset] = []
        paths_by_hash: dict[str, tuple[Path, Path]] = {}
        for payload in assets:
            asset_path = self.storage_paths.asset_path(document_id=document_id, filename=payload.filename)
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            data = self._asset_bytes(payload)
            content_hash = sha256(data).hexdigest()
            thumbnail_path = self.storage_paths.asset_path(
                document_id=document_id,
                filename=self._thumbnail_filename(payload.filename),
            )
            if content_hash in paths_by_hash:
                asset_path, thumbnail_path = paths_by_hash[content_hash]
            else:
                asset_path.write_bytes(data)
                self.thumbnail_generator.generate(source_path=asset_path, thumbnail_path=thumbnail_path)
                paths_by_hash[content_hash] = (asset_path, thumbnail_path)
            extracted.append(
                DocumentAsset(
                    asset_id=payload.asset_id,
                    document_id=document_id,
                    asset_type=payload.asset_type,
                    storage_path=self._relative_storage_path(asset_path),
                    thumbnail_path=self._relative_storage_path(thumbnail_path),
                    mime_type=payload.mime_type,
                    content_hash=content_hash,
                    page_number=payload.page_number,
                    section_id=payload.section_id,
                    block_id=payload.block_id,
                    caption=payload.caption,
                    nearby_text=payload.nearby_text,
                    bbox=payload.bbox,
                )
            )
        return extracted

    def _asset_bytes(self, payload: DoclingAssetPayload) -> bytes:
        if payload.bytes_data is not None:
            return payload.bytes_data
        if payload.source_path is not None:
            return payload.source_path.read_bytes()
        raise ValueError("Docling asset payload must include bytes_data or source_path")

    def _thumbnail_filename(self, filename: str) -> str:
        path = Path(filename)
        return f"{path.stem}_thumb{path.suffix or '.png'}"

    def _relative_storage_path(self, path: Path) -> str:
        try:
            return path.relative_to(self.storage_paths.storage_root).as_posix()
        except ValueError:
            return path.as_posix()


class DocumentStructureBuilder:
    def __init__(self, *, asset_extractor: AssetExtractor | None = None):
        self.asset_extractor = asset_extractor or AssetExtractor()

    def build(
        self,
        *,
        document_id: str,
        source_path: Path,
        parsed: DoclingParseResult,
    ) -> DocumentStructure:
        assets = self.asset_extractor.extract(document_id=document_id, assets=parsed.assets)
        return DocumentStructure(
            document_id=document_id,
            source_file=str(source_path),
            parser_version=parsed.parser_version,
            pages=parsed.pages,
            sections=parsed.sections,
            blocks=parsed.blocks,
            assets=assets,
            warnings=parsed.warnings,
        )


class DoclingParser:
    """Boundary for real Docling integration; accepts injected parse results in tests."""

    def __init__(
        self,
        *,
        builder: DocumentStructureBuilder | None = None,
        converter_factory: Callable[[], Any] | None = None,
    ):
        self.builder = builder or DocumentStructureBuilder()
        self.converter_factory = converter_factory

    def parse(
        self,
        *,
        document_id: str,
        source_path: Path,
        parsed: DoclingParseResult | None = None,
    ) -> DocumentStructure:
        if parsed is None:
            converter = self._converter()
            parsed = self._parse_conversion_result(
                document_id=document_id,
                conversion_result=converter.convert(source_path),
            )
        return self.builder.build(document_id=document_id, source_path=source_path, parsed=parsed)

    def _converter(self) -> Any:
        if self.converter_factory is not None:
            return self.converter_factory()

        try:
            base_models = import_module("docling.datamodel.base_models")
            pipeline_module = import_module("docling.datamodel.pipeline_options")
            converter_module = import_module("docling.document_converter")
        except ImportError as exc:
            raise RuntimeError("Docling is not installed") from exc

        input_format = base_models.InputFormat
        pipeline_options_cls = pipeline_module.PdfPipelineOptions
        document_converter_cls = converter_module.DocumentConverter
        pdf_format_option_cls = converter_module.PdfFormatOption

        pipeline_options = pipeline_options_cls()
        pipeline_options.generate_picture_images = True
        pipeline_options.generate_page_images = True
        pipeline_options.images_scale = 2.0
        return document_converter_cls(
            format_options={
                input_format.PDF: pdf_format_option_cls(pipeline_options=pipeline_options),
            }
        )

    def _parse_conversion_result(
        self,
        *,
        document_id: str,
        conversion_result: Any,
    ) -> DoclingParseResult:
        doc = conversion_result.document
        sections: list[DocumentSection] = []
        blocks: list[DocumentBlock] = []
        assets: list[DoclingAssetPayload] = []
        page_text: dict[int, list[str]] = {}
        current_section_id: str | None = None
        sections_by_level: dict[int, str] = {}
        warnings: list[str] = []

        for index, value in enumerate(doc.iterate_items(), start=1):
            item, level = self._iterated_item(value)
            label = self._label_name(item)
            page_number = self._page_number(item) or 1
            text = self._item_text(item=item, doc=doc)
            block_id = f"{document_id}-block-{index}"
            nearby_text = "\n".join(page_text.get(page_number, [])[-3:]) or None
            if text:
                page_text.setdefault(page_number, []).append(text)

            block_type = self._block_type(label)
            if block_type == "heading" and text:
                section_id = f"{document_id}-sec-{len(sections) + 1}"
                section_level = max(int(level or 1), 1)
                parent_section_id = self._parent_section_id(
                    sections_by_level=sections_by_level,
                    level=section_level,
                )
                current_section_id = section_id
                sections.append(
                    DocumentSection(
                        section_id=section_id,
                        document_id=document_id,
                        title=text,
                        level=section_level,
                        parent_section_id=parent_section_id,
                        page_start=page_number,
                        page_end=page_number,
                    )
                )
                if parent_section_id:
                    sections = self._append_child_section_id(
                        sections=sections,
                        parent_section_id=parent_section_id,
                        child_section_id=section_id,
                    )
                sections_by_level = {
                    existing_level: existing_section_id
                    for existing_level, existing_section_id in sections_by_level.items()
                    if existing_level < section_level
                }
                sections_by_level[section_level] = section_id
            elif block_type == "unknown":
                warnings.append(f"unknown Docling label: {label or '<empty>'}")

            asset_ids: list[str] = []
            if block_type in {"figure", "image", "table"}:
                asset_payload = self._asset_payload(
                    document_id=document_id,
                    item=item,
                    doc=doc,
                    block_id=block_id,
                    section_id=current_section_id,
                    page_number=page_number,
                    index=len(assets) + 1,
                    asset_type="table_image" if block_type == "table" else block_type,
                    nearby_text=nearby_text,
                )
                if asset_payload is not None:
                    assets.append(asset_payload)
                    asset_ids.append(asset_payload.asset_id)

            block = DocumentBlock(
                block_id=block_id,
                document_id=document_id,
                section_id=current_section_id,
                type=block_type,
                text=text,
                page_start=page_number,
                page_end=page_number,
                bbox=self._bbox(item),
                reading_order=index,
                asset_ids=asset_ids,
            )
            blocks.append(block)
            if current_section_id and sections:
                sections[-1].block_ids.append(block_id)

        pages = self._pages(doc=doc, page_text=page_text)
        return DoclingParseResult(
            pages=pages,
            sections=sections,
            blocks=blocks,
            assets=assets,
            parser_version=self._docling_version(),
            warnings=warnings,
        )

    def _iterated_item(self, value: Any) -> tuple[Any, int]:
        if isinstance(value, tuple):
            item = value[0]
            level = value[1] if len(value) > 1 and isinstance(value[1], int) else 1
            return item, level
        return value, 1

    def _label_name(self, item: Any) -> str:
        label = getattr(item, "label", None)
        return str(getattr(label, "name", label) or "").upper()

    def _block_type(self, label: str) -> str:
        if label in {"SECTION_HEADER", "TITLE", "HEADING", "HEADER"}:
            return "heading"
        if label == "TABLE":
            return "table"
        if label in {"PICTURE", "FIGURE"}:
            return "figure"
        if label == "IMAGE":
            return "image"
        if label in {"CAPTION", "TEXT_CAPTION"}:
            return "caption"
        if label in {"CODE", "CODE_BLOCK"}:
            return "code"
        if label in {"LIST", "LIST_ITEM", "ORDERED_LIST", "UNORDERED_LIST"}:
            return "list"
        if label in {"PAGE_HEADER", "PAGE_TOP"}:
            return "page_header"
        if label in {"PAGE_FOOTER", "PAGE_BOTTOM"}:
            return "page_footer"
        if label in {"TEXT", "PARAGRAPH", "BODY_TEXT"}:
            return "paragraph"
        return "unknown"

    def _parent_section_id(
        self,
        *,
        sections_by_level: dict[int, str],
        level: int,
    ) -> str | None:
        parent_levels = [item for item in sections_by_level if item < level]
        if not parent_levels:
            return None
        return sections_by_level[max(parent_levels)]

    def _append_child_section_id(
        self,
        *,
        sections: list[DocumentSection],
        parent_section_id: str,
        child_section_id: str,
    ) -> list[DocumentSection]:
        updated: list[DocumentSection] = []
        for section in sections:
            if section.section_id != parent_section_id:
                updated.append(section)
                continue
            child_ids = list(section.child_section_ids)
            if child_section_id not in child_ids:
                child_ids.append(child_section_id)
            updated.append(section.model_copy(update={"child_section_ids": child_ids}))
        return updated

    def _item_text(self, *, item: Any, doc: Any) -> str:
        if hasattr(item, "export_to_markdown"):
            try:
                return str(item.export_to_markdown(doc=doc)).strip()
            except TypeError:
                return str(item.export_to_markdown()).strip()
        if hasattr(item, "caption_text"):
            caption = str(item.caption_text(doc=doc)).strip()
            if caption:
                return caption
        return str(getattr(item, "text", "") or "").strip()

    def _page_number(self, item: Any) -> int | None:
        prov = getattr(item, "prov", None) or []
        if not prov:
            return None
        page_no = getattr(prov[0], "page_no", None)
        return int(page_no) if page_no is not None else None

    def _bbox(self, item: Any) -> dict | None:
        prov = getattr(item, "prov", None) or []
        if not prov:
            return None
        bbox = getattr(prov[0], "bbox", None)
        if bbox is None:
            return None
        if hasattr(bbox, "model_dump"):
            return bbox.model_dump()
        if hasattr(bbox, "as_tuple"):
            return {"tuple": list(bbox.as_tuple())}
        return None

    def _asset_payload(
        self,
        *,
        document_id: str,
        item: Any,
        doc: Any,
        block_id: str,
        section_id: str | None,
        page_number: int,
        index: int,
        asset_type: str,
        nearby_text: str | None,
    ) -> DoclingAssetPayload | None:
        image = self._item_image(item=item, doc=doc)
        if image is None:
            return None
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        asset_id = f"{document_id}-asset-{index}"
        caption = self._caption_text(item=item, doc=doc)
        return DoclingAssetPayload(
            asset_id=asset_id,
            filename=f"{asset_id}.png",
            bytes_data=buffer.getvalue(),
            asset_type=asset_type,
            mime_type="image/png",
            page_number=page_number,
            section_id=section_id,
            block_id=block_id,
            caption=caption or None,
            nearby_text=nearby_text,
        )

    def _item_image(self, *, item: Any, doc: Any) -> Any | None:
        image_ref = getattr(item, "image", None)
        image = getattr(image_ref, "pil_image", None)
        if image is not None:
            return image
        if hasattr(item, "get_image"):
            try:
                return item.get_image(doc=doc)
            except TypeError:
                return item.get_image()
        if hasattr(image_ref, "save"):
            return image_ref
        return None

    def _caption_text(self, *, item: Any, doc: Any) -> str:
        if not hasattr(item, "caption_text"):
            return ""
        try:
            return str(item.caption_text(doc=doc)).strip()
        except TypeError:
            return str(item.caption_text()).strip()

    def _pages(self, *, doc: Any, page_text: dict[int, list[str]]) -> list[DocumentPage]:
        pages = getattr(doc, "pages", None) or {}
        if isinstance(pages, dict) and pages:
            page_numbers = sorted(int(page_no) for page_no in pages)
            return [
                DocumentPage(
                    page_number=page_number,
                    width=self._page_dimension(pages[page_number], "width"),
                    height=self._page_dimension(pages[page_number], "height"),
                    text="\n".join(page_text.get(page_number, [])),
                )
                for page_number in page_numbers
            ]
        return [
            DocumentPage(page_number=page_number, text="\n".join(text))
            for page_number, text in sorted(page_text.items())
        ]

    def _page_dimension(self, page: Any, name: str) -> float | None:
        size = getattr(page, "size", None)
        value = getattr(size, name, None)
        return float(value) if value is not None else None

    def _docling_version(self) -> str | None:
        try:
            docling = import_module("docling")
        except ImportError:
            return None
        return getattr(docling, "__version__", None)
