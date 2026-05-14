from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import JobStatus, utc_now
from app.storage.tables import JobRow


class JobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, *, kind: str, document_id: str | None, metadata: dict | None = None) -> JobRow:
        job = JobRow(kind=kind, document_id=document_id, meta=metadata or {})
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get(self, job_id: str) -> JobRow | None:
        return self.session.get(JobRow, job_id)

    def list(self) -> list[JobRow]:
        return list(self.session.scalars(select(JobRow).order_by(JobRow.created_at.desc())))

    def set_status(
        self,
        job: JobRow,
        status: JobStatus,
        *,
        error_message: str | None = None,
        metadata: dict | None = None,
    ) -> JobRow:
        job.status = status.value
        job.error_message = error_message
        if metadata is not None:
            job.meta = metadata
        job.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(job)
        return job

