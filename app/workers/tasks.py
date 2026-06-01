from app.domain.models import JobStatus
from app.services.document_ingestion_status_service import DocumentIngestionStatusService
from app.services.lightrag_ingestion_service import DomainIngestBusy, LightRAGIngestionService
from app.services.document_service import DocumentService
from app.storage.db import SessionLocal
from app.storage.repositories.jobs import JobRepository


def run_document_ingest_job(job_id: str) -> None:
    with SessionLocal() as session:
        jobs = JobRepository(session)
        job = jobs.get(job_id)
        if not job or not job.document_id:
            return

        status = DocumentIngestionStatusService(session)
        status.mark_running(
            document_id=job.document_id,
            operation_id=job.id,
            stage="parse_local_structure",
            message="Parsing local document structure",
        )
        try:
            remote_status = LightRAGIngestionService(session).ingest_document(job.document_id)
            if remote_status == "indexing":
                status.mark_waiting_remote(
                    document_id=job.document_id,
                    operation_id=job.id,
                    message="Waiting for LightRAG to finish indexing",
                )
            else:
                status.mark_succeeded(document_id=job.document_id, operation_id=job.id)
        except DomainIngestBusy as exc:
            jobs.set_status(
                job,
                JobStatus.QUEUED,
                stage="register_upload",
                message=str(exc),
                error_message=str(exc),
            )
            raise
        except Exception as exc:
            status.mark_failed(
                document_id=job.document_id,
                operation_id=job.id,
                error_message=str(exc),
            )
            raise


def poll_lightrag_statuses() -> None:
    with SessionLocal() as session:
        DocumentService(session).refresh_pending_lightrag_statuses()


