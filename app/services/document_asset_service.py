from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.core.errors import not_found
from app.storage.repositories.document_processing import DocumentProcessingRepository


@dataclass(frozen=True)
class DocumentAssetFile:
    path: Path
    media_type: str
    filename: str


class DocumentAssetService:
    def __init__(
        self,
        *,
        access_policy,
        assets: DocumentProcessingRepository,
        storage_root: Path | None = None,
    ):
        self.access_policy = access_policy
        self.assets = assets
        self.storage_root = storage_root or get_settings().storage_root

    def get_asset_file(
        self,
        *,
        user,
        document_id: str,
        asset_id: str,
        thumbnail: bool = False,
    ) -> DocumentAssetFile:
        self.access_policy.get_readable_document_or_404(user=user, document_id=document_id)
        asset = self.assets.get_asset(document_id, asset_id)
        if not asset:
            raise not_found("Document asset not found")

        raw_path = asset.thumbnail_path if thumbnail else asset.storage_path
        if not raw_path:
            raise not_found("Document asset not found")

        path = self._resolve_asset_path(raw_path=raw_path, document_id=document_id)
        if not path.is_file():
            raise FileNotFoundError(f"Document asset file not found: {path}")

        return DocumentAssetFile(
            path=path,
            media_type=asset.mime_type,
            filename=path.name,
        )

    def _resolve_asset_path(self, *, raw_path: str, document_id: str) -> Path:
        storage_root = self.storage_root.resolve()
        path = Path(raw_path)
        candidate = path if path.is_absolute() else storage_root / path
        resolved = candidate.resolve()
        document_root = (storage_root / "documents" / document_id).resolve()
        if not resolved.is_relative_to(document_root):
            raise not_found("Document asset not found")
        return resolved
