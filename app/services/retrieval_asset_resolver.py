from app.domain.models import Evidence
from app.schemas.query import AssetResponse
from app.storage.repositories.document_processing import DocumentProcessingRepository


class RetrievalAssetResolver:
    def __init__(self, repository: DocumentProcessingRepository):
        self.repository = repository

    def resolve(
        self,
        evidence: list[Evidence],
        *,
        include_thumbnails: bool,
        max_assets: int,
    ) -> list[AssetResponse]:
        if max_assets <= 0:
            return []

        chunk_ids: list[str] = []
        for item in evidence:
            source_chunk_id = str(item.metadata.get("source_chunk_id") or item.id)
            chunk = self.repository.get_source_chunk(str(item.document_id), source_chunk_id)
            if chunk and chunk.chunk_id not in chunk_ids:
                chunk_ids.append(chunk.chunk_id)

        responses: list[AssetResponse] = []
        seen: set[str] = set()
        for asset in self.repository.list_assets_for_chunks(chunk_ids):
            if asset.asset_id in seen:
                continue
            seen.add(asset.asset_id)
            thumbnail_url = None
            if include_thumbnails and asset.thumbnail_path:
                thumbnail_url = f"/documents/{asset.document_id}/assets/{asset.asset_id}/thumbnail"
            responses.append(
                AssetResponse(
                    asset_id=asset.asset_id,
                    document_id=asset.document_id,
                    asset_type=asset.asset_type,
                    caption=asset.caption,
                    page_number=asset.page_number,
                    url=f"/documents/{asset.document_id}/assets/{asset.asset_id}",
                    thumbnail_url=thumbnail_url,
                )
            )
            if len(responses) >= max_assets:
                break
        return responses
