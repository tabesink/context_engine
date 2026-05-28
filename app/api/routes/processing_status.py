from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.schemas.processing_status import (
    DomainProcessingStatusResponse,
    DocumentProcessingStatusResponse,
    ProcessingStatusListResponse,
)
from app.services.lightrag_domain_registry import (
    LightRAGDomainRegistryError,
    lightrag_domain_http_exception,
)
from app.services.processing_status_service import ProcessingStatusService
from app.storage.db import get_session
from app.storage.tables import UserRow

router = APIRouter(tags=["processing-status"])


@router.get("/lightrag/domains/{domain_id}/processing-status")
def get_user_domain_processing_status(
    domain_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DomainProcessingStatusResponse:
    del user
    try:
        return ProcessingStatusService(session).get_domain_status(domain_id=domain_id, admin=False)
    except LightRAGDomainRegistryError as exc:
        raise lightrag_domain_http_exception(exc) from exc


@router.get("/admin/lightrag/domains/{domain_id}/processing-status")
def get_admin_domain_processing_status(
    domain_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DomainProcessingStatusResponse:
    del admin
    try:
        return ProcessingStatusService(session).get_domain_status(domain_id=domain_id, admin=True)
    except LightRAGDomainRegistryError as exc:
        raise lightrag_domain_http_exception(exc) from exc


@router.get("/admin/documents/{document_id}/processing-status")
def get_admin_document_processing_status(
    document_id: str,
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> DocumentProcessingStatusResponse:
    del admin
    return ProcessingStatusService(session).get_admin_document_status(document_id=document_id)


@router.get("/documents/{document_id}/processing-status")
def get_user_document_processing_status(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentProcessingStatusResponse:
    return ProcessingStatusService(session).get_user_document_status(document_id=document_id, user=user)


@router.get("/admin/lightrag/domains/{domain_id}/documents/processing-status")
def get_admin_domain_documents_processing_status(
    domain_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin: UserRow = Depends(require_admin),
    session: Session = Depends(get_session),
) -> ProcessingStatusListResponse:
    del admin
    try:
        return ProcessingStatusService(session).get_admin_domain_documents_status(
            domain_id=domain_id,
            limit=limit,
            offset=offset,
        )
    except LightRAGDomainRegistryError as exc:
        raise lightrag_domain_http_exception(exc) from exc
