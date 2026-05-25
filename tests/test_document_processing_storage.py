import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.document_processing.artifacts import DocumentProcessingArtifactStore
from app.document_processing.models import DocumentAsset, DocumentPage, DocumentStructure, SourceChunk
from app.document_processing.storage_paths import DocumentStoragePaths
from app.storage.db import Base
from app.storage.repositories.document_processing import DocumentProcessingRepository
from app.storage import tables  # noqa: F401


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as session:
        yield session


def test_document_processing_repository_persists_source_chunks_and_assets(session: Session) -> None:
    repository = DocumentProcessingRepository(session)
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        source_chunks=[
            SourceChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                block_ids=["block-1"],
                text="See figure 1.",
                asset_ids=["asset-1"],
            )
        ],
        assets=[
            DocumentAsset(
                asset_id="asset-1",
                document_id="doc-1",
                asset_type="figure",
                storage_path="documents/doc-1/assets/asset-1.png",
                thumbnail_path="documents/doc-1/assets/asset-1_thumb.png",
                content_hash="hash-1",
                chunk_id="chunk-1",
            )
        ],
    )

    repository.save_structure(structure)

    assert repository.get_source_chunk("doc-1", "chunk-1").asset_ids == ["asset-1"]
    assert repository.list_assets_for_chunks(["chunk-1"])[0].asset_id == "asset-1"


def test_document_processing_repository_persists_pages_and_returns_ordered_page_data(
    session: Session,
) -> None:
    repository = DocumentProcessingRepository(session)
    structure = DocumentStructure(
        document_id="doc-1",
        source_file="manual.pdf",
        pages=[
            DocumentPage(page_number=2, text="Second page", metadata={"kind": "body"}),
            DocumentPage(page_number=1, text="First page", metadata={"kind": "cover"}),
        ],
    )
    repository.save_structure(structure)

    loaded = repository.get_structure("doc-1", source_file="manual.pdf")
    assert loaded is not None
    assert [page.page_number for page in loaded.pages] == [1, 2]
    assert loaded.pages[0].metadata == {"kind": "cover"}
    assert loaded.pages[1].metadata == {"kind": "body"}


def test_document_processing_repository_get_page_returns_single_page_or_none(session: Session) -> None:
    repository = DocumentProcessingRepository(session)
    repository.save_structure(
        DocumentStructure(
            document_id="doc-1",
            source_file="manual.pdf",
            pages=[
                DocumentPage(page_number=1, text="One"),
                DocumentPage(page_number=2, text="Two", metadata={"label": "target"}),
            ],
        )
    )

    page = repository.get_page("doc-1", 2)
    assert page is not None
    assert page.page_number == 2
    assert page.text == "Two"
    assert page.metadata == {"label": "target"}
    assert repository.get_page("doc-1", 3) is None


def test_document_processing_repository_resave_replaces_existing_pages(session: Session) -> None:
    repository = DocumentProcessingRepository(session)
    repository.save_structure(
        DocumentStructure(
            document_id="doc-1",
            source_file="manual.pdf",
            pages=[DocumentPage(page_number=1, text="Old page")],
        )
    )
    repository.save_structure(
        DocumentStructure(
            document_id="doc-1",
            source_file="manual.pdf",
            pages=[DocumentPage(page_number=2, text="New page")],
        )
    )

    loaded = repository.get_structure("doc-1", source_file="manual.pdf")
    assert loaded is not None
    assert [page.page_number for page in loaded.pages] == [2]
    assert repository.get_page("doc-1", 1) is None


def test_document_storage_paths_reject_paths_outside_document_root(tmp_path: Path) -> None:
    paths = DocumentStoragePaths(storage_root=tmp_path)

    asset_path = paths.asset_path(document_id="doc-1", filename="figure.png")

    assert asset_path == tmp_path / "documents" / "doc-1" / "assets" / "figure.png"
    with pytest.raises(ValueError, match="inside document storage"):
        paths.asset_path(document_id="doc-1", filename="../secret.txt")


def test_artifact_store_writes_document_structure_manifest(tmp_path: Path) -> None:
    store = DocumentProcessingArtifactStore(
        storage_paths=DocumentStoragePaths(storage_root=tmp_path),
    )

    path = store.save_structure(
        DocumentStructure(
            document_id="doc-1",
            source_file="manual.pdf",
            source_chunks=[
                SourceChunk(
                    chunk_id="chunk-1",
                    document_id="doc-1",
                    block_ids=["block-1"],
                    text="See figure 1.",
                    asset_ids=["asset-1"],
                )
            ],
        )
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path == tmp_path / "documents" / "doc-1" / "manifest" / "document_structure.json"
    assert payload["document_id"] == "doc-1"
    assert payload["source_chunks"][0]["asset_ids"] == ["asset-1"]


