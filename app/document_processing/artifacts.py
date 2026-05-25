import json
from dataclasses import asdict
from pathlib import Path

from app.document_processing.models import DocumentStructure
from app.document_processing.refinement import TocRefinementResult
from app.document_processing.storage_paths import DocumentStoragePaths


class DocumentProcessingArtifactStore:
    def __init__(self, *, storage_paths: DocumentStoragePaths | None = None):
        self.storage_paths = storage_paths or DocumentStoragePaths()

    def save_structure(self, structure: DocumentStructure) -> Path:
        path = self.storage_paths.manifest_path(
            document_id=structure.document_id,
            filename="document_structure.json",
        )
        self._write_json(path, structure.model_dump(mode="json"))
        return path

    def save_toc_refinement_report(
        self,
        *,
        document_id: str,
        enabled: bool,
        result: TocRefinementResult,
    ) -> Path:
        path = self.storage_paths.manifest_path(
            document_id=document_id,
            filename="toc_refinement_report.json",
        )
        payload = asdict(result)
        payload["enabled"] = enabled
        payload["structure"] = result.structure.model_dump(mode="json")
        self._write_json(path, payload)
        return path

    def _write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(f"{path.suffix}.tmp")
        tmp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(path)
