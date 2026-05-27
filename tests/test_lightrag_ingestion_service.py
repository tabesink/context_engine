import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["INDEX_JOBS_INLINE"] = "true"
Path(".data").mkdir(parents=True, exist_ok=True)
Path(".data/test_context_engine.db").unlink(missing_ok=True)

from app.document_processing.artifacts import DocumentProcessingArtifactStore  # noqa: E402
from app.document_processing.models import (  # noqa: E402
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentStructure,
)
from app.document_processing.storage_paths import DocumentStoragePaths  # noqa: E402
from app.domain.models import DocumentStatus  # noqa: E402
from app.lightrag_deploy.manifest import DomainManifestStore  # noqa: E402
from app.lightrag_deploy.models import DomainEmbeddingSnapshot, LightRAGDomain  # noqa: E402
from app.services.lightrag_ingestion_service import LightRAGIngestionService  # noqa: E402
from app.storage import tables  # noqa: E402, F401
from app.storage.db import Base  # noqa: E402
from app.storage.repositories.document_processing import DocumentProcessingRepository  # noqa: E402
from app.storage.repositories.documents import DocumentRepository  # noqa: E402
from app.storage.tables import DocumentSourceChunkRow  # noqa: E402


class FakeLock:
    def __init__(self) -> None:
        self.acquired = False
        self.released = False

    def acquire(self) -> bool:
        self.acquired = True
        return True

    def release(self) -> None:
        self.released = True


class CapturingChunkAdapter:
    def __init__(self) -> None:
        self.ingested_domain: str | None = None
        self.ingested_chunks = []

    def ingest_source_chunks(self, *, domain: str, chunks: list) -> dict:
        self.ingested_domain = domain
        self.ingested_chunks = chunks
        return {"track_id": "track-chunks", "status": "ready", "message": "chunks accepted"}


class CapturingRawUploadAdapter:
    def __init__(self) -> None:
        self.uploaded = None
        self.ingested_chunks = None

    def ingest_source_chunks(self, *, domain: str, chunks: list) -> dict:
        self.ingested_chunks = {"domain": domain, "chunks": chunks}
        return {"track_id": "unexpected", "status": "ready"}

    def upload_document(self, **kwargs) -> dict:
        self.uploaded = kwargs
        return {"document_id": "remote-doc", "track_id": "track-raw", "status": "ready"}


class FakeStructureParser:
    def __init__(self, structure: DocumentStructure) -> None:
        self.structure = structure

    def parse(self, *, document_id: str, source_path: Path) -> DocumentStructure:
        del document_id, source_path
        return self.structure


class FailingStructureParser:
    def parse(self, *, document_id: str, source_path: Path) -> DocumentStructure:
        del document_id, source_path
        raise RuntimeError("parser exploded")


def _artifact_store(tmp_path: Path) -> DocumentProcessingArtifactStore:
    return DocumentProcessingArtifactStore(
        storage_paths=DocumentStoragePaths(storage_root=tmp_path),
    )


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        yield session


def test_lightrag_ingestion_persists_document_structure_and_ingests_source_chunks(
    tmp_path: Path,
    session: Session,
) -> None:
    upload_path = tmp_path / "manual.txt"
    upload_path.write_text("# Safety\nWear eye protection.\n\n# Service\nDisconnect power.", encoding="utf-8")
    lock = FakeLock()
    adapter = CapturingChunkAdapter()

    document = DocumentRepository(session).create(
        owner_id=None,
        filename="manual.txt",
        content_type="text/plain",
        storage_path=str(upload_path),
        metadata={
            "semantic_engine": "lightrag",
            "lightrag": {"domain_id": "fatigue", "status": "queued"},
        },
        status=DocumentStatus.INDEXING,
    )

    LightRAGIngestionService(
        session,
        adapter_factory=lambda domain_id: adapter,
        lock_factory=lambda domain_id: lock,
        artifact_store=_artifact_store(tmp_path),
    ).ingest_document(document.id)

    refreshed = DocumentRepository(session).get(document.id)
    ingested_chunk = adapter.ingested_chunks[0]
    source_chunk = DocumentProcessingRepository(session).get_source_chunk(
        document.id,
        ingested_chunk.chunk_id,
    )

    assert lock.acquired is True
    assert lock.released is True
    assert refreshed is not None
    assert refreshed.status == DocumentStatus.READY.value
    assert refreshed.meta["lightrag"]["track_id"] == "track-chunks"
    assert refreshed.meta["lightrag"]["status"] == "ready"
    assert source_chunk is not None
    assert source_chunk.document_id == document.id
    assert source_chunk.section_id == f"{document.id}-sec-1"
    assert source_chunk.block_ids == [f"{document.id}-block-1"]
    assert source_chunk.page_start == 1
    assert source_chunk.page_end == 1
    assert source_chunk.asset_ids == []
    assert adapter.ingested_domain == "fatigue"
    assert len(adapter.ingested_chunks) == 2
    assert ingested_chunk.chunk_id == f"{document.id}-source-chunk-1"
    structure_manifest = tmp_path / "documents" / document.id / "manifest" / "document_structure.json"
    assert json.loads(structure_manifest.read_text(encoding="utf-8"))["document_id"] == document.id


def test_lightrag_ingestion_builds_chunks_with_asset_metadata(
    tmp_path: Path,
    session: Session,
) -> None:
    upload_path = tmp_path / "manual.txt"
    upload_path.write_text("See figure 1.", encoding="utf-8")
    lock = FakeLock()
    adapter = CapturingChunkAdapter()
    document = DocumentRepository(session).create(
        owner_id=None,
        filename="manual.txt",
        content_type="text/plain",
        storage_path=str(upload_path),
        metadata={
            "semantic_engine": "lightrag",
            "lightrag": {"domain_id": "fatigue", "status": "queued"},
        },
        status=DocumentStatus.INDEXING,
    )
    section_id = f"{document.id}-sec-1"
    block_id = f"{document.id}-block-1"
    asset_id = f"{document.id}-asset-1"

    LightRAGIngestionService(
        session,
        adapter_factory=lambda domain_id: adapter,
        lock_factory=lambda domain_id: lock,
        artifact_store=_artifact_store(tmp_path),
        structure_parser=FakeStructureParser(
            DocumentStructure(
                document_id=document.id,
                source_file=str(upload_path),
                pages=[DocumentPage(page_number=1, text="See figure 1.")],
                blocks=[
                    DocumentBlock(
                        block_id=block_id,
                        document_id=document.id,
                        section_id=section_id,
                        type="figure",
                        text="Figure 1. Safety envelope.",
                        page_start=1,
                        page_end=1,
                        asset_ids=[asset_id],
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id=asset_id,
                        document_id=document.id,
                        asset_type="figure",
                        storage_path=f"documents/{document.id}/assets/figure.png",
                        thumbnail_path=f"documents/{document.id}/assets/figure_thumb.png",
                        content_hash="hash-1",
                        block_id=block_id,
                        page_number=1,
                    )
                ],
            )
        ),
    ).ingest_document(document.id)

    chunk = adapter.ingested_chunks[0]
    stored_asset = DocumentProcessingRepository(session).list_assets_for_chunks([chunk.chunk_id])[0]
    assert chunk.asset_ids == [asset_id]
    assert stored_asset.chunk_id == chunk.chunk_id
    assert stored_asset.thumbnail_path == f"documents/{document.id}/assets/figure_thumb.png"


def test_lightrag_ingestion_does_not_refine_toc_and_ingests_chunks_directly(
    tmp_path: Path,
    session: Session,
) -> None:
    upload_path = tmp_path / "manual.txt"
    upload_path.write_text("# Safety\nWear eye protection.", encoding="utf-8")
    lock = FakeLock()
    adapter = CapturingChunkAdapter()
    document = DocumentRepository(session).create(
        owner_id=None,
        filename="manual.txt",
        content_type="text/plain",
        storage_path=str(upload_path),
        metadata={
            "semantic_engine": "lightrag",
            "lightrag": {"domain_id": "fatigue", "status": "queued"},
        },
        status=DocumentStatus.INDEXING,
    )

    LightRAGIngestionService(
        session,
        adapter_factory=lambda domain_id: adapter,
        lock_factory=lambda domain_id: lock,
        artifact_store=_artifact_store(tmp_path),
        structure_parser=FakeStructureParser(
            DocumentStructure(
                document_id=document.id,
                source_file=str(upload_path),
                pages=[DocumentPage(page_number=1, text="Safety")],
                blocks=[
                    DocumentBlock(
                        block_id=f"{document.id}-block-1",
                        document_id=document.id,
                        type="paragraph",
                        text="Wear eye protection.",
                        page_start=1,
                        page_end=1,
                    )
                ],
            )
        ),
    ).ingest_document(document.id)

    assert adapter.ingested_chunks[0].section_id is None


def test_lightrag_ingestion_fails_when_pdf_structure_processing_is_unavailable(
    tmp_path: Path,
    session: Session,
) -> None:
    upload_path = tmp_path / "manual.pdf"
    upload_path.write_bytes(b"%PDF-1.7 fake pdf bytes")
    lock = FakeLock()
    adapter = CapturingRawUploadAdapter()
    document = DocumentRepository(session).create(
        owner_id=None,
        filename="manual.pdf",
        content_type="application/pdf",
        storage_path=str(upload_path),
        metadata={
            "semantic_engine": "lightrag",
            "lightrag": {"domain_id": "fatigue", "status": "queued"},
        },
        status=DocumentStatus.INDEXING,
    )

    with pytest.raises(ValueError, match="Structure-aware ingestion failed"):
        LightRAGIngestionService(
            session,
            adapter_factory=lambda domain_id: adapter,
            lock_factory=lambda domain_id: lock,
            artifact_store=_artifact_store(tmp_path),
        ).ingest_document(document.id)

    refreshed = DocumentRepository(session).get(document.id)
    source_chunk_count = session.query(DocumentSourceChunkRow).count()

    assert adapter.ingested_chunks is None
    assert adapter.uploaded is None
    assert source_chunk_count == 0
    assert refreshed is not None
    assert refreshed.status == DocumentStatus.FAILED.value
    assert refreshed.meta["lightrag"]["status"] == "failed"
    assert "Structure-aware ingestion failed" in refreshed.meta["lightrag"]["message"]


def test_lightrag_ingestion_fails_when_structure_parser_errors(
    tmp_path: Path,
    session: Session,
) -> None:
    upload_path = tmp_path / "manual.txt"
    upload_path.write_text("Hello world", encoding="utf-8")
    lock = FakeLock()
    adapter = CapturingChunkAdapter()
    document = DocumentRepository(session).create(
        owner_id=None,
        filename="manual.txt",
        content_type="text/plain",
        storage_path=str(upload_path),
        metadata={
            "semantic_engine": "lightrag",
            "lightrag": {"domain_id": "fatigue", "status": "queued"},
        },
        status=DocumentStatus.INDEXING,
    )

    with pytest.raises(ValueError, match="Structure-aware ingestion failed"):
        LightRAGIngestionService(
            session,
            adapter_factory=lambda domain_id: adapter,
            lock_factory=lambda domain_id: lock,
            artifact_store=_artifact_store(tmp_path),
            structure_parser=FailingStructureParser(),
        ).ingest_document(document.id)

    refreshed = DocumentRepository(session).get(document.id)
    assert refreshed is not None
    assert refreshed.status == DocumentStatus.FAILED.value
    assert refreshed.meta["lightrag"]["status"] == "failed"
    assert "Structure-aware ingestion failed" in refreshed.meta["lightrag"]["message"]


def test_lightrag_ingestion_locks_domain_embedding_on_first_success(
    tmp_path: Path,
    session: Session,
) -> None:
    manifest = DomainManifestStore(tmp_path / "domains.json")
    now = datetime(2026, 5, 18, 14, 30, tzinfo=UTC)
    manifest.add_domain(
        LightRAGDomain(
            id="fatigue",
            display_name="Fatigue",
            workspace="fatigue",
            postgres_database="lightrag_fatigue",
            postgres_user="lightrag_fatigue",
            host="127.0.0.1",
            host_port=9621,
            container_port=9621,
            base_url="http://127.0.0.1:9621",
            host_base_url="http://127.0.0.1:9621",
            container_base_url="http://lightrag_fatigue:9621",
            container_name="context_engine_lightrag_fatigue",
            service_name="lightrag_fatigue",
            status="running",
            paths={"root": str(tmp_path / "lightrag" / "domains" / "fatigue")},
            embedding=DomainEmbeddingSnapshot(
                profile_id="openai-text-embedding-3-small",
                provider="openai",
                binding="openai",
                base_url="https://api.openai.com/v1",
                model="text-embedding-3-small",
                dimensions=1536,
                fingerprint="openai:text-embedding-3-small:1536",
            ),
            created_at=now,
            updated_at=now,
        )
    )

    upload_path = tmp_path / "manual.txt"
    upload_path.write_text("Hello world", encoding="utf-8")
    lock = FakeLock()
    adapter = CapturingChunkAdapter()
    document = DocumentRepository(session).create(
        owner_id=None,
        filename="manual.txt",
        content_type="text/plain",
        storage_path=str(upload_path),
        metadata={
            "semantic_engine": "lightrag",
            "lightrag": {"domain_id": "fatigue", "status": "queued"},
        },
        status=DocumentStatus.INDEXING,
    )

    LightRAGIngestionService(
        session,
        adapter_factory=lambda domain_id: adapter,
        lock_factory=lambda domain_id: lock,
        artifact_store=_artifact_store(tmp_path),
        domain_manifest=manifest,
        now=lambda: now,
    ).ingest_document(document.id)

    updated_domain = manifest.get_domain("fatigue")
    assert updated_domain is not None
    assert updated_domain.embedding_locked_at is not None
    assert updated_domain.first_ingested_document_id == document.id
