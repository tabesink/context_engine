from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.domain.models import DocumentStatus, JobStatus
from app.integrations.lightrag_remote_adapter import LightRAGAdapterError, LightRAGRemoteAdapter
from app.schemas.processing_status import (
    ActiveProcessingOperation,
    DocumentProcessingStatusItem,
    DocumentProcessingStatusResponse,
    DomainProcessingStatusResponse,
    LightRAGPipelineStatus,
    ProcessingStatusListResponse,
    ProcessingStatusPagination,
    ProcessingCounts,
    ProcessingStatusError,
)
from app.services.document_access_policy import DocumentAccessPolicy
from app.services.lightrag_domain_registry import LightRAGDomainRegistry
from app.services.processing_status_cache import processing_status_cache
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.jobs import JobRepository
from app.storage.tables import DocumentRow, UserRow


class ProcessingStatusService:
    def __init__(self, session: Session):
        self.session = session
        self.documents = DocumentRepository(session)
        self.jobs = JobRepository(session)
        self.domain_registry = LightRAGDomainRegistry()

    def get_domain_status(self, *, domain_id: str, admin: bool) -> DomainProcessingStatusResponse:
        self.domain_registry.validate_available(domain_id)
        docs = self.documents.list_all_by_lightrag_domain(domain_id)
        latest_jobs = self.jobs.list_latest_by_document_ids([doc.id for doc in docs])
        jobs_by_document = {job.document_id: job for job in latest_jobs if job.document_id}
        items = [self._to_document_item(doc, jobs_by_document.get(doc.id)) for doc in docs]
        local_counts = self._counts(items)

        remote_snapshot, is_stale, errors = self._remote_snapshot(domain_id=domain_id)
        counts = self._merge_counts(local_counts, remote_snapshot)
        active = self._active_operation(remote_snapshot, counts)
        state = self._domain_state(counts=counts, remote_snapshot=remote_snapshot, errors=errors)

        response = DomainProcessingStatusResponse(
            domain_id=domain_id,
            state=state,
            is_busy=state in {"busy", "queued"},
            is_stale=is_stale,
            updated_at=datetime.now(UTC),
            counts=counts,
            active=active,
            documents=items if admin else [],
            lightrag=self._to_lightrag_payload(remote_snapshot) if admin else None,
            errors=errors,
        )
        return response

    def get_admin_document_status(self, *, document_id: str) -> DocumentProcessingStatusResponse:
        document = self.documents.get(document_id)
        if document is None:
            raise not_found("Document not found")
        item = self._document_with_latest_job(document)
        domain_id = self._document_domain(document)
        domain = self.get_domain_status(domain_id=domain_id, admin=True) if domain_id else None
        return DocumentProcessingStatusResponse(document=item, domain=domain)

    def get_user_document_status(self, *, document_id: str, user: UserRow) -> DocumentProcessingStatusResponse:
        document = DocumentAccessPolicy(self.documents).get_readable_document_or_404(
            user=user,
            document_id=document_id,
        )
        item = self._document_with_latest_job(document)
        domain_id = self._document_domain(document)
        domain = self.get_domain_status(domain_id=domain_id, admin=False) if domain_id else None
        return DocumentProcessingStatusResponse(document=item, domain=domain)

    def get_admin_domain_documents_status(
        self,
        *,
        domain_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> ProcessingStatusListResponse:
        self.domain_registry.validate_available(domain_id)
        docs = self.documents.list_all_by_lightrag_domain(domain_id)
        paged_docs = docs[offset : offset + limit]
        latest_jobs = self.jobs.list_latest_by_document_ids([doc.id for doc in paged_docs])
        jobs_by_document = {job.document_id: job for job in latest_jobs if job.document_id}
        items = [self._to_document_item(doc, jobs_by_document.get(doc.id)) for doc in paged_docs]
        counts = self._counts(items)
        return ProcessingStatusListResponse(
            domain_id=domain_id,
            documents=items,
            status_counts=counts,
            pagination=ProcessingStatusPagination(
                limit=limit,
                offset=offset,
                returned=len(items),
                total=len(docs),
            ),
            updated_at=datetime.now(UTC),
        )

    def _document_with_latest_job(self, document: DocumentRow) -> DocumentProcessingStatusItem:
        latest = self.jobs.list_latest_by_document_ids([document.id])
        job = latest[0] if latest else None
        return self._to_document_item(document, job)

    def _to_document_item(self, document: DocumentRow, job) -> DocumentProcessingStatusItem:
        lightrag = document.meta.get("lightrag", {}) if isinstance(document.meta, dict) else {}
        lightrag_status_raw = lightrag.get("status")
        mapped = self._map_document_state(
            document_status=document.status,
            job_status=job.status if job else None,
            lightrag_status=lightrag_status_raw,
        )
        return DocumentProcessingStatusItem(
            document_id=document.id,
            filename=document.filename,
            status=mapped,
            domain_id=self._document_domain(document),
            job_id=job.id if job else None,
            job_status=job.status if job else None,
            lightrag_status=str(lightrag_status_raw) if lightrag_status_raw is not None else None,
            message=document.error_message or lightrag.get("message"),
            can_retry=bool(job and job.kind == "document_ingest" and job.status == JobStatus.FAILED.value),
            updated_at=document.updated_at,
        )

    def _document_domain(self, document: DocumentRow) -> str | None:
        if document.lightrag_domain_id:
            return document.lightrag_domain_id
        lightrag = document.meta.get("lightrag", {}) if isinstance(document.meta, dict) else {}
        value = lightrag.get("domain_id") or lightrag.get("domain")
        return str(value) if value else None

    def _map_document_state(self, *, document_status: str, job_status: str | None, lightrag_status: Any) -> str:
        raw = str(lightrag_status or "").lower()
        if raw in {"pending", "queued"}:
            return "queued"
        if raw in {"processing", "parsing", "analyzing", "preprocessed", "indexing"}:
            return "indexing"
        if raw in {"processed", "ready", "complete", "completed", "success"}:
            return "ready"
        if raw in {"failed", "failure", "error"}:
            return "failed"

        if job_status == JobStatus.QUEUED.value:
            return "queued"
        if job_status == JobStatus.RUNNING.value:
            return "indexing"
        if job_status == JobStatus.FAILED.value:
            return "failed"

        mapped = {
            DocumentStatus.UPLOADED.value: "uploaded",
            DocumentStatus.INDEXING.value: "indexing",
            DocumentStatus.READY.value: "ready",
            DocumentStatus.FAILED.value: "failed",
            DocumentStatus.DELETED.value: "deleted",
        }
        return mapped.get(document_status, "unknown")

    def _counts(self, items: list[DocumentProcessingStatusItem]) -> ProcessingCounts:
        counts = ProcessingCounts()
        for item in items:
            if item.status in {"uploaded", "queued"}:
                counts.queued += 1
            elif item.status == "indexing":
                counts.indexing += 1
            elif item.status == "ready":
                counts.ready += 1
            elif item.status == "failed":
                counts.failed += 1
            elif item.status == "deleted":
                counts.deleted += 1
            else:
                counts.unknown += 1
        return counts

    def _remote_snapshot(self, *, domain_id: str) -> tuple[dict[str, Any] | None, bool, list[ProcessingStatusError]]:
        cache_key = f"processing-status:remote:{domain_id}"
        cached = processing_status_cache.get(cache_key)
        if cached is not None:
            return cached, False, []

        adapter = LightRAGRemoteAdapter.for_domain(domain_id)
        errors: list[ProcessingStatusError] = []
        try:
            pipeline = adapter.pipeline_status()
            counts = adapter.status_counts()
            snapshot = {"pipeline": pipeline, "counts": counts}
            ttl = 3 if bool(pipeline.get("busy")) else 20
            processing_status_cache.set(cache_key, snapshot, ttl_seconds=ttl)
            return snapshot, False, []
        except LightRAGAdapterError as exc:
            errors.append(
                ProcessingStatusError(
                    code="domain_unreachable",
                    source="lightrag",
                    message=str(exc),
                )
            )
            return None, True, errors

    def _merge_counts(
        self,
        local_counts: ProcessingCounts,
        remote_snapshot: dict[str, Any] | None,
    ) -> ProcessingCounts:
        if remote_snapshot is None:
            return local_counts
        payload = remote_snapshot.get("counts", {})
        status_counts = payload.get("status_counts", {}) if isinstance(payload, dict) else {}
        if not isinstance(status_counts, dict):
            return local_counts

        merged = ProcessingCounts(
            queued=int(status_counts.get("pending", 0)) + int(status_counts.get("queued", 0)),
            indexing=int(status_counts.get("processing", 0)) + int(status_counts.get("indexing", 0)),
            ready=int(status_counts.get("processed", 0)) + int(status_counts.get("ready", 0)),
            failed=int(status_counts.get("failed", 0)) + int(status_counts.get("error", 0)),
            deleted=int(status_counts.get("deleted", 0)),
            unknown=int(status_counts.get("unknown", 0)),
        )
        if merged.queued + merged.indexing + merged.ready + merged.failed + merged.deleted + merged.unknown == 0:
            return local_counts
        return merged

    def _active_operation(
        self,
        remote_snapshot: dict[str, Any] | None,
        counts: ProcessingCounts,
    ) -> ActiveProcessingOperation | None:
        if remote_snapshot is None:
            if counts.queued or counts.indexing:
                return ActiveProcessingOperation(label="Indexing documents")
            return None
        pipeline = remote_snapshot.get("pipeline", {})
        if not isinstance(pipeline, dict):
            return None
        if not pipeline.get("busy") and not (counts.queued or counts.indexing):
            return None

        total = None
        current = None
        docs = pipeline.get("docs")
        cur_batch = pipeline.get("cur_batch")
        if isinstance(docs, int):
            total = docs
        if isinstance(cur_batch, int):
            current = cur_batch

        return ActiveProcessingOperation(
            label=str(pipeline.get("job_name") or "Indexing documents"),
            current=current,
            total=total,
            message=str(pipeline.get("latest_message") or "") or None,
            started_at=self._parse_datetime(pipeline.get("job_start")),
        )

    def _to_lightrag_payload(self, remote_snapshot: dict[str, Any] | None) -> LightRAGPipelineStatus | None:
        if remote_snapshot is None:
            return LightRAGPipelineStatus(reachable=False)
        pipeline = remote_snapshot.get("pipeline", {})
        if not isinstance(pipeline, dict):
            return LightRAGPipelineStatus(reachable=False)
        history = pipeline.get("history_messages")
        history_tail = history[-5:] if isinstance(history, list) else []
        return LightRAGPipelineStatus(
            reachable=True,
            pipeline_busy=bool(pipeline.get("busy")),
            job_name=str(pipeline.get("job_name") or "") or None,
            job_start=self._parse_datetime(pipeline.get("job_start")),
            latest_message=str(pipeline.get("latest_message") or "") or None,
            history_tail=[str(item) for item in history_tail],
            update_status=pipeline.get("update_status") if isinstance(pipeline.get("update_status"), dict) else {},
        )

    def _domain_state(
        self,
        *,
        counts: ProcessingCounts,
        remote_snapshot: dict[str, Any] | None,
        errors: list[ProcessingStatusError],
    ) -> str:
        pipeline_busy = False
        if remote_snapshot and isinstance(remote_snapshot.get("pipeline"), dict):
            pipeline_busy = bool(remote_snapshot["pipeline"].get("busy"))

        if errors and not (counts.queued or counts.indexing):
            return "unreachable"
        if pipeline_busy or counts.indexing:
            return "busy"
        if counts.queued:
            return "queued"
        if counts.failed and not (counts.queued or counts.indexing):
            return "partial_failure"
        if counts.ready or counts.deleted:
            return "idle"
        return "unknown"

    def _parse_datetime(self, value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            candidate = value.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(candidate)
            except ValueError:
                return None
        return None
