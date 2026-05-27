import os
from types import SimpleNamespace

os.environ.setdefault("DATABASE_URL", "sqlite:///./.data/test_context_engine.db")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi import HTTPException

from app.document_processing.models import (
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
    SourceChunk,
)
from app.domain.models import DocumentStatus
from app.services.lightrag_domain_lifecycle_service import LightRAGDomainLifecycleService
from app.services.workspace_context_service import (
    WorkspaceContextService,
    parse_workspace_node_id,
    resolve_document_domain_id,
)


class FakeDomainRegistry:
    def validate_available(self, domain_id: str):
        return SimpleNamespace(
            id=domain_id,
            display_name="Manuals",
            is_healthy=True,
            is_default=False,
            status="ready",
        )


class FakeDocuments:
    def __init__(self, document):
        self.document = document

    def get(self, document_id: str):
        if document_id == self.document.id:
            return self.document
        return None


class FakeProcessing:
    def __init__(self, structure: DocumentStructure | None):
        self.structure = structure

    def get_structure(self, document_id: str, *, source_file: str = ""):
        del document_id, source_file
        return self.structure

    def count_by_document_ids(self, document_ids: list[str]) -> dict[str, int]:
        del document_ids
        if not self.structure:
            return {"pages": 0, "sections": 0, "blocks": 0, "chunks": 0, "assets": 0}
        return {
            "pages": len(self.structure.pages),
            "sections": len(self.structure.sections),
            "blocks": len(self.structure.blocks),
            "chunks": len(self.structure.source_chunks),
            "assets": len(self.structure.assets),
        }


@pytest.fixture(autouse=True)
def _active_domains(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(LightRAGDomainLifecycleService, "is_active", lambda _self, _domain_id: True)


def test_parse_workspace_node_id_accepts_current_tree_id_contract() -> None:
    assert parse_workspace_node_id("domain:manuals").kind == "domain"
    assert parse_workspace_node_id("document:doc-1").document_id == "doc-1"

    section = parse_workspace_node_id("section:doc-1:intro")
    assert section.kind == "section"
    assert section.document_id == "doc-1"
    assert section.value == "intro"

    assert parse_workspace_node_id("page:doc-1:12").value == "12"
    assert parse_workspace_node_id("chunk:doc-1:chunk-1").value == "chunk-1"
    assert parse_workspace_node_id("asset:doc-1:asset-1").value == "asset-1"


def test_parse_workspace_node_id_rejects_invalid_ids() -> None:
    with pytest.raises(HTTPException) as exc_info:
        parse_workspace_node_id("chunk:missing-value")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid workspace node id"


def test_workspace_context_service_builds_exact_chunk_context() -> None:
    service = _service()

    context = service.build_for_node(
        domain_id="manuals",
        node_id="chunk:doc-1:chunk-1",
        user=SimpleNamespace(),
    )

    assert context.kind == "chunk"
    assert context.document is not None
    assert context.document.document_id == "doc-1"
    assert context.section_id == "intro"
    assert context.page_start == 2
    assert context.page_end == 3
    assert context.text == "Exact chunk text for the selected source."
    assert [asset.asset_id for asset in context.assets] == ["asset-1"]
    assert [item.kind for item in context.breadcrumb] == ["domain", "document", "section", "chunk"]


def test_workspace_context_service_builds_section_context_with_linked_assets() -> None:
    service = _service()

    context = service.build_for_node(
        domain_id="manuals",
        node_id="section:doc-1:intro",
        user=SimpleNamespace(),
    )

    assert context.kind == "section"
    assert context.title == "Introduction"
    assert context.text == "Exact chunk text for the selected source."
    assert context.assets[0].asset_id == "asset-1"


def test_workspace_context_service_rejects_cross_domain_documents() -> None:
    service = _service(domain_id="other-domain")

    with pytest.raises(HTTPException) as exc_info:
        service.build_for_node(
            domain_id="manuals",
            node_id="document:doc-1",
            user=SimpleNamespace(),
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Document not found"


def test_resolve_document_domain_id_uses_column_before_metadata() -> None:
    document = SimpleNamespace(
        lightrag_domain_id="column-domain",
        meta={"lightrag": {"domain_id": "metadata-domain"}},
    )

    assert resolve_document_domain_id(document) == "column-domain"


def _service(domain_id: str = "manuals") -> WorkspaceContextService:
    document = SimpleNamespace(
        id="doc-1",
        lightrag_domain_id=domain_id,
        filename="manual.pdf",
        content_type="application/pdf",
        storage_path=".data/uploads/manual.pdf",
        status=DocumentStatus.READY.value,
        meta={"lightrag": {"domain_id": domain_id}},
    )
    return WorkspaceContextService(
        documents=FakeDocuments(document),
        processing=FakeProcessing(_structure()),
        domain_registry=FakeDomainRegistry(),
    )


def _structure() -> DocumentStructure:
    return DocumentStructure(
        document_id="doc-1",
        source_file=".data/uploads/manual.pdf",
        pages=[DocumentPage(page_number=2, text="Page two text")],
        sections=[
            DocumentSection(
                section_id="intro",
                document_id="doc-1",
                title="Introduction",
                level=1,
                page_start=2,
                page_end=3,
            )
        ],
        blocks=[
            DocumentBlock(
                block_id="block-1",
                document_id="doc-1",
                section_id="intro",
                type="paragraph",
                text="Exact chunk text for the selected source.",
                page_start=2,
                page_end=3,
            )
        ],
        source_chunks=[
            SourceChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                section_id="intro",
                block_ids=["block-1"],
                text="Exact chunk text for the selected source.",
                page_start=2,
                page_end=3,
                asset_ids=["asset-1"],
            )
        ],
        assets=[
            DocumentAsset(
                asset_id="asset-1",
                document_id="doc-1",
                section_id="intro",
                block_id="block-1",
                chunk_id="chunk-1",
                asset_type="figure",
                storage_path="documents/doc-1/assets/figure.png",
                thumbnail_path="documents/doc-1/assets/figure-thumb.png",
                mime_type="image/png",
                content_hash="asset-hash",
                page_number=2,
                caption="Figure 1",
            )
        ],
    )
