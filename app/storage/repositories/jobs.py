from collections.abc import Sequence
from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import JobStatus, OperationResourceType, OperationStatus, utc_now
from app.storage.tables import JobRow


class JobRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        kind: str,
        document_id: str | None,
        metadata: dict | None = None,
        resource_type: OperationResourceType | str | None = None,
        resource_id: str | None = None,
        requested_by_user_id: str | None = None,
        stage: str | None = None,
        message: str | None = None,
        progress_current: int | None = None,
        progress_total: int | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> JobRow:
        resolved_resource_type = resource_type or (
            OperationResourceType.DOCUMENT if document_id else OperationResourceType.SYSTEM
        )
        resolved_resource_id = resource_id if resource_id is not None else document_id
        job = JobRow(
            kind=kind,
            document_id=document_id,
            resource_type=str(resolved_resource_type),
            resource_id=resolved_resource_id,
            requested_by_user_id=requested_by_user_id,
            stage=stage,
            message=message,
            progress_current=progress_current,
            progress_total=progress_total,
            started_at=started_at,
            finished_at=finished_at,
            meta=metadata or {},
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def create_operation(
        self,
        *,
        operation_type: str,
        resource_type: OperationResourceType | str,
        resource_id: str | None,
        requested_by_user_id: str | None = None,
        metadata: dict | None = None,
        document_id: str | None = None,
        stage: str | None = None,
        message: str | None = None,
        progress_current: int | None = None,
        progress_total: int | None = None,
    ) -> JobRow:
        return self.create(
            kind=operation_type,
            document_id=document_id,
            metadata=metadata,
            resource_type=resource_type,
            resource_id=resource_id,
            requested_by_user_id=requested_by_user_id,
            stage=stage,
            message=message,
            progress_current=progress_current,
            progress_total=progress_total,
        )

    def get(self, job_id: str) -> JobRow | None:
        return self.session.get(JobRow, job_id)

    def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        resource_type: OperationResourceType | str | None = None,
        resource_id: str | None = None,
        status: JobStatus | OperationStatus | str | None = None,
    ) -> List[JobRow]:
        query = select(JobRow)
        if resource_type is not None:
            query = query.where(JobRow.resource_type == str(resource_type))
        if resource_id is not None:
            query = query.where(JobRow.resource_id == resource_id)
        if status is not None:
            query = query.where(JobRow.status == str(status))
        query = query.order_by(JobRow.created_at.desc()).limit(limit).offset(offset)
        return list(self.session.scalars(query))

    def list_operations(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        resource_type: OperationResourceType | str | None = None,
        resource_id: str | None = None,
        status: JobStatus | OperationStatus | str | None = None,
    ) -> List[JobRow]:
        return self.list(
            limit=limit,
            offset=offset,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
        )

    def set_status(
        self,
        job: JobRow,
        status: JobStatus | OperationStatus,
        *,
        error_message: str | None = None,
        metadata: dict | None = None,
        stage: str | None = None,
        message: str | None = None,
        progress_current: int | None = None,
        progress_total: int | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> JobRow:
        status_value = status.value if isinstance(status, (JobStatus, OperationStatus)) else str(status)
        job.status = status_value
        job.error_message = error_message
        if metadata is not None:
            job.meta = metadata
        if stage is not None:
            job.stage = stage
        if message is not None:
            job.message = message
        if progress_current is not None:
            job.progress_current = progress_current
        if progress_total is not None:
            job.progress_total = progress_total
        if started_at is not None:
            job.started_at = started_at
        if finished_at is not None:
            job.finished_at = finished_at
        job.updated_at = utc_now()
        self.session.commit()
        self.session.refresh(job)
        return job

    def mark_operation_running(
        self,
        job: JobRow,
        *,
        metadata: dict | None = None,
        stage: str | None = None,
        message: str | None = None,
        progress_current: int | None = None,
        progress_total: int | None = None,
        started_at: datetime | None = None,
    ) -> JobRow:
        return self.set_status(
            job,
            OperationStatus.RUNNING,
            metadata=metadata,
            stage=stage,
            message=message,
            progress_current=progress_current,
            progress_total=progress_total,
            started_at=started_at or utc_now(),
            finished_at=None,
        )

    def mark_operation_succeeded(
        self,
        job: JobRow,
        *,
        metadata: dict | None = None,
        stage: str | None = None,
        message: str | None = None,
        progress_current: int | None = None,
        progress_total: int | None = None,
        finished_at: datetime | None = None,
    ) -> JobRow:
        return self.set_status(
            job,
            OperationStatus.SUCCEEDED,
            metadata=metadata,
            stage=stage,
            message=message,
            progress_current=progress_current,
            progress_total=progress_total,
            finished_at=finished_at or utc_now(),
            error_message=None,
        )

    def mark_operation_failed(
        self,
        job: JobRow,
        *,
        error_message: str | None = None,
        metadata: dict | None = None,
        stage: str | None = None,
        message: str | None = None,
        finished_at: datetime | None = None,
    ) -> JobRow:
        return self.set_status(
            job,
            OperationStatus.FAILED,
            error_message=error_message,
            metadata=metadata,
            stage=stage,
            message=message,
            finished_at=finished_at or utc_now(),
        )

    def list_by_document_ids(self, document_ids: Sequence[str]) -> List[JobRow]:
        if not document_ids:
            return []
        return list(
            self.session.scalars(
                select(JobRow).where(JobRow.document_id.in_(document_ids)).order_by(JobRow.created_at.desc())
            )
        )

    def clear_document_references(self, document_ids: Sequence[str]) -> int:
        if not document_ids:
            return 0
        jobs = self.list_by_document_ids(document_ids)
        for job in jobs:
            job.document_id = None
            job.updated_at = utc_now()
        self.session.commit()
        return len(jobs)

