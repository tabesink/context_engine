from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.errors import not_found
from app.document_processing.refinement import StructureQualityScorer
from app.schemas.documents import (
    DocumentResponse,
    PageResponse,
    SectionDetailResponse,
    SourceChunkResponse,
    StructureQualityResponse,
    StructureResponse,
)
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
    include_blocks: bool = Query(default=False),
    include_assets: bool = Query(default=False),
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> StructureResponse:
    document = DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    processing = DocumentProcessingRepository(session)
    canonical = processing.get_structure(document_id, source_file=document.storage_path)
    if canonical:
        return StructureResponse(
            document_id=document_id,
            tree=_section_tree(canonical.sections),
            source="document_structure",
            pages=[page.model_dump() for page in canonical.pages],
            sections=[section.model_dump() for section in canonical.sections],
            blocks=[block.model_dump() for block in canonical.blocks] if include_blocks else [],
            source_chunks=[chunk.model_dump() for chunk in canonical.source_chunks],
            assets=[asset.model_dump() for asset in canonical.assets] if include_assets else [],
        )
    raise not_found("Document structure not found")


def _section_tree(sections) -> list[dict]:
    by_parent: dict[str | None, list] = {}
    for section in sections:
        by_parent.setdefault(section.parent_section_id, []).append(section)

    def build(parent_id: str | None) -> list[dict]:
        return [
            {
                "section_id": section.section_id,
                "title": section.title,
                "level": section.level,
                "page_start": section.page_start,
                "page_end": section.page_end,
                "children": build(section.section_id),
            }
            for section in by_parent.get(parent_id, [])
        ]

    return build(None)


@router.get("/{document_id}/ingestion-status")
def get_ingestion_status(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    document = DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    metadata = document.meta if isinstance(document.meta, dict) else {}
    return {
        "document_id": document.id,
        "status": document.status,
        "lightrag": metadata.get("lightrag") or {},
        "navigation": metadata.get("navigation") or {},
        "error_message": document.error_message,
    }


@router.get("/{document_id}/structure-quality")
def get_structure_quality(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> StructureQualityResponse:
    document = DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    structure = DocumentProcessingRepository(session).get_structure(
        document_id,
        source_file=document.storage_path,
    )
    if not structure:
        raise not_found("Document structure not found")
    quality = StructureQualityScorer().score(structure)
    return StructureQualityResponse(document_id=document_id, **quality.model_dump())


@router.get("/{document_id}/sections/{section_id}")
def get_section(
    document_id: str,
    section_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> SectionDetailResponse:
    document = DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    structure = DocumentProcessingRepository(session).get_structure(
        document_id,
        source_file=document.storage_path,
    )
    if not structure:
        raise not_found("Document section not found")

    section = next((item for item in structure.sections if item.section_id == section_id), None)
    if not section:
        raise not_found("Document section not found")

    blocks = [block for block in structure.blocks if block.section_id == section_id]
    chunks = [chunk for chunk in structure.source_chunks if chunk.section_id == section_id]
    block_ids = {block.block_id for block in blocks}
    chunk_ids = {chunk.chunk_id for chunk in chunks}
    assets = [
        asset
        for asset in structure.assets
        if asset.section_id == section_id
        or asset.block_id in block_ids
        or asset.chunk_id in chunk_ids
    ]
    return SectionDetailResponse(
        document_id=document_id,
        section=section.model_dump(),
        blocks=[block.model_dump() for block in blocks],
        source_chunks=[chunk.model_dump() for chunk in chunks],
        assets=[asset.model_dump() for asset in assets],
    )


@router.get("/{document_id}/assets")
def list_assets(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[dict]:
    document = DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    structure = DocumentProcessingRepository(session).get_structure(
        document_id,
        source_file=document.storage_path,
    )
    if not structure:
        raise not_found("Document assets not found")
    return [asset.model_dump() for asset in structure.assets]


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


@router.get("/{document_id}/chunks")
def list_source_chunks(
    document_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> list[SourceChunkResponse]:
    document = DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    structure = DocumentProcessingRepository(session).get_structure(
        document_id,
        source_file=document.storage_path,
    )
    if not structure:
        raise not_found("Document source chunks not found")
    return [SourceChunkResponse(**chunk.model_dump()) for chunk in structure.source_chunks]


@router.get("/{document_id}/chunks/{chunk_id}")
def get_source_chunk(
    document_id: str,
    chunk_id: str,
    user: UserRow = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> SourceChunkResponse:
    DocumentAccessPolicy(DocumentRepository(session)).get_readable_document_or_404(
        user=user,
        document_id=document_id,
    )
    chunk = DocumentProcessingRepository(session).get_source_chunk(document_id, chunk_id)
    if not chunk:
        raise not_found("Document source chunk not found")
    return SourceChunkResponse(**chunk.model_dump())


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
    page = DocumentProcessingRepository(session).get_page(document_id, page_number)
    if not page:
        raise not_found("Page not found")
    return PageResponse(
        document_id=document_id,
        page_number=page_number,
        text=page.text or "",
        metadata=page.metadata,
    )

