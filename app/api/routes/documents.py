from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import not_found
from app.schemas.documents import DocumentResponse, PageResponse, StructureResponse
from app.services.document_access_policy import DocumentAccessPolicy
from app.services.document_asset_service import DocumentAssetService
from app.storage.db import get_session
from app.storage.repositories.documents import DocumentRepository
from app.storage.repositories.document_processing import DocumentProcessingRepository
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
    policy = DocumentAccessPolicy(DocumentRepository(session))
    return [document_response(document) for document in policy.list_readable_documents(user)]


@router.get("/{document_id}")
def get_document(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> DocumentResponse:
    document = DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    return document_response(document)


@router.get("/{document_id}/structure")
def get_structure(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> StructureResponse:
    DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    navigation = DocumentRepository(session).get_navigation_index(document_id)
    if not navigation:
        raise not_found("Document structure not found")
    return StructureResponse(document_id=document_id, tree=navigation.tree)


@router.get("/{document_id}/assets/{asset_id}")
def get_asset(
    document_id: str,
    asset_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> FileResponse:
    asset = DocumentAssetService(
        access_policy=DocumentAccessPolicy(DocumentRepository(session)),
        assets=DocumentProcessingRepository(session),
    ).get_asset_file(user=user, document_id=document_id, asset_id=asset_id)
    return FileResponse(asset.path, media_type=asset.media_type, filename=asset.filename)


@router.get("/{document_id}/assets/{asset_id}/thumbnail")
def get_asset_thumbnail(
    document_id: str,
    asset_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> FileResponse:
    asset = DocumentAssetService(
        access_policy=DocumentAccessPolicy(DocumentRepository(session)),
        assets=DocumentProcessingRepository(session),
    ).get_asset_file(user=user, document_id=document_id, asset_id=asset_id, thumbnail=True)
    return FileResponse(asset.path, media_type=asset.media_type, filename=asset.filename)


@router.get("/{document_id}/pages/{page_number}")
def get_page(
    document_id: str,
    page_number: int,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PageResponse:
    DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
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

