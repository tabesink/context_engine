from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.api.routes.documents import document_response
from app.schemas.documents import DocumentResponse, UploadResponse
from app.services.document_service import DocumentService
from app.services.job_service import JobService
from app.storage.db import get_session
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.logs import LogRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/ping")
def admin_ping(admin: UserRow = Depends(require_admin)) -> dict[str, str]:
    return {"status": "ok", "admin": admin.email}


@router.post("/documents/upload")
def upload_document(
    file: UploadFile,
    semantic_engine: str = Form(default="lightrag"),
    lightrag_domain_id: str | None = Form(default=None),
    process_navigation: bool = Form(default=True),
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> UploadResponse:
    document, job_id = DocumentService(session).upload(
        actor_id=admin.id,
        file=file,
        semantic_engine=semantic_engine,
        lightrag_domain_id=lightrag_domain_id,
        process_navigation=process_navigation,
    )
    return UploadResponse(document=document_response(document), job_id=job_id)


@router.post("/documents/{document_id}/index")
def index_document(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    del admin
    job_id = JobService(session).enqueue_index_document(document_id=document_id)
    return {"job_id": job_id}


@router.post("/documents/{document_id}/reindex")
def reindex_document(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> dict[str, str]:
    del admin
    job_id = JobService(session).enqueue_index_document(document_id=document_id)
    return {"job_id": job_id}


@router.post("/documents/{document_id}/refresh-lightrag-status")
def refresh_lightrag_status(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DocumentResponse:
    del admin
    document = DocumentService(session).refresh_lightrag_status(document_id=document_id)
    return document_response(document)


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
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> list[DocumentResponse]:
    del admin
    return [document_response(document) for document in DocumentRepository(session).list_all()]


@router.get("/audit-logs")
def list_audit_logs(
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
        for row in LogRepository(session).list_audit()
    ]


@router.get("/query-logs")
def list_query_logs(
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
        for row in LogRepository(session).list_queries()
    ]

