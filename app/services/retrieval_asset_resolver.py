from app.domain.models import Evidence
from app.schemas.retrieval import AssetResponse
from app.services.asset_urls import document_asset_thumbnail_url, document_asset_url
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.document_processing.models import DocumentAsset, DocumentStructure, SourceChunk


class RetrievalAssetResolver:
    def __init__(self, repository: DocumentProcessingRepository):
        self.repository = repository

    def resolve(
        self,
        evidence: list[Evidence],
        *,
        query: str = "",
        include_thumbnails: bool,
        max_assets: int,
    ) -> list[AssetResponse]:
        if max_assets <= 0:
            return []

        ranked_assets: list[tuple[tuple[int, int, str], DocumentAsset]] = []
        structures: dict[str, DocumentStructure | None] = {}
        for evidence_index, item in enumerate(evidence):
            document_id = str(item.document_id)
            if document_id not in structures:
                structures[document_id] = self.repository.get_structure(document_id)
            structure = structures[document_id]
            if structure is None:
                continue
            chunk = self._source_chunk_for_evidence(item=item, structure=structure)
            for asset in structure.assets:
                score = self._asset_score(
                    asset=asset,
                    chunk=chunk,
                    evidence=item,
                    query=query,
                )
                if score is None:
                    continue
                ranked_assets.append(((score, evidence_index, asset.asset_id), asset))

        responses: list[AssetResponse] = []
        seen: set[str] = set()
        for _, asset in sorted(ranked_assets, key=lambda item: item[0]):
            if asset.asset_id in seen:
                continue
            seen.add(asset.asset_id)
            responses.append(
                AssetResponse(
                    asset_id=asset.asset_id,
                    document_id=asset.document_id,
                    asset_type=asset.asset_type,
                    caption=asset.caption,
                    page_number=asset.page_number,
                    url=document_asset_url(asset.document_id, asset.asset_id),
                    thumbnail_url=document_asset_thumbnail_url(
                        asset.document_id,
                        asset.asset_id,
                        has_thumbnail=include_thumbnails and bool(asset.thumbnail_path),
                    ),
                )
            )
            if len(responses) >= max_assets:
                break
        return responses

    def _source_chunk_for_evidence(
        self,
        *,
        item: Evidence,
        structure: DocumentStructure,
    ) -> SourceChunk | None:
        source_chunk_id = str(
            item.metadata.get("source_chunk_id")
            or item.metadata.get("chunk_id")
            or item.id
        )
        return next((chunk for chunk in structure.source_chunks if chunk.chunk_id == source_chunk_id), None)

    def _asset_score(
        self,
        *,
        asset: DocumentAsset,
        chunk: SourceChunk | None,
        evidence: Evidence,
        query: str,
    ) -> int | None:
        metadata_asset_ids = evidence.metadata.get("asset_ids")
        if not isinstance(metadata_asset_ids, list):
            metadata_asset_ids = []
        if asset.asset_id in metadata_asset_ids:
            return metadata_asset_ids.index(asset.asset_id)
        if chunk and (asset.chunk_id == chunk.chunk_id or asset.asset_id in chunk.asset_ids):
            return 0
        if chunk and asset.block_id and asset.block_id in chunk.block_ids:
            return 1
        if self._caption_overlaps_query(asset=asset, query=query):
            return 2
        if self._same_page(asset=asset, chunk=chunk, evidence=evidence):
            return 3
        if chunk and asset.section_id and asset.section_id == chunk.section_id:
            return 4
        if self._near_page_range(asset=asset, chunk=chunk, evidence=evidence):
            return 5
        return None

    def _caption_overlaps_query(self, *, asset: DocumentAsset, query: str) -> bool:
        if not asset.caption or not query:
            return False
        caption_terms = self._terms(asset.caption)
        query_terms = self._terms(query)
        return bool(caption_terms & query_terms)

    def _terms(self, value: str) -> set[str]:
        return {term for term in value.lower().replace(".", " ").split() if len(term) > 2}

    def _same_page(
        self,
        *,
        asset: DocumentAsset,
        chunk: SourceChunk | None,
        evidence: Evidence,
    ) -> bool:
        if asset.page_number is None:
            return False
        page_start = chunk.page_start if chunk else None
        page_end = chunk.page_end if chunk else None
        if evidence.page_ref:
            page_start = page_start or evidence.page_ref.page_start
            page_end = page_end or evidence.page_ref.page_end
        return page_start is not None and page_start <= asset.page_number <= (page_end or page_start)

    def _near_page_range(
        self,
        *,
        asset: DocumentAsset,
        chunk: SourceChunk | None,
        evidence: Evidence,
    ) -> bool:
        if asset.page_number is None:
            return False
        page_start = chunk.page_start if chunk else None
        page_end = chunk.page_end if chunk else None
        if evidence.page_ref:
            page_start = page_start or evidence.page_ref.page_start
            page_end = page_end or evidence.page_ref.page_end
        if page_start is None:
            return False
        page_end = page_end or page_start
        return page_start - 1 <= asset.page_number <= page_end + 1
