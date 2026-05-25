from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.errors import not_found
from app.schemas.jobs import JobResponse
from app.services.job_service import JobService
from app.storage.db import get_session
from app.storage.repositories.jobs import JobRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/jobs", tags=["jobs"])


def job_response(job) -> JobResponse:
    return JobResponse(
        id=job.id,
        kind=job.kind,
        status=job.status,
        document_id=job.document_id,
        error_message=job.error_message,
        metadata=job.meta,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("")
def list_jobs(
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[JobResponse]:
    del admin
    return [job_response(job) for job in JobRepository(session).list()]


@router.get("/{job_id}")
def get_job(
    job_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> JobResponse:
    del admin
    job = JobRepository(session).get(job_id)
    if not job:
        raise not_found("Job not found")
    return job_response(job)


@router.post("/{job_id}/retry")
def retry_job(
    job_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> JobResponse:
    del admin
    job = JobRepository(session).get(job_id)
    if not job:
        raise not_found("Job not found")
    if job.kind != "lightrag_ingest_document":
        raise HTTPException(status_code=400, detail="Only lightrag_ingest_document jobs can be retried")
    JobService(session).run_lightrag_ingest_job(job.id)
    refreshed = JobRepository(session).get(job_id)
    return job_response(refreshed)

