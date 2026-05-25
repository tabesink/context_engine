import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
Path(".data/test_context_engine.db").unlink(missing_ok=True)

from app.document_processing.models import (  # noqa: E402
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
    SourceChunk,
)
from app.domain.models import DocumentStatus  # noqa: E402
from app.retrieval.rich_navigation_engine import RichNavigationEngine  # noqa: E402
from app.storage import tables  # noqa: E402, F401
from app.storage.db import Base  # noqa: E402
from app.storage.repositories.document_processing import DocumentProcessingRepository  # noqa: E402
from app.storage.repositories.documents import DocumentRepository  # noqa: E402


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return session_factory()


def test_rich_navigation_engine_prefers_source_chunks_and_preserves_refs() -> None:
    with _session() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path="/tmp/manual.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        section_id = f"{document.id}-sec-1"
        block_id = f"{document.id}-block-1"
        chunk_id = f"{document.id}-chunk-1"
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                pages=[DocumentPage(page_number=1, text="Installation overview")],
                sections=[
                    DocumentSection(
                        section_id=section_id,
                        document_id=document.id,
                        title="Installation",
                        level=1,
                        page_start=1,
                        page_end=1,
                    )
                ],
                blocks=[
                    DocumentBlock(
                        block_id=block_id,
                        document_id=document.id,
                        section_id=section_id,
                        type="paragraph",
                        text="Installation steps for pump service.",
                        page_start=1,
                        page_end=1,
                    )
                ],
                source_chunks=[
                    SourceChunk(
                        chunk_id=chunk_id,
                        document_id=document.id,
                        section_id=section_id,
                        block_ids=[block_id],
                        text="Installation steps for pump service.",
                        page_start=1,
                        page_end=1,
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id=f"{document.id}-asset-1",
                        document_id=document.id,
                        section_id=section_id,
                        asset_type="figure",
                        storage_path="/tmp/figure.png",
                        content_hash="hash-1",
                        page_number=1,
                        caption="Installation figure",
                    )
                ],
            )
        )

        evidence = RichNavigationEngine(session).retrieve(
            query="installation steps",
            document_ids=[document.id],
            top_k=3,
            user_id="user-1",
        )

    assert evidence
    assert evidence[0].metadata["source"] == "source_chunk"
    assert evidence[0].metadata["chunk_id"] == chunk_id
    assert evidence[0].section_ref is not None
    assert evidence[0].section_ref.title == "Installation"
    assert evidence[0].page_ref is not None
    assert evidence[0].page_ref.page_start == 1


def test_rich_navigation_engine_respects_document_filter_and_top_k() -> None:
    with _session() as session:
        first = DocumentRepository(session).create(
            owner_id=None,
            filename="first.txt",
            content_type="text/plain",
            storage_path="/tmp/first.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        second = DocumentRepository(session).create(
            owner_id=None,
            filename="second.txt",
            content_type="text/plain",
            storage_path="/tmp/second.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        repo = DocumentProcessingRepository(session)
        repo.save_structure(
            DocumentStructure(
                document_id=first.id,
                source_file=first.storage_path,
                source_chunks=[
                    SourceChunk(
                        chunk_id=f"{first.id}-chunk-1",
                        document_id=first.id,
                        block_ids=[],
                        text="Calibration reference",
                    )
                ],
            )
        )
        repo.save_structure(
            DocumentStructure(
                document_id=second.id,
                source_file=second.storage_path,
                source_chunks=[
                    SourceChunk(
                        chunk_id=f"{second.id}-chunk-1",
                        document_id=second.id,
                        block_ids=[],
                        text="Calibration limits and torque",
                    )
                ],
            )
        )

        evidence = RichNavigationEngine(session).retrieve(
            query="calibration torque",
            document_ids=[second.id],
            top_k=1,
            user_id="user-1",
        )

    assert len(evidence) == 1
    assert str(evidence[0].document_id) == second.id
