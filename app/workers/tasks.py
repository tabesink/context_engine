from app.domain.models import JobStatus
from app.services.lightrag_ingestion_service import DomainIngestBusy, LightRAGIngestionService
from app.services.indexing_service import IndexingService
from app.storage.db import SessionLocal
from app.storage.repositories.jobs import JobRepository


def index_document(document_id: str) -> None:
    with SessionLocal() as session:
        IndexingService(session).index_document(document_id)


def run_index_job(job_id: str) -> None:
    with SessionLocal() as session:
        jobs = JobRepository(session)
        job = jobs.get(job_id)
        if not job or not job.document_id:
            return

        jobs.set_status(job, JobStatus.RUNNING)
        try:
            IndexingService(session).index_document(job.document_id)
            jobs.set_status(job, JobStatus.SUCCEEDED)
        except Exception as exc:
            jobs.set_status(job, JobStatus.FAILED, error_message=str(exc))


def run_lightrag_ingest_job(job_id: str) -> None:
    with SessionLocal() as session:
        jobs = JobRepository(session)
        job = jobs.get(job_id)
        if not job or not job.document_id:
            return

        jobs.set_status(job, JobStatus.RUNNING)
        try:
            LightRAGIngestionService(session).ingest_document(job.document_id)
            jobs.set_status(job, JobStatus.SUCCEEDED)
        except DomainIngestBusy as exc:
            jobs.set_status(job, JobStatus.QUEUED, error_message=str(exc))
            raise
        except Exception as exc:
            jobs.set_status(job, JobStatus.FAILED, error_message=str(exc))
            raise


def run_navigation_process_job(job_id: str) -> None:
    with SessionLocal() as session:
        jobs = JobRepository(session)
        job = jobs.get(job_id)
        if not job or not job.document_id:
            return

        jobs.set_status(job, JobStatus.RUNNING)
        try:
            IndexingService(session).index_document(job.document_id)
            jobs.set_status(job, JobStatus.SUCCEEDED)
        except Exception as exc:
            jobs.set_status(job, JobStatus.FAILED, error_message=str(exc))
            raise

