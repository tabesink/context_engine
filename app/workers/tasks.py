from app.domain.models import JobStatus
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

        jobs.mark_operation_running(job)
        try:
            LightRAGIngestionService(session).ingest_document(job.document_id)
            jobs.mark_operation_succeeded(job)
        except DomainIngestBusy as exc:
            jobs.set_status(job, JobStatus.QUEUED, error_message=str(exc))
            raise
        except Exception as exc:
            jobs.mark_operation_failed(job, error_message=str(exc))
            raise


def poll_lightrag_statuses() -> None:
    with SessionLocal() as session:
        DocumentService(session).refresh_pending_lightrag_statuses()


