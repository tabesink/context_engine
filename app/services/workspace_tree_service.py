from app.document_processing.models import DocumentAsset, DocumentPage, DocumentSection, SourceChunk
from app.schemas.workspace_tree import WorkspaceTreeNode, WorkspaceTreeResponse
from app.services.asset_urls import document_asset_thumbnail_url, document_asset_url
from app.services.document_access_policy import DocumentAccessPolicy
from app.services.lightrag_domain_registry import LightRAGDomainRegistry
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage.repositories.documents import DocumentRepository
from app.storage.tables import DocumentRow, UserRow


class WorkspaceTreeService:
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

    def build_for_domain(
        self,
        *,
        domain_id: str,
        user: UserRow,
        depth: int | None = None,
        include_assets: bool = True,
    ) -> WorkspaceTreeResponse:
        domain = self.domain_registry.validate_available(domain_id)
        documents = DocumentAccessPolicy(self.documents).filter_readable_documents(
            user,
            self.documents.list_ready_by_lightrag_domain(domain_id),
        )

        root = WorkspaceTreeNode(
            id=f"domain:{domain.id}",
            kind="domain",
            title=domain.display_name or domain.id,
            children=[
                self._document_node(
                    document,
                    current_depth=1,
                    max_depth=depth,
                    include_assets=include_assets,
                )
                for document in documents
                if self._can_include_children(current_depth=0, max_depth=depth)
            ],
            metadata={
                "is_healthy": domain.is_healthy,
                "is_default": domain.is_default,
            },
        )
        return WorkspaceTreeResponse(
            domain_id=domain.id,
            display_name=domain.display_name,
            document_count=len(root.children),
            root=root,
        )

    def _document_node(
        self,
        document: DocumentRow,
        *,
        current_depth: int,
        max_depth: int | None,
        include_assets: bool,
    ) -> WorkspaceTreeNode:
        structure = self.processing.get_structure(document.id, source_file=document.storage_path)
        metadata = {"structure_available": structure is not None}
        if structure is None or not self._can_include_children(
            current_depth=current_depth,
            max_depth=max_depth,
        ):
            children: list[WorkspaceTreeNode] = []
        else:
            children = self._structure_nodes(
                document_id=document.id,
                sections=structure.sections,
                pages=structure.pages,
                chunks=structure.source_chunks,
                assets=structure.assets,
                current_depth=current_depth + 1,
                max_depth=max_depth,
                include_assets=include_assets,
            )

        return WorkspaceTreeNode(
            id=f"document:{document.id}",
            kind="document",
            title=document.filename,
            document_id=document.id,
            status=document.status,
            filename=document.filename,
            content_type=document.content_type,
            children=children,
            metadata=metadata,
        )

    def _structure_nodes(
        self,
        *,
        document_id: str,
        sections: list[DocumentSection],
        pages: list[DocumentPage],
        chunks: list[SourceChunk],
        assets: list[DocumentAsset],
        current_depth: int,
        max_depth: int | None,
        include_assets: bool,
    ) -> list[WorkspaceTreeNode]:
        placed_chunks: set[str] = set()
        placed_assets: set[str] = set()

        if sections:
            nodes = self._section_nodes(
                document_id=document_id,
                sections=sections,
                pages=pages,
                chunks=chunks,
                assets=assets,
                placed_chunks=placed_chunks,
                placed_assets=placed_assets,
                current_depth=current_depth,
                max_depth=max_depth,
                include_assets=include_assets,
            )
        elif pages:
            nodes = [
                self._page_node(
                    document_id=document_id,
                    page=page,
                    chunks=chunks,
                    assets=assets,
                    placed_chunks=placed_chunks,
                    placed_assets=placed_assets,
                    current_depth=current_depth,
                    max_depth=max_depth,
                    include_assets=include_assets,
                )
                for page in sorted(pages, key=lambda item: item.page_number)
            ]
        else:
            nodes = []

        nodes.extend(
            self._loose_reference_nodes(
                document_id=document_id,
                chunks=chunks,
                assets=assets,
                placed_chunks=placed_chunks,
                placed_assets=placed_assets,
                current_depth=current_depth,
                max_depth=max_depth,
                include_assets=include_assets,
            )
        )
        return nodes

    def _section_nodes(
        self,
        *,
        document_id: str,
        sections: list[DocumentSection],
        pages: list[DocumentPage],
        chunks: list[SourceChunk],
        assets: list[DocumentAsset],
        placed_chunks: set[str],
        placed_assets: set[str],
        current_depth: int,
        max_depth: int | None,
        include_assets: bool,
    ) -> list[WorkspaceTreeNode]:
        by_parent: dict[str | None, list[DocumentSection]] = {}
        for section in sections:
            by_parent.setdefault(section.parent_section_id, []).append(section)

        def build(parent_id: str | None, node_depth: int) -> list[WorkspaceTreeNode]:
            nodes: list[WorkspaceTreeNode] = []
            for section in by_parent.get(parent_id, []):
                child_sections = (
                    build(section.section_id, node_depth + 1)
                    if self._can_include_children(
                        current_depth=node_depth,
                        max_depth=max_depth,
                    )
                    else []
                )
                child_ranges = [
                    (child.page_start, child.page_end)
                    for child in by_parent.get(section.section_id, [])
                    if child.page_start is not None
                ]
                child_pages = [
                    self._page_node(
                        document_id=document_id,
                        page=page,
                        chunks=chunks,
                        assets=assets,
                        placed_chunks=placed_chunks,
                        placed_assets=placed_assets,
                        current_depth=node_depth + 1,
                        max_depth=max_depth,
                        include_assets=include_assets,
                    )
                    for page in sorted(pages, key=lambda item: item.page_number)
                    if self._can_include_children(
                        current_depth=node_depth,
                        max_depth=max_depth,
                    )
                    and self._page_in_section(page, section)
                    and not self._page_in_ranges(page.page_number, child_ranges)
                ]
                direct_chunks = [
                    self._chunk_node(document_id=document_id, chunk=chunk)
                    for chunk in chunks
                    if self._can_include_children(
                        current_depth=node_depth,
                        max_depth=max_depth,
                    )
                    and chunk.section_id == section.section_id
                    and chunk.chunk_id not in placed_chunks
                ]
                direct_assets = [
                    self._asset_node(document_id=document_id, asset=asset)
                    for asset in assets
                    if include_assets
                    and self._can_include_children(
                        current_depth=node_depth,
                        max_depth=max_depth,
                    )
                    and asset.section_id == section.section_id
                    and asset.asset_id not in placed_assets
                ]
                placed_chunks.update(node.chunk_id for node in direct_chunks if node.chunk_id)
                placed_assets.update(node.asset_id for node in direct_assets if node.asset_id)
                nodes.append(
                    WorkspaceTreeNode(
                        id=f"section:{document_id}:{section.section_id}",
                        kind="section",
                        title=section.title,
                        document_id=document_id,
                        section_id=section.section_id,
                        page_start=section.page_start,
                        page_end=section.page_end,
                        children=child_sections + child_pages + direct_chunks + direct_assets,
                        metadata={"level": section.level},
                    )
                )
            return nodes

        return build(None, current_depth)

    def _page_node(
        self,
        *,
        document_id: str,
        page: DocumentPage,
        chunks: list[SourceChunk],
        assets: list[DocumentAsset],
        placed_chunks: set[str],
        placed_assets: set[str],
        current_depth: int,
        max_depth: int | None,
        include_assets: bool,
    ) -> WorkspaceTreeNode:
        page_chunks = [
            self._chunk_node(document_id=document_id, chunk=chunk)
            for chunk in chunks
            if self._can_include_children(current_depth=current_depth, max_depth=max_depth)
            and chunk.chunk_id not in placed_chunks
            and self._chunk_in_page(chunk, page.page_number)
        ]
        page_assets = [
            self._asset_node(document_id=document_id, asset=asset)
            for asset in assets
            if include_assets
            and self._can_include_children(current_depth=current_depth, max_depth=max_depth)
            and asset.asset_id not in placed_assets
            and asset.page_number == page.page_number
        ]
        placed_chunks.update(node.chunk_id for node in page_chunks if node.chunk_id)
        placed_assets.update(node.asset_id for node in page_assets if node.asset_id)
        metadata = {key: value for key, value in page.metadata.items() if key != "text"}
        return WorkspaceTreeNode(
            id=f"page:{document_id}:{page.page_number}",
            kind="page",
            title=f"Page {page.page_number}",
            document_id=document_id,
            page_number=page.page_number,
            children=page_chunks + page_assets,
            metadata=metadata,
        )

    def _loose_reference_nodes(
        self,
        *,
        document_id: str,
        chunks: list[SourceChunk],
        assets: list[DocumentAsset],
        placed_chunks: set[str],
        placed_assets: set[str],
        current_depth: int,
        max_depth: int | None,
        include_assets: bool,
    ) -> list[WorkspaceTreeNode]:
        nodes: list[WorkspaceTreeNode] = []
        if not self._can_include_children(current_depth=current_depth - 1, max_depth=max_depth):
            return nodes
        for chunk in chunks:
            if chunk.chunk_id not in placed_chunks and self._can_include_loose_chunk(
                chunk,
                max_depth=max_depth,
            ):
                nodes.append(self._chunk_node(document_id=document_id, chunk=chunk))
        if include_assets:
            for asset in assets:
                if asset.asset_id not in placed_assets and self._can_include_loose_asset(
                    asset,
                    max_depth=max_depth,
                ):
                    nodes.append(self._asset_node(document_id=document_id, asset=asset))
        return nodes

    def _chunk_node(self, *, document_id: str, chunk: SourceChunk) -> WorkspaceTreeNode:
        snippet = " ".join(chunk.text.split())[:80]
        return WorkspaceTreeNode(
            id=f"chunk:{document_id}:{chunk.chunk_id}",
            kind="chunk",
            title=snippet or f"Chunk {chunk.chunk_id}",
            document_id=document_id,
            section_id=chunk.section_id,
            chunk_id=chunk.chunk_id,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            metadata={"asset_ids": chunk.asset_ids},
        )

    def _asset_node(self, *, document_id: str, asset: DocumentAsset) -> WorkspaceTreeNode:
        title = asset.caption or f"{asset.asset_type.replace('_', ' ').title()} {asset.asset_id}"
        thumbnail_url = (
            document_asset_thumbnail_url(document_id, asset.asset_id)
            if asset.thumbnail_path
            else None
        )
        return WorkspaceTreeNode(
            id=f"asset:{document_id}:{asset.asset_id}",
            kind="asset",
            title=title,
            document_id=document_id,
            section_id=asset.section_id,
            page_number=asset.page_number,
            asset_id=asset.asset_id,
            asset_type=asset.asset_type,
            thumbnail_url=thumbnail_url,
            metadata={
                "url": document_asset_url(document_id, asset.asset_id),
                "caption": asset.caption,
                "mime_type": asset.mime_type,
            },
        )

    def _page_in_section(self, page: DocumentPage, section: DocumentSection) -> bool:
        if section.page_start is None:
            return False
        page_end = section.page_end or section.page_start
        return section.page_start <= page.page_number <= page_end

    def _page_in_ranges(
        self,
        page_number: int,
        ranges: list[tuple[int | None, int | None]],
    ) -> bool:
        for start, end in ranges:
            if start is None:
                continue
            if start <= page_number <= (end or start):
                return True
        return False

    def _chunk_in_page(self, chunk: SourceChunk, page_number: int) -> bool:
        if chunk.page_start is None:
            return False
        return chunk.page_start <= page_number <= (chunk.page_end or chunk.page_start)

    def _can_include_children(self, *, current_depth: int, max_depth: int | None) -> bool:
        return max_depth is None or current_depth < max_depth

    def _can_include_loose_chunk(
        self,
        chunk: SourceChunk,
        *,
        max_depth: int | None,
    ) -> bool:
        if max_depth is None:
            return True
        return chunk.section_id is None and chunk.page_start is None

    def _can_include_loose_asset(
        self,
        asset: DocumentAsset,
        *,
        max_depth: int | None,
    ) -> bool:
        if max_depth is None:
            return True
        return asset.section_id is None and asset.page_number is None
