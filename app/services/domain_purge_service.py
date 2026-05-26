import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.document_processing.storage_paths import DocumentStoragePaths
from app.domain.models import JobStatus
from app.lightrag_deploy.errors import DomainNotFoundError, PermanentDeleteDisabledError
from app.lightrag_deploy.models import LightRAGDomainPurgePreview, LightRAGDomainPurgeResult
from app.lightrag_deploy.service import LightRAGDomainService
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.jobs import JobRepository
from app.storage.repositories.lightrag_domain_lifecycle import LightRAGDomainLifecycleRepository
from app.storage.repositories.logs import LogRepository


class DomainPurgeService:
    def __init__(
        self,
        session: Session,
        *,
        settings: Settings | None = None,
        domain_service: LightRAGDomainService | None = None,
    ):
        self.session = session
        self.settings = settings or get_settings()
        self.documents = DocumentRepository(session)
        self.processing = DocumentProcessingRepository(session)
        self.jobs = JobRepository(session)
        self.lifecycle = LightRAGDomainLifecycleRepository(session)
        self.logs = LogRepository(session)
        self.domain_service = domain_service or LightRAGDomainService()
        self.storage_root = self.settings.storage_root.resolve()
        self.storage_paths = DocumentStoragePaths(storage_root=self.storage_root)

    def preview_lightrag_domain_purge(self, domain_id: str) -> LightRAGDomainPurgePreview:
        self.domain_service.get_domain(domain_id)
        documents = self.documents.list_all_by_lightrag_domain(domain_id)
        document_ids = [document.id for document in documents]
        processing_counts = self.processing.count_by_document_ids(document_ids)

        estimated_bytes = 0
        upload_count = 0
        for document in documents:
            upload_file = self._resolve_upload_path(document.storage_path)
            if upload_file and upload_file.is_file():
                upload_count += 1
                estimated_bytes += upload_file.stat().st_size
            artifact_root = self.storage_paths.document_root(document.id)
            if artifact_root.exists():
                estimated_bytes += self._path_size(artifact_root)

        return LightRAGDomainPurgePreview(
            domain_id=domain_id,
            documents=len(documents),
            original_uploads=upload_count,
            assets=processing_counts["assets"],
            chunks=processing_counts["chunks"],
            pages=processing_counts["pages"],
            sections=processing_counts["sections"],
            blocks=processing_counts["blocks"],
            estimated_bytes=estimated_bytes,
            will_delete=[
                "LightRAG domain root",
                "Context Engine uploaded originals",
                "Context Engine extracted images/tables/thumbnails",
                "document navigation rows",
                "asset rows",
            ],
        )

    def purge_lightrag_domain(
        self,
        *,
        domain_id: str,
        actor_id: str,
        confirm_domain_id: str,
    ) -> LightRAGDomainPurgeResult:
        if confirm_domain_id != domain_id:
            raise ValueError("confirm_domain_id must match domain_id")
        if not self.settings.lightrag_allow_permanent_delete:
            raise PermanentDeleteDisabledError("Permanent LightRAG domain delete is disabled")

        try:
            self.domain_service.get_domain(domain_id)
        except DomainNotFoundError:
            raise

        preview = self.preview_lightrag_domain_purge(domain_id)
        self.lifecycle.set_state(
            domain_id=domain_id,
            state="purging",
            metadata={"preview": preview.model_dump()},
        )
        self.logs.record_audit(
            actor_id=actor_id,
            event="lightrag.domain.purge_started",
            target_id=domain_id,
            metadata=preview.model_dump(),
        )

        try:
            documents = self.documents.list_all_by_lightrag_domain(domain_id)
            document_ids = [document.id for document in documents]
            canceled_jobs = self._cancel_jobs(document_ids)
            purged_original_uploads, purged_artifact_roots = self._delete_document_files(documents)
            purged_processing_rows = self.processing.delete_by_document_ids(document_ids)
            cleared_job_document_references = self.jobs.clear_document_references(document_ids)
            purged_documents = self.documents.hard_delete_by_ids(document_ids)
            deleted_domain_archive = self._delete_archived_domain_roots(domain_id)
            remove_result = self.domain_service.remove(domain_id, permanent=True)
            deleted_domain_archive = deleted_domain_archive or bool(remove_result.archive_path)
            self.lifecycle.set_state(domain_id=domain_id, state="purged")
            result = LightRAGDomainPurgeResult(
                domain_id=domain_id,
                state="purged",
                purged_documents=purged_documents,
                purged_original_uploads=purged_original_uploads,
                purged_artifact_roots=purged_artifact_roots,
                purged_processing_rows=purged_processing_rows,
                canceled_jobs=canceled_jobs,
                cleared_job_document_references=cleared_job_document_references,
                deleted_domain_root=True,
                deleted_domain_archive=deleted_domain_archive,
            )
            self.logs.record_audit(
                actor_id=actor_id,
                event="lightrag.domain.purged",
                target_id=domain_id,
                metadata=result.model_dump(),
            )
            return result
        except Exception as exc:
            self.lifecycle.set_state(
                domain_id=domain_id,
                state="failed",
                error_message=str(exc),
                metadata={"operation": "purge"},
            )
            raise

    def _cancel_jobs(self, document_ids: list[str]) -> int:
        canceled = 0
        for job in self.jobs.list_by_document_ids(document_ids):
            if job.status in {"queued", "running"}:
                self.jobs.set_status(job, status=JobStatus.CANCELED)
                canceled += 1
        return canceled

    def _resolve_upload_path(self, raw_path: str) -> Path | None:
        candidate = Path(raw_path)
        resolved = candidate if candidate.is_absolute() else candidate.resolve()
        resolved = resolved.resolve()
        if not resolved.is_relative_to(self.storage_root):
            return None
        return resolved

    def _delete_document_files(self, documents: list) -> tuple[int, int]:
        deleted_uploads = 0
        deleted_artifacts = 0
        for document in documents:
            upload_file = self._resolve_upload_path(document.storage_path)
            if upload_file and upload_file.exists():
                upload_file.unlink(missing_ok=True)
                deleted_uploads += 1
            artifact_root = self.storage_paths.document_root(document.id)
            if artifact_root.exists():
                shutil.rmtree(artifact_root, ignore_errors=True)
                deleted_artifacts += 1
        return deleted_uploads, deleted_artifacts

    def _delete_archived_domain_roots(self, domain_id: str) -> bool:
        deleted_root = self.settings.lightrag_deleted_root
        if not deleted_root.exists():
            return False
        removed = False
        for path in deleted_root.glob(f"{domain_id}-*"):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                removed = True
        return removed

    def _path_size(self, path: Path) -> int:
        if path.is_file():
            return path.stat().st_size
        if not path.is_dir():
            return 0
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
