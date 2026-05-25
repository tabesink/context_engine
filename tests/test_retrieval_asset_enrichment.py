from uuid import UUID

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.document_processing.models import DocumentAsset, DocumentStructure, SourceChunk
from app.domain.models import Evidence, RetrievalMode, RetrievalResult, UserRole
from app.schemas.query import QueryRequest
from app.services.retrieval_service import RetrievalService
from app.storage import tables  # noqa: F401
from app.storage.db import Base
from app.storage.repositories.document_processing import DocumentProcessingRepository


class FakeStrategy:
    def retrieve(self, **kwargs) -> RetrievalResult:
        del kwargs
        document_id = UUID("11111111-1111-4111-8111-111111111111")
        return RetrievalResult(
            query="show diagram",
            mode=RetrievalMode.SEMANTIC,
            evidence=[
                Evidence(
                    id="lightrag-evidence-1",
                    document_id=document_id,
                    source_engine="lightrag",
                    text="See figure 1.",
                    metadata={"source_chunk_id": "chunk-1"},
                )
            ],
        )


class FakeChunkMetadataStrategy:
    def retrieve(self, **kwargs) -> RetrievalResult:
        del kwargs
        document_id = UUID("11111111-1111-4111-8111-111111111111")
        return RetrievalResult(
            query="show diagram",
            mode=RetrievalMode.SEMANTIC,
            evidence=[
                Evidence(
                    id="lightrag-evidence-1",
                    document_id=document_id,
                    source_engine="lightrag",
                    text="See figure 1.",
                    metadata={"chunk_id": "chunk-1"},
                )
            ],
        )


class FakeAssetMetadataStrategy:
    def retrieve(self, **kwargs) -> RetrievalResult:
        del kwargs
        document_id = UUID("11111111-1111-4111-8111-111111111111")
        return RetrievalResult(
            query="show hydraulic diagram",
            mode=RetrievalMode.SEMANTIC,
            evidence=[
                Evidence(
                    id="lightrag-evidence-1",
                    document_id=document_id,
                    source_engine="lightrag",
                    text="Hydraulic circuit details.",
                    metadata={"chunk_id": "chunk-1", "asset_ids": ["asset-2", "asset-1"]},
                )
            ],
        )


def _retrieval_service(session, strategy) -> RetrievalService:
    return RetrievalService(
        session,
        local_strategy=strategy,
        remote_strategy=strategy,
    )


def test_retrieval_response_can_include_assets_linked_to_source_chunks() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id="11111111-1111-4111-8111-111111111111",
                source_file="manual.pdf",
                source_chunks=[
                    SourceChunk(
                        chunk_id="chunk-1",
                        document_id="11111111-1111-4111-8111-111111111111",
                        block_ids=["block-1"],
                        text="See figure 1.",
                        asset_ids=["asset-1"],
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id="asset-1",
                        document_id="11111111-1111-4111-8111-111111111111",
                        asset_type="figure",
                        storage_path="documents/doc/assets/asset-1.png",
                        thumbnail_path="documents/doc/assets/asset-1_thumb.png",
                        content_hash="hash-1",
                        chunk_id="chunk-1",
                        caption="Figure 1",
                    )
                ],
            )
        )
        user = tables.UserRow(id="user-1", email="u@example.com", password_hash="x", role=UserRole.USER.value)
        response = _retrieval_service(session, FakeStrategy()).retrieve(
            request=QueryRequest(
                query="show diagram",
                mode=RetrievalMode.SEMANTIC,
                include_assets=True,
            ),
            user=user,
        )

    assert response.assets[0].asset_id == "asset-1"
    assert response.assets[0].thumbnail_url.endswith("/documents/11111111-1111-4111-8111-111111111111/assets/asset-1/thumbnail")


def test_retrieval_response_resolves_assets_from_lightrag_chunk_metadata() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id="11111111-1111-4111-8111-111111111111",
                source_file="manual.pdf",
                source_chunks=[
                    SourceChunk(
                        chunk_id="chunk-1",
                        document_id="11111111-1111-4111-8111-111111111111",
                        block_ids=["block-1"],
                        text="See figure 1.",
                        asset_ids=["asset-1"],
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id="asset-1",
                        document_id="11111111-1111-4111-8111-111111111111",
                        asset_type="figure",
                        storage_path="documents/doc/assets/asset-1.png",
                        content_hash="hash-1",
                        chunk_id="chunk-1",
                    )
                ],
            )
        )
        user = tables.UserRow(id="user-1", email="u@example.com", password_hash="x", role=UserRole.USER.value)
        response = _retrieval_service(session, FakeChunkMetadataStrategy()).retrieve(
            request=QueryRequest(
                query="show diagram",
                mode=RetrievalMode.SEMANTIC,
                include_assets=True,
            ),
            user=user,
        )

    assert response.assets[0].asset_id == "asset-1"


def test_retrieval_asset_enrichment_ranks_metadata_assets_and_applies_limit() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id="11111111-1111-4111-8111-111111111111",
                source_file="manual.pdf",
                source_chunks=[
                    SourceChunk(
                        chunk_id="chunk-1",
                        document_id="11111111-1111-4111-8111-111111111111",
                        block_ids=["block-1"],
                        text="Hydraulic circuit details.",
                        page_start=3,
                        page_end=3,
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id="asset-1",
                        document_id="11111111-1111-4111-8111-111111111111",
                        asset_type="figure",
                        storage_path="documents/doc/assets/asset-1.png",
                        content_hash="hash-1",
                        caption="Figure 1. Electrical wiring",
                        page_number=3,
                    ),
                    DocumentAsset(
                        asset_id="asset-2",
                        document_id="11111111-1111-4111-8111-111111111111",
                        asset_type="figure",
                        storage_path="documents/doc/assets/asset-2.png",
                        content_hash="hash-2",
                        caption="Figure 2. Hydraulic circuit diagram",
                        page_number=4,
                    ),
                ],
            )
        )
        user = tables.UserRow(id="user-1", email="u@example.com", password_hash="x", role=UserRole.USER.value)
        response = _retrieval_service(session, FakeAssetMetadataStrategy()).retrieve(
            request=QueryRequest(
                query="show hydraulic diagram",
                mode=RetrievalMode.SEMANTIC,
                include_assets=True,
                max_assets=1,
            ),
            user=user,
        )

    assert [asset.asset_id for asset in response.assets] == ["asset-2"]


def test_retrieval_asset_enrichment_is_opt_in() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        user = tables.UserRow(id="user-1", email="u@example.com", password_hash="x", role=UserRole.USER.value)
        response = _retrieval_service(session, FakeStrategy()).retrieve(
            request=QueryRequest(
                query="show diagram",
                mode=RetrievalMode.SEMANTIC,
                include_assets=False,
            ),
            user=user,
        )

    assert response.evidence[0].evidence_id == "lightrag-evidence-1"
    assert response.assets == []
