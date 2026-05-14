from app.domain.models import JobStatus
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

