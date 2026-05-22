from pathlib import Path

from app.core.config import get_settings


class DocumentStoragePaths:
    def __init__(self, *, storage_root: Path | None = None):
        self.storage_root = storage_root or get_settings().storage_root

    def document_root(self, document_id: str) -> Path:
        return self.storage_root / "documents" / document_id

    def manifest_path(self, *, document_id: str, filename: str) -> Path:
        self._validate_filename(filename)
        return self._confined(self.document_root(document_id) / "manifest" / filename, document_id)

    def asset_path(self, *, document_id: str, filename: str) -> Path:
        self._validate_filename(filename)
        return self._confined(self.document_root(document_id) / "assets" / filename, document_id)

    def _validate_filename(self, filename: str) -> None:
        if Path(filename).name != filename:
            raise ValueError("Path must stay inside document storage")

    def _confined(self, path: Path, document_id: str) -> Path:
        root = self.document_root(document_id).resolve()
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            raise ValueError("Path must stay inside document storage")
        return resolved
