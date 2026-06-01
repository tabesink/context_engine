from fastapi import APIRouter, Depends, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.api.routes.documents import document_response, ingestion_status_response
from app.core.errors import not_found
from app.schemas.documents import (
    DocumentResponse,
    DomainDocumentsProcessingStatusResponse,
    ProcessingDomainStatus,
    ProcessingStatusResponse,
    UploadOperationResponse,
    UploadResponse,
)
from app.services.document_service import DocumentService
from app.services.document_retry_service import DocumentRetryService
from app.services.processing_status_service import ProcessingStatusService
from app.storage.db import get_session
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.jobs import JobRepository
from app.storage.repositories.logs import LogRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def admin_ping(admin: UserRow = Depends(require_admin)) -> dict[str, str]:
    return {"status": "ok", "admin": admin.email}


@router.post("/documents/upload")
def upload_document(
    file: UploadFile,
    lightrag_domain_id: str | None = Form(default=None),
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> UploadResponse:
    document, job_id = DocumentService(session).upload(
        actor_id=admin.id,
        file=file,
        lightrag_domain_id=lightrag_domain_id,
    )
    operation = JobRepository(session).get(job_id) if job_id else None
    return UploadResponse(
        document=document_response(document),
        operation_id=operation.id if operation is not None else job_id,
        operation=upload_operation_response(operation) if operation is not None else None,
        status_url=f"/documents/{document.id}/processing-status",
    )


def upload_operation_response(job) -> UploadOperationResponse:
    return UploadOperationResponse(
        id=job.id,
        type=job.kind,
        status=job.status,
        stage=job.stage,
        message=job.message,
    )


@router.post("/documents/{document_id}/refresh-status")
def refresh_status(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DocumentResponse:
    del admin
    document = DocumentService(session).refresh_lightrag_status(document_id=document_id)
    return document_response(document)


@router.get("/documents/{document_id}/ingestion-status")
def get_admin_ingestion_status(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> dict:
    # Deprecated compatibility surface. New UI should poll processing-status.
    del admin
    document = DocumentRepository(session).get(document_id)
    if not document:
        raise not_found("Document not found")
    structure = DocumentProcessingRepository(session).get_structure(
        document_id,
        source_file=document.storage_path,
    )
    return ingestion_status_response(document, structure)


@router.get("/documents/{document_id}/processing-status")
def get_admin_processing_status(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ProcessingStatusResponse:
    del admin
    document = DocumentRepository(session).get(document_id)
    if not document:
        raise not_found("Document not found")
    return ProcessingStatusService(session).for_document(document)


@router.get("/lightrag/domains/{domain_id}/documents/processing-status")
def get_admin_domain_documents_processing_status(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DomainDocumentsProcessingStatusResponse:
    del admin
    documents = DocumentRepository(session).list_all_by_lightrag_domain(domain_id)
    return ProcessingStatusService(session).for_domain_documents(
        domain_id=domain_id,
        documents=documents,
    )


@router.get("/lightrag/domains/{domain_id}/processing-status")
def get_admin_domain_processing_status(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ProcessingDomainStatus:
    del admin
    documents = DocumentRepository(session).list_all_by_lightrag_domain(domain_id)
    return ProcessingStatusService(session).domain_summary(domain_id=domain_id, documents=documents)


@router.post("/documents/{document_id}/reingest")
def reingest(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    operation_id = DocumentService(session).reingest(actor_id=admin.id, document_id=document_id)
    return {"operation_id": operation_id}


@router.post("/documents/{document_id}/retry-ingestion")
def retry_document_ingestion(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> UploadResponse:
    document, job_id = DocumentRetryService(session).retry_ingestion(
        actor_id=admin.id,
        document_id=document_id,
    )
    operation = JobRepository(session).get(job_id)
    return UploadResponse(
        document=document_response(document),
        operation_id=operation.id if operation is not None else job_id,
        operation=upload_operation_response(operation) if operation is not None else None,
        status_url=f"/documents/{document.id}/processing-status",
    )


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DocumentResponse:
    document = DocumentService(session).delete(actor_id=admin.id, document_id=document_id)
    return document_response(document)


@router.get("/documents")
def list_all_documents(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[DocumentResponse]:
    del admin
    return [
        document_response(document)
        for document in DocumentRepository(session).list_all(limit=limit, offset=offset)
    ]


@router.get("/audit-logs")
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[dict]:
    del admin
    return [
        {
            "id": row.id,
            "event": row.event,
            "target_id": row.target_id,
            "metadata": row.meta,
            "created_at": row.created_at,
        }
        for row in LogRepository(session).list_audit(limit=limit, offset=offset)
    ]


@router.get("/query-logs")
def list_query_logs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[dict]:
    del admin
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "query": row.query,
            "mode": row.mode,
            "latency_ms": row.latency_ms,
            "evidence_count": row.evidence_count,
            "created_at": row.created_at,
        }
        for row in LogRepository(session).list_queries(limit=limit, offset=offset)
    ]

