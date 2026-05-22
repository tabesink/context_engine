from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.document_processing.models import (
    DocumentAsset,
    DocumentBlock,
    DocumentSection,
    DocumentStructure,
    SourceChunk,
)
from app.storage.tables import (
    DocumentAssetRow,
    DocumentBlockRow,
    DocumentSectionRow,
    DocumentSourceChunkRow,
)


class DocumentProcessingRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_structure(self, structure: DocumentStructure) -> None:
        document_id = structure.document_id
        for table in (
            DocumentAssetRow,
            DocumentSourceChunkRow,
            DocumentBlockRow,
            DocumentSectionRow,
        ):
            self.session.execute(delete(table).where(table.document_id == document_id))

        for section in structure.sections:
            self.session.add(self._section_row(section))
        for block in structure.blocks:
            self.session.add(self._block_row(block))
        for chunk in structure.source_chunks:
            self.session.add(self._chunk_row(chunk))
        for asset in structure.assets:
            self.session.add(self._asset_row(asset))
        self.session.commit()

    def get_source_chunk(self, document_id: str, chunk_id: str) -> SourceChunk | None:
        row = self.session.get(DocumentSourceChunkRow, chunk_id)
        if not row or row.document_id != document_id:
            return None
        return self._chunk_model(row)

    def list_assets_for_chunks(self, chunk_ids: list[str]) -> list[DocumentAsset]:
        if not chunk_ids:
            return []
        rows = self.session.scalars(
            select(DocumentAssetRow).where(DocumentAssetRow.chunk_id.in_(chunk_ids))
        )
        return [self._asset_model(row) for row in rows]

    def get_asset(self, document_id: str, asset_id: str) -> DocumentAsset | None:
        row = self.session.get(DocumentAssetRow, asset_id)
        if not row or row.document_id != document_id:
            return None
        return self._asset_model(row)

    def _section_row(self, section: DocumentSection) -> DocumentSectionRow:
        return DocumentSectionRow(
            id=section.section_id,
            document_id=section.document_id,
            parent_section_id=section.parent_section_id,
            title=section.title,
            level=section.level,
            page_start=section.page_start,
            page_end=section.page_end,
            block_ids=section.block_ids,
            child_section_ids=section.child_section_ids,
            source=section.source,
            confidence=section.confidence,
        )

    def _block_row(self, block: DocumentBlock) -> DocumentBlockRow:
        return DocumentBlockRow(
            id=block.block_id,
            document_id=block.document_id,
            section_id=block.section_id,
            type=block.type,
            text=block.text,
            page_start=block.page_start,
            page_end=block.page_end,
            bbox=block.bbox,
            reading_order=block.reading_order,
            asset_ids=block.asset_ids,
        )

    def _chunk_row(self, chunk: SourceChunk) -> DocumentSourceChunkRow:
        return DocumentSourceChunkRow(
            id=chunk.chunk_id,
            document_id=chunk.document_id,
            section_id=chunk.section_id,
            block_ids=chunk.block_ids,
            text=chunk.text,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            asset_ids=chunk.asset_ids,
            meta=chunk.metadata,
        )

    def _asset_row(self, asset: DocumentAsset) -> DocumentAssetRow:
        return DocumentAssetRow(
            id=asset.asset_id,
            document_id=asset.document_id,
            section_id=asset.section_id,
            block_id=asset.block_id,
            chunk_id=asset.chunk_id,
            asset_type=asset.asset_type,
            storage_path=asset.storage_path,
            thumbnail_path=asset.thumbnail_path,
            mime_type=asset.mime_type,
            content_hash=asset.content_hash,
            page_number=asset.page_number,
            caption=asset.caption,
            nearby_text=asset.nearby_text,
            bbox=asset.bbox,
            generated_description=asset.generated_description,
            ocr_text=asset.ocr_text,
        )

    def _chunk_model(self, row: DocumentSourceChunkRow) -> SourceChunk:
        return SourceChunk(
            chunk_id=row.id,
            document_id=row.document_id,
            section_id=row.section_id,
            block_ids=row.block_ids,
            text=row.text,
            page_start=row.page_start,
            page_end=row.page_end,
            asset_ids=row.asset_ids,
            metadata=row.meta,
        )

    def _asset_model(self, row: DocumentAssetRow) -> DocumentAsset:
        return DocumentAsset(
            asset_id=row.id,
            document_id=row.document_id,
            section_id=row.section_id,
            block_id=row.block_id,
            chunk_id=row.chunk_id,
            asset_type=row.asset_type,
            storage_path=row.storage_path,
            thumbnail_path=row.thumbnail_path,
            mime_type=row.mime_type,
            content_hash=row.content_hash,
            page_number=row.page_number,
            caption=row.caption,
            nearby_text=row.nearby_text,
            bbox=row.bbox,
            generated_description=row.generated_description,
            ocr_text=row.ocr_text,
        )
