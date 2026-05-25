from collections import defaultdict

from app.document_processing.models import DocumentAsset, DocumentBlock, DocumentStructure, SourceChunk


class StructureAwareChunkBuilder:
    def __init__(self, *, max_chars: int = 1800):
        self.max_chars = max_chars

    def build(self, structure: DocumentStructure) -> DocumentStructure:
        chunks: list[SourceChunk] = []
        chunk_index = 1
        for section_id, blocks in self._ordered_block_groups(structure).items():
            pending: list[DocumentBlock] = []
            pending_chars = 0
            for block in blocks:
                block_text = block.text.strip()
                if not block_text and not block.asset_ids:
                    continue
                next_size = len(block_text)
                if pending and pending_chars + next_size > self.max_chars:
                    chunks.append(self._chunk(structure, section_id, pending, chunk_index))
                    chunk_index += 1
                    pending = []
                    pending_chars = 0
                pending.append(block)
                pending_chars += next_size
            if pending:
                chunks.append(self._chunk(structure, section_id, pending, chunk_index))
                chunk_index += 1

        assets = self._assign_assets_to_chunks(structure.assets, chunks)
        return structure.model_copy(update={"source_chunks": chunks, "assets": assets})

    def _ordered_block_groups(self, structure: DocumentStructure) -> dict[str | None, list[DocumentBlock]]:
        section_order = [section.section_id for section in structure.sections]
        groups: dict[str | None, list[DocumentBlock]] = {section_id: [] for section_id in section_order}
        groups.setdefault(None, [])
        sorted_blocks = sorted(
            structure.blocks,
            key=lambda block: (
                block.page_start or 0,
                block.reading_order if block.reading_order is not None else 10**9,
                block.block_id,
            ),
        )
        for block in sorted_blocks:
            groups.setdefault(block.section_id, []).append(block)

        ordered: dict[str | None, list[DocumentBlock]] = {}
        for section_id in section_order:
            if groups.get(section_id):
                ordered[section_id] = groups[section_id]
        if groups.get(None):
            ordered[None] = groups[None]
        for section_id, blocks in groups.items():
            if section_id not in ordered and blocks:
                ordered[section_id] = blocks
        return ordered

    def _chunk(
        self,
        structure: DocumentStructure,
        section_id: str | None,
        blocks: list[DocumentBlock],
        index: int,
    ) -> SourceChunk:
        block_ids = [block.block_id for block in blocks]
        page_starts = [block.page_start for block in blocks if block.page_start is not None]
        page_ends = [block.page_end for block in blocks if block.page_end is not None]
        asset_ids = self._asset_ids_for_blocks(structure.assets, blocks)
        metadata = {"semantic_owner": "lightrag"} | self._section_metadata(structure, section_id)
        text = self._chunk_text(
            structure=structure,
            blocks=blocks,
            asset_ids=asset_ids,
            section_path=metadata.get("section_path", []),
        )
        return SourceChunk(
            chunk_id=f"{structure.document_id}-source-chunk-{index}",
            document_id=structure.document_id,
            section_id=section_id,
            block_ids=block_ids,
            text=text,
            page_start=min(page_starts) if page_starts else None,
            page_end=max(page_ends) if page_ends else None,
            asset_ids=asset_ids,
            metadata=metadata,
        )

    def _chunk_text(
        self,
        *,
        structure: DocumentStructure,
        blocks: list[DocumentBlock],
        asset_ids: list[str],
        section_path: list[str],
    ) -> str:
        parts = [block.text.strip() for block in blocks if block.text.strip()]
        if not parts:
            captions = [
                asset.caption.strip()
                for asset in structure.assets
                if asset.asset_id in asset_ids and asset.caption
            ]
            parts.extend(captions)
        text = "\n\n".join(parts)
        if section_path:
            prefix = f"Section: {' > '.join(section_path)}"
            return f"{prefix}\n\n{text}" if text else prefix
        return text

    def _section_metadata(self, structure: DocumentStructure, section_id: str | None) -> dict:
        if section_id is None:
            return {}
        sections_by_id = {section.section_id: section for section in structure.sections}
        section = sections_by_id.get(section_id)
        if section is None:
            return {}
        path: list[str] = []
        visited: set[str] = set()
        current = section
        while current and current.section_id not in visited:
            visited.add(current.section_id)
            path.append(current.title)
            if current.parent_section_id is None:
                break
            current = sections_by_id.get(current.parent_section_id)
        path.reverse()
        return {
            "section_title": section.title,
            "section_path": path,
        }

    def _asset_ids_for_blocks(
        self,
        assets: list[DocumentAsset],
        blocks: list[DocumentBlock],
    ) -> list[str]:
        block_ids = {block.block_id for block in blocks}
        section_ids = {block.section_id for block in blocks if block.section_id}
        asset_ids: list[str] = []
        for block in blocks:
            for asset_id in block.asset_ids:
                if asset_id not in asset_ids:
                    asset_ids.append(asset_id)
        for asset in assets:
            if asset.asset_id in asset_ids:
                continue
            if asset.block_id in block_ids or (asset.section_id is not None and asset.section_id in section_ids):
                asset_ids.append(asset.asset_id)
        return asset_ids

    def _assign_assets_to_chunks(
        self,
        assets: list[DocumentAsset],
        chunks: list[SourceChunk],
    ) -> list[DocumentAsset]:
        chunk_by_asset_id: dict[str, str] = {}
        chunks_by_block_id: dict[str, str] = {}
        chunks_by_section_id: dict[str, list[str]] = defaultdict(list)
        for chunk in chunks:
            for asset_id in chunk.asset_ids:
                chunk_by_asset_id.setdefault(asset_id, chunk.chunk_id)
            for block_id in chunk.block_ids:
                chunks_by_block_id[block_id] = chunk.chunk_id
            if chunk.section_id:
                chunks_by_section_id[chunk.section_id].append(chunk.chunk_id)

        updated: list[DocumentAsset] = []
        for asset in assets:
            chunk_id = (
                chunk_by_asset_id.get(asset.asset_id)
                or (chunks_by_block_id.get(asset.block_id) if asset.block_id else None)
                or (
                    chunks_by_section_id[asset.section_id][0]
                    if asset.section_id and chunks_by_section_id.get(asset.section_id)
                    else None
                )
            )
            updated.append(asset.model_copy(update={"chunk_id": chunk_id or asset.chunk_id}))
        return updated
