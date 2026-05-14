from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import not_found
from app.schemas.documents import DocumentResponse, PageResponse, StructureResponse
from app.services.document_service import DocumentService
from app.storage.db import get_session
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import UserRow

router = APIRouter(prefix="/documents", tags=["documents"])


def document_response(document) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
        metadata=document.meta,
        error_message=document.error_message,
    )


@router.get("")
def list_documents(
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[DocumentResponse]:
    del user
    return [document_response(document) for document in DocumentRepository(session).list_ready()]


@router.get("/{document_id}")
def get_document(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentResponse:
    del user
    document = DocumentService(session).get_ready_or_404(document_id)
    return document_response(document)


@router.get("/{document_id}/structure")
def get_structure(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> StructureResponse:
    del user
    DocumentService(session).get_ready_or_404(document_id)
    navigation = DocumentRepository(session).get_navigation_index(document_id)
    if not navigation:
        raise not_found("Document structure not found")
    return StructureResponse(document_id=document_id, tree=navigation.tree)


@router.get("/{document_id}/pages/{page_number}")
def get_page(
    document_id: str,
    page_number: int,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PageResponse:
    del user
    DocumentService(session).get_ready_or_404(document_id)
    parsed = DocumentRepository(session).get_parsed(document_id)
    if not parsed:
        raise not_found("Parsed document not found")
    for page in parsed.pages:
        if page.get("number") == page_number:
            return PageResponse(
                document_id=document_id,
                page_number=page_number,
                text=page.get("text", ""),
                metadata=page.get("metadata", {}),
            )
    raise not_found("Page not found")

