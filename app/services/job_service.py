from typing import Protocol

from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.models import JobStatus
from app.storage.repositories.jobs import JobRepository

DOCUMENT_INGEST_JOB_KIND = "document_ingest"
LEGACY_DOCUMENT_INGEST_JOB_KINDS = {"lightrag_ingest_document"}


def is_document_ingest_job_kind(kind: str) -> bool:
    return kind == DOCUMENT_INGEST_JOB_KIND or kind in LEGACY_DOCUMENT_INGEST_JOB_KINDS


class IndexQueue(Protocol):
    def enqueue(self, function: object, job_id: str):
        ...


class JobService:
    def __init__(
        self,
        session: Session,
        *,
        queue: IndexQueue | None = None,
        run_inline: bool | None = None,
    ):
        self.session = session
        self.jobs = JobRepository(session)
        self.run_inline = get_settings().index_jobs_inline if run_inline is None else run_inline
        self.queue = queue

    def enqueue_document_ingest(self, *, document_id: str) -> str:
        job = self.jobs.create(kind=DOCUMENT_INGEST_JOB_KIND, document_id=document_id)
        if self.run_inline:
            self.run_document_ingest_job(job.id)
            return job.id

        from app.workers.tasks import run_document_ingest_job

        queued_job = self._queue().enqueue(run_document_ingest_job, job.id)
        metadata = job.meta | {"rq_job_id": queued_job.id}
        self.jobs.set_status(job, JobStatus.QUEUED, metadata=metadata)
        return job.id

    def run_document_ingest_job(self, job_id: str) -> None:
        from app.workers.tasks import run_document_ingest_job

        run_document_ingest_job(job_id)

    # Backward-compatible wrapper for call sites that still use old naming.
    def enqueue_lightrag_ingest_document(self, *, document_id: str) -> str:
        return self.enqueue_document_ingest(document_id=document_id)

    # Backward-compatible wrapper for retry or direct invocations.
    def run_lightrag_ingest_job(self, job_id: str) -> None:
        self.run_document_ingest_job(job_id)

    def _queue(self) -> IndexQueue:
        if self.queue is not None:
            return self.queue
        settings = get_settings()
        return Queue("indexing", connection=Redis.from_url(settings.redis_url))

