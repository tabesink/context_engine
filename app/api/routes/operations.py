from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.errors import not_found
from app.schemas.jobs import OperationResponse
from app.services.job_service import JobService, is_document_ingest_job_kind
from app.storage.db import get_session
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.jobs import JobRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/operations", tags=["operations"])


def operation_response(job, *, session: Session) -> OperationResponse:
    return OperationResponse(
        id=job.id,
        type=job.kind,
        status=job.status,
        stage=job.stage,
        progress=operation_progress(job),
        resource_type=job.resource_type,
        resource_id=job.resource_id,
        resource_label=operation_resource_label(job, session=session),
        actor_user_id=job.requested_by_user_id,
        message=job.message,
        error_message=job.error_message,
        metadata=job.meta,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        updated_at=job.updated_at,
    )


def operation_progress(job) -> int | None:
    if job.progress_current is None:
        return None
    if job.progress_total and job.progress_total > 0:
        return min(100, max(0, round((job.progress_current / job.progress_total) * 100)))
    return job.progress_current


def operation_resource_label(job, *, session: Session) -> str | None:
    if job.resource_type == "document" and job.resource_id:
        document = DocumentRepository(session).get(job.resource_id)
        if document is not None:
            return document.filename
    if isinstance(job.meta, dict):
        label = job.meta.get("resource_label") or job.meta.get("display_name")
        if label:
            return str(label)
    return job.resource_id


@router.get("")
def list_operations(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[OperationResponse]:
    del admin
    jobs = JobRepository(session).list_operations(
        limit=limit,
        offset=offset,
        resource_type=resource_type,
        resource_id=resource_id,
        status=status,
    )
    return [operation_response(job, session=session) for job in jobs]


@router.get("/{operation_id}")
def get_operation(
    operation_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> OperationResponse:
    del admin
    operation = JobRepository(session).get(operation_id)
    if not operation:
        raise not_found("Operation not found")
    return operation_response(operation, session=session)


@router.post("/{operation_id}/retry")
def retry_operation(
    operation_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> OperationResponse:
    del admin
    operation = JobRepository(session).get(operation_id)
    if not operation:
        raise not_found("Operation not found")
    if not is_document_ingest_job_kind(operation.kind):
        raise HTTPException(status_code=400, detail="Only document_ingest operations can be retried")
    JobService(session).run_document_ingest_job(operation.id)
    session.expire_all()
    refreshed = JobRepository(session).get(operation_id)
    if not refreshed:
        raise not_found("Operation not found")
    return operation_response(refreshed, session=session)
