from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.errors import not_found
from app.schemas.jobs import OperationResponse
from app.storage.db import get_session
from app.storage.repositories.jobs import JobRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/operations", tags=["operations"])


def operation_response(job) -> OperationResponse:
    return OperationResponse(
        id=job.id,
        operation_type=job.kind,
        status=job.status,
        resource_type=job.resource_type,
        resource_id=job.resource_id,
        requested_by_user_id=job.requested_by_user_id,
        stage=job.stage,
        message=job.message,
        progress_current=job.progress_current,
        progress_total=job.progress_total,
        error_message=job.error_message,
        metadata=job.meta,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        updated_at=job.updated_at,
    )


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
    return [operation_response(job) for job in jobs]


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
    return operation_response(operation)
