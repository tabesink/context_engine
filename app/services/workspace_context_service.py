from dataclasses import dataclass

from fastapi import HTTPException, status

from app.core.errors import not_found
from app.document_processing.models import (
    DocumentAsset,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
    SourceChunk,
)
from app.schemas.workspace_context import (
    WorkspaceContextAsset,
    WorkspaceContextBreadcrumbItem,
    WorkspaceContextDocument,
    WorkspaceContextNodeKind,
    WorkspaceSourceContext,
)
from app.services.asset_urls import document_asset_thumbnail_url, document_asset_url
from app.services.document_access_policy import DocumentAccessPolicy
from app.services.lightrag_domain_registry import LightRAGDomainRegistry
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow, UserRow


TEXT_LIMIT = 12_000


@dataclass(frozen=True)
class ParsedWorkspaceNodeId:
    kind: WorkspaceContextNodeKind
    document_id: str | None = None
    value: str | None = None


def parse_workspace_node_id(node_id: str) -> ParsedWorkspaceNodeId:
    parts = node_id.split(":", 2)
    kind = parts[0]

    if kind == "domain" and len(parts) == 2 and parts[1]:
        return ParsedWorkspaceNodeId(kind="domain", value=parts[1])
    if kind == "document" and len(parts) == 2 and parts[1]:
        return ParsedWorkspaceNodeId(kind="document", document_id=parts[1])
    if kind in {"section", "page", "chunk", "asset"} and len(parts) == 3:
        document_id, value = parts[1], parts[2]
        if document_id and value:
            return ParsedWorkspaceNodeId(
                kind=kind,  # type: ignore[arg-type]
                document_id=document_id,
                value=value,
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid workspace node id",
    )


def resolve_document_domain_id(document: DocumentRow) -> str | None:
    domain_id = (document.lightrag_domain_id or "").strip()
    if domain_id:
        return domain_id

    metadata = document.meta if isinstance(document.meta, dict) else {}
    lightrag = metadata.get("lightrag", {}) if isinstance(metadata.get("lightrag"), dict) else {}
    resolved = str(lightrag.get("domain_id") or lightrag.get("domain") or "").strip()
    return resolved or None


class WorkspaceContextService:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        processing: DocumentProcessingRepository,
        domain_registry: LightRAGDomainRegistry,
    ):
        self.documents = documents
        self.processing = processing
        self.domain_registry = domain_registry

    def build_for_node(
        self,
        *,
        domain_id: str,
        node_id: str,
        user: UserRow,
    ) -> WorkspaceSourceContext:
        domain = self.domain_registry.validate_available(domain_id)
        parsed = parse_workspace_node_id(node_id)

        if parsed.kind == "domain":
            if parsed.value != domain.id:
                raise not_found("Workspace source context not found")
            return WorkspaceSourceContext(
                node_id=node_id,
                kind="domain",
                title=domain.display_name or domain.id,
                domain_id=domain.id,
                breadcrumb=[
                    WorkspaceContextBreadcrumbItem(
                        id=f"domain:{domain.id}",
                        kind="domain",
                        title=domain.display_name or domain.id,
                    )
                ],
                summary="Workspace source tree root.",
                metadata={
                    "is_healthy": domain.is_healthy,
                    "is_default": domain.is_default,
                    "status": domain.status,
                },
            )

        if not parsed.document_id:
            raise not_found("Workspace source context not found")

        document = DocumentAccessPolicy(self.documents).get_readable_document_or_404(
            user=user,
            document_id=parsed.document_id,
        )
        if resolve_document_domain_id(document) != domain.id:
            raise not_found("Document not found")

        structure = self.processing.get_structure(document.id, source_file=document.storage_path)
        if parsed.kind == "document":
            return self._document_context(
                domain_id=domain.id,
                domain_title=domain.display_name or domain.id,
                node_id=node_id,
                document=document,
                structure=structure,
            )
        if structure is None:
            raise not_found(self._missing_detail(parsed.kind))
        if parsed.kind == "section":
            return self._section_context(
                domain_id=domain.id,
                domain_title=domain.display_name or domain.id,
                node_id=node_id,
                document=document,
                structure=structure,
                section_id=parsed.value or "",
            )
        if parsed.kind == "page":
            try:
                page_number = int(parsed.value or "")
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid workspace node id",
                ) from exc
            return self._page_context(
                domain_id=domain.id,
                domain_title=domain.display_name or domain.id,
                node_id=node_id,
                document=document,
                structure=structure,
                page_number=page_number,
            )
        if parsed.kind == "chunk":
            return self._chunk_context(
                domain_id=domain.id,
                domain_title=domain.display_name or domain.id,
                node_id=node_id,
                document=document,
                structure=structure,
                chunk_id=parsed.value or "",
            )
        return self._asset_context(
            domain_id=domain.id,
            domain_title=domain.display_name or domain.id,
            node_id=node_id,
            document=document,
            structure=structure,
            asset_id=parsed.value or "",
        )

    def _document_context(
        self,
        *,
        domain_id: str,
        domain_title: str,
        node_id: str,
        document: DocumentRow,
        structure: DocumentStructure | None,
    ) -> WorkspaceSourceContext:
        counts = self.processing.count_by_document_ids([document.id])
        text = None
        if structure:
            text = self._truncate_text(self._first_text(structure))

        return WorkspaceSourceContext(
            node_id=node_id,
            kind="document",
            title=document.filename,
            domain_id=domain_id,
            breadcrumb=self._base_breadcrumb(domain_id, domain_title, document),
            document=self._document_payload(document),
            summary="Document source context.",
            text=text,
            metadata={
                "structure_available": structure is not None,
                "counts": counts,
            },
        )

    def _section_context(
        self,
        *,
        domain_id: str,
        domain_title: str,
        node_id: str,
        document: DocumentRow,
        structure: DocumentStructure,
        section_id: str,
    ) -> WorkspaceSourceContext:
        section = next((item for item in structure.sections if item.section_id == section_id), None)
        if section is None:
            raise not_found("Document section not found")

        chunks = [chunk for chunk in structure.source_chunks if chunk.section_id == section_id]
        block_ids = {
            block.block_id for block in structure.blocks if block.section_id == section_id
        }
        chunk_ids = {chunk.chunk_id for chunk in chunks}
        assets = [
            asset
            for asset in structure.assets
            if asset.section_id == section_id
            or asset.block_id in block_ids
            or asset.chunk_id in chunk_ids
        ]
        return WorkspaceSourceContext(
            node_id=node_id,
            kind="section",
            title=section.title,
            domain_id=domain_id,
            breadcrumb=self._breadcrumb_for_section(domain_id, domain_title, document, structure, section),
            document=self._document_payload(document),
            section_id=section.section_id,
            page_start=section.page_start,
            page_end=section.page_end,
            summary=self._page_range_summary("Section", section.page_start, section.page_end),
            text=self._truncate_text("\n\n".join(chunk.text for chunk in chunks if chunk.text)),
            assets=[self._asset_payload(asset) for asset in assets],
            metadata={
                "level": section.level,
                "source": section.source,
            },
        )

    def _page_context(
        self,
        *,
        domain_id: str,
        domain_title: str,
        node_id: str,
        document: DocumentRow,
        structure: DocumentStructure,
        page_number: int,
    ) -> WorkspaceSourceContext:
        page = next((item for item in structure.pages if item.page_number == page_number), None)
        if page is None:
            raise not_found("Page not found")

        chunks = [chunk for chunk in structure.source_chunks if self._chunk_in_page(chunk, page_number)]
        assets = [asset for asset in structure.assets if asset.page_number == page_number]
        text = page.text or "\n\n".join(chunk.text for chunk in chunks if chunk.text)
        title = f"Page {page.page_number}"
        return WorkspaceSourceContext(
            node_id=node_id,
            kind="page",
            title=title,
            domain_id=domain_id,
            breadcrumb=[
                *self._base_breadcrumb(domain_id, domain_title, document),
                WorkspaceContextBreadcrumbItem(id=node_id, kind="page", title=title),
            ],
            document=self._document_payload(document),
            page_number=page.page_number,
            page_start=page.page_number,
            page_end=page.page_number,
            summary=f"Exact page context for page {page.page_number}.",
            text=self._truncate_text(text),
            assets=[self._asset_payload(asset) for asset in assets],
            metadata=self._safe_page_metadata(page),
        )

    def _chunk_context(
        self,
        *,
        domain_id: str,
        domain_title: str,
        node_id: str,
        document: DocumentRow,
        structure: DocumentStructure,
        chunk_id: str,
    ) -> WorkspaceSourceContext:
        chunk = next((item for item in structure.source_chunks if item.chunk_id == chunk_id), None)
        if chunk is None:
            raise not_found("Document source chunk not found")

        section = self._section_for_chunk(structure, chunk)
        assets = [
            asset
            for asset in structure.assets
            if asset.asset_id in chunk.asset_ids or asset.chunk_id == chunk.chunk_id
        ]
        title = self._chunk_title(chunk)
        breadcrumb = self._breadcrumb_for_section(
            domain_id,
            domain_title,
            document,
            structure,
            section,
        ) if section else self._base_breadcrumb(domain_id, domain_title, document)
        return WorkspaceSourceContext(
            node_id=node_id,
            kind="chunk",
            title=title,
            domain_id=domain_id,
            breadcrumb=[
                *breadcrumb,
                WorkspaceContextBreadcrumbItem(id=node_id, kind="chunk", title=title),
            ],
            document=self._document_payload(document),
            section_id=chunk.section_id,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            chunk_id=chunk.chunk_id,
            summary=self._page_range_summary("Exact source chunk", chunk.page_start, chunk.page_end),
            text=chunk.text,
            assets=[self._asset_payload(asset) for asset in assets],
            metadata=chunk.metadata,
        )

    def _asset_context(
        self,
        *,
        domain_id: str,
        domain_title: str,
        node_id: str,
        document: DocumentRow,
        structure: DocumentStructure,
        asset_id: str,
    ) -> WorkspaceSourceContext:
        asset = next((item for item in structure.assets if item.asset_id == asset_id), None)
        if asset is None:
            raise not_found("Document assets not found")

        nearby_chunks = [
            chunk
            for chunk in structure.source_chunks
            if chunk.chunk_id == asset.chunk_id
            or asset.asset_id in chunk.asset_ids
            or (asset.page_number is not None and self._chunk_in_page(chunk, asset.page_number))
            or (asset.section_id is not None and chunk.section_id == asset.section_id)
        ]
        title = asset.caption or f"{asset.asset_type.replace('_', ' ').title()} {asset.asset_id}"
        nearby_text = (
            asset.nearby_text
            or asset.generated_description
            or asset.ocr_text
            or "\n\n".join(chunk.text for chunk in nearby_chunks if chunk.text)
        )
        return WorkspaceSourceContext(
            node_id=node_id,
            kind="asset",
            title=title,
            domain_id=domain_id,
            breadcrumb=[
                *self._base_breadcrumb(domain_id, domain_title, document),
                WorkspaceContextBreadcrumbItem(id=node_id, kind="asset", title=title),
            ],
            document=self._document_payload(document),
            section_id=asset.section_id,
            page_number=asset.page_number,
            asset_id=asset.asset_id,
            summary="Document asset context.",
            text=self._truncate_text(nearby_text),
            assets=[self._asset_payload(asset)],
            metadata={
                "block_id": asset.block_id,
                "chunk_id": asset.chunk_id,
                "content_hash": asset.content_hash,
            },
        )

    def _base_breadcrumb(
        self,
        domain_id: str,
        domain_title: str,
        document: DocumentRow,
    ) -> list[WorkspaceContextBreadcrumbItem]:
        return [
            WorkspaceContextBreadcrumbItem(
                id=f"domain:{domain_id}",
                kind="domain",
                title=domain_title,
            ),
            WorkspaceContextBreadcrumbItem(
                id=f"document:{document.id}",
                kind="document",
                title=document.filename,
            ),
        ]

    def _breadcrumb_for_section(
        self,
        domain_id: str,
        domain_title: str,
        document: DocumentRow,
        structure: DocumentStructure,
        section: DocumentSection,
    ) -> list[WorkspaceContextBreadcrumbItem]:
        sections_by_id = {item.section_id: item for item in structure.sections}
        chain: list[DocumentSection] = []
        current: DocumentSection | None = section
        seen: set[str] = set()
        while current and current.section_id not in seen:
            seen.add(current.section_id)
            chain.append(current)
            current = sections_by_id.get(current.parent_section_id or "")
        chain.reverse()
        return [
            *self._base_breadcrumb(domain_id, domain_title, document),
            *[
                WorkspaceContextBreadcrumbItem(
                    id=f"section:{document.id}:{item.section_id}",
                    kind="section",
                    title=item.title,
                )
                for item in chain
            ],
        ]

    def _document_payload(self, document: DocumentRow) -> WorkspaceContextDocument:
        return WorkspaceContextDocument(
            document_id=document.id,
            title=document.filename,
            filename=document.filename,
            content_type=document.content_type,
            status=document.status,
            source_path=document.storage_path,
        )

    def _asset_payload(self, asset: DocumentAsset) -> WorkspaceContextAsset:
        title = asset.caption or f"{asset.asset_type.replace('_', ' ').title()} {asset.asset_id}"
        return WorkspaceContextAsset(
            asset_id=asset.asset_id,
            document_id=asset.document_id,
            asset_type=asset.asset_type,
            title=title,
            caption=asset.caption,
            page_number=asset.page_number,
            section_id=asset.section_id,
            url=document_asset_url(asset.document_id, asset.asset_id),
            thumbnail_url=document_asset_thumbnail_url(
                asset.document_id,
                asset.asset_id,
                has_thumbnail=bool(asset.thumbnail_path),
            ),
            mime_type=asset.mime_type,
            metadata={
                "block_id": asset.block_id,
                "chunk_id": asset.chunk_id,
                "content_hash": asset.content_hash,
            },
        )

    def _first_text(self, structure: DocumentStructure) -> str:
        for chunk in structure.source_chunks:
            if chunk.text:
                return chunk.text
        for page in structure.pages:
            if page.text:
                return page.text
        return ""

    def _section_for_chunk(
        self,
        structure: DocumentStructure,
        chunk: SourceChunk,
    ) -> DocumentSection | None:
        if not chunk.section_id:
            return None
        return next((item for item in structure.sections if item.section_id == chunk.section_id), None)

    def _chunk_title(self, chunk: SourceChunk) -> str:
        snippet = " ".join(chunk.text.split())[:80]
        return snippet or f"Chunk {chunk.chunk_id}"

    def _page_range_summary(self, label: str, start: int | None, end: int | None) -> str:
        if start is None:
            return f"{label}."
        if end and end != start:
            return f"{label}, pages {start}-{end}."
        return f"{label}, page {start}."

    def _safe_page_metadata(self, page: DocumentPage) -> dict:
        return {key: value for key, value in page.metadata.items() if key != "text"}

    def _chunk_in_page(self, chunk: SourceChunk, page_number: int) -> bool:
        if chunk.page_start is None:
            return False
        return chunk.page_start <= page_number <= (chunk.page_end or chunk.page_start)

    def _truncate_text(self, text: str | None) -> str | None:
        if not text:
            return None
        return text[:TEXT_LIMIT]

    def _missing_detail(self, kind: WorkspaceContextNodeKind) -> str:
        if kind == "section":
            return "Document section not found"
        if kind == "page":
            return "Page not found"
        if kind == "chunk":
            return "Document source chunk not found"
        if kind == "asset":
            return "Document assets not found"
        return "Workspace source context not found"
