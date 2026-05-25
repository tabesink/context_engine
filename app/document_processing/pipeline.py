from pathlib import Path

from app.document_processing.models import (
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
    SourceChunk,
    StructureQuality,
)


class TextDoclingParser:
    """Lightweight parser adapter used until the real Docling dependency is wired in."""

    def parse(self, *, document_id: str, source_path: Path) -> DocumentStructure:
        text = source_path.read_text(encoding="utf-8")
        id_prefix = document_id
        sections: list[DocumentSection] = []
        blocks: list[DocumentBlock] = []
        chunks: list[SourceChunk] = []
        current_section_id: str | None = None
        current_title = "Document"
        block_index = 0

        for line in [item.strip() for item in text.splitlines() if item.strip()]:
            if line.startswith("#"):
                section_id = f"{id_prefix}-sec-{len(sections) + 1}"
                current_section_id = section_id
                current_title = line.lstrip("#").strip() or current_title
                sections.append(
                    DocumentSection(
                        section_id=section_id,
                        document_id=document_id,
                        title=current_title,
                        level=1,
                        page_start=1,
                        page_end=1,
                    )
                )
                continue

            block_index += 1
            block_id = f"{id_prefix}-block-{block_index}"
            chunk_id = f"{id_prefix}-source-chunk-{block_index}"
            block = DocumentBlock(
                block_id=block_id,
                document_id=document_id,
                section_id=current_section_id,
                type="paragraph",
                text=line,
                page_start=1,
                page_end=1,
            )
            blocks.append(block)
            chunks.append(
                SourceChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    section_id=current_section_id,
                    block_ids=[block_id],
                    text=line,
                    page_start=1,
                    page_end=1,
                )
            )
            if current_section_id:
                section = sections[-1]
                section.block_ids.append(block_id)

        page_text = "\n".join([section.title for section in sections] + [block.text for block in blocks])
        return DocumentStructure(
            document_id=document_id,
            source_file=str(source_path),
            pages=[DocumentPage(page_number=1, text=page_text)],
            sections=sections,
            blocks=blocks,
            source_chunks=chunks,
            quality=StructureQuality(
                heading_count=len(sections),
                section_count=len(sections),
                block_count=len(blocks),
                score=1.0 if sections else 0.5,
            ),
        )

