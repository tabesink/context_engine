import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
os.environ["INDEX_JOBS_INLINE"] = "true"
os.environ["LIGHTRAG_ENABLED"] = "true"
Path(".data/test_context_engine.db").unlink(missing_ok=True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.document_processing.models import (  # noqa: E402
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
    SourceChunk,
)
from app.document_processing.pipeline import TextDoclingParser  # noqa: E402
from app.domain.models import DocumentStatus, UserRole  # noqa: E402
from app.integrations.lightrag_remote_adapter import LightRAGRemoteAdapter  # noqa: E402
from app.lightrag_deploy.models import LightRAGDomainCreateRequest  # noqa: E402
from app.lightrag_deploy.service import LightRAGDomainService  # noqa: E402
from app.lightrag_deploy.settings import LightRAGDeploySettings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.lightrag_ingestion_service import LightRAGIngestionService  # noqa: E402
from app.services.job_service import JobService  # noqa: E402
from app.storage.db import SessionLocal, create_db_and_tables  # noqa: E402
from app.storage.repositories.document_processing import DocumentProcessingRepository  # noqa: E402
from app.storage.repositories.jobs import JobRepository  # noqa: E402
from app.storage.repositories.documents import DocumentRepository  # noqa: E402
from app.storage.repositories.users import UserRepository  # noqa: E402
from app.workers.tasks import run_lightrag_ingest_job  # noqa: E402


@pytest.fixture(autouse=True)
def _settings_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    manifest_root = tmp_path_factory.mktemp("lightrag-manifest")
    manifest_path = manifest_root / "domains.json"
    manifest_path.write_text(
        '{"domains":[{"id":"default","status":"ready"},{"id":"fatigue","status":"ready"}]}',
        encoding="utf-8",
    )
    monkeypatch.setenv("LIGHTRAG_DOMAIN_MANIFEST", str(manifest_path))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", str(manifest_path))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _seed_users() -> None:
    with SessionLocal() as session:
        users = UserRepository(session)
        if not users.get_by_email("admin@example.com"):
            users.create(email="admin@example.com", password="secret", role=UserRole.ADMIN)
        if not users.get_by_email("user@example.com"):
            users.create(email="user@example.com", password="secret", role=UserRole.USER)


def _login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_admin_guardrails_and_document_retrieve_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_ingest_source_chunks(
        self: LightRAGRemoteAdapter,
        *,
        domain: str,
        chunks: list[SourceChunk],
    ) -> dict:
        del self
        assert domain == "default"
        assert chunks
        return {"document_id": "remote-doc-1", "track_id": "track-1", "status": "ready"}

    monkeypatch.setattr(LightRAGRemoteAdapter, "ingest_source_chunks", fake_ingest_source_chunks)

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        user_headers = _login(client, "user@example.com")

        blocked = client.get("/admin/ping", headers=user_headers)
        assert blocked.status_code == 403

        upload = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            files={"file": ("manual.txt", b"Installation steps live on page one.", "text/plain")},
        )
        assert upload.status_code == 200
        document_id = upload.json()["document"]["id"]

        documents = client.get("/documents", headers=user_headers)
        assert documents.status_code == 200
        assert documents.json()[0]["id"] == document_id

        retrieve = client.post(
            "/retrieve",
            headers=user_headers,
            json={"query": "where are installation steps", "mode": "navigation", "top_k": 3},
        )
        assert retrieve.status_code == 200
        body = retrieve.json()
        assert body["mode"] == "navigation"
        assert body["evidence"][0]["source_engine"] == "navigation"
        assert "answer" not in body


def test_removed_query_routes_return_404() -> None:
    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        payload = {"query": "where are installation steps", "mode": "navigation", "top_k": 3}

        assert client.post("/query", headers=user_headers, json=payload).status_code == 404
        assert client.post("/query/answer", headers=user_headers, json=payload).status_code == 404
        assert client.post("/query/retrieve", headers=user_headers, json=payload).status_code == 404


def test_lightrag_settings_default_to_remote_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LIGHTRAG_ENABLED", raising=False)
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.lightrag_enabled is True
    assert settings.lightrag_base_url


def test_lightrag_settings_reject_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "false")
    get_settings.cache_clear()

    with pytest.raises(ValidationError, match="LightRAG is required"):
        get_settings()


def test_lightrag_settings_require_endpoint_or_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    monkeypatch.setenv("LIGHTRAG_BASE_URL", "")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_MANIFEST", "")
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", "")
    get_settings.cache_clear()

    with pytest.raises(
        ValidationError,
        match="no LightRAG base URL or domain manifest is configured",
    ):
        get_settings()


def test_user_document_reads_hide_non_ready_documents() -> None:
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="draft.txt",
            content_type="text/plain",
            storage_path=".data/uploads/draft.txt",
            metadata={},
            status=DocumentStatus.INDEXING,
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")

        detail = client.get(f"/documents/{document_id}", headers=user_headers)
        structure = client.get(f"/documents/{document_id}/structure", headers=user_headers)
        page = client.get(f"/documents/{document_id}/pages/1", headers=user_headers)

    assert detail.status_code == 404
    assert structure.status_code == 404
    assert page.status_code == 404


def test_user_can_read_canonical_document_structure() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                sections=[
                    DocumentSection(
                        section_id=f"{document.id}-sec-1",
                        document_id=document.id,
                        title="Safety",
                        level=1,
                        page_start=1,
                        page_end=1,
                        block_ids=[f"{document.id}-block-1"],
                    )
                ],
                blocks=[
                    DocumentBlock(
                        block_id=f"{document.id}-block-1",
                        document_id=document.id,
                        section_id=f"{document.id}-sec-1",
                        type="paragraph",
                        text="Wear eye protection.",
                        page_start=1,
                        page_end=1,
                    )
                ],
                source_chunks=[
                    SourceChunk(
                        chunk_id=f"{document.id}-source-chunk-1",
                        document_id=document.id,
                        section_id=f"{document.id}-sec-1",
                        block_ids=[f"{document.id}-block-1"],
                        text="Wear eye protection.",
                        page_start=1,
                        page_end=1,
                    )
                ],
            )
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get(f"/documents/{document_id}/structure", headers=user_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "document_structure"
    assert body["tree"][0]["title"] == "Safety"
    assert body["pages"] == []
    assert body["sections"][0]["section_id"] == f"{document_id}-sec-1"
    assert body["source_chunks"][0]["chunk_id"] == f"{document_id}-source-chunk-1"
    assert body["blocks"] == []
    assert body["assets"] == []

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        included = client.get(
            f"/documents/{document_id}/structure?include_blocks=true&include_assets=true",
            headers=user_headers,
        )

    included_body = included.json()
    assert included.status_code == 200
    assert included_body["blocks"][0]["block_id"] == f"{document_id}-block-1"


def test_user_can_read_document_page_from_rich_structure() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                pages=[
                    DocumentPage(
                        page_number=1,
                        text="Page one content",
                        metadata={"label": "cover"},
                    )
                ],
            )
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get(f"/documents/{document_id}/pages/1", headers=user_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert body["page_number"] == 1
    assert body["text"] == "Page one content"
    assert body["metadata"] == {"label": "cover"}


def test_user_can_read_document_structure_quality() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                sections=[
                    DocumentSection(
                        section_id=f"{document.id}-sec-1",
                        document_id=document.id,
                        title="Safety",
                        level=1,
                        page_start=1,
                        page_end=1,
                    )
                ],
                blocks=[
                    DocumentBlock(
                        block_id=f"{document.id}-block-1",
                        document_id=document.id,
                        section_id=f"{document.id}-sec-1",
                        type="paragraph",
                        text="Wear eye protection.",
                    )
                ],
            )
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get(f"/documents/{document_id}/structure-quality", headers=user_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert body["heading_count"] == 0
    assert body["section_count"] == 1
    assert body["block_count"] == 1
    assert body["has_page_ranges"] is True
    assert body["should_run_toc_refiner"] is False


def test_structure_quality_route_hides_missing_structure_and_non_ready_documents() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        ready_document = DocumentRepository(session).create(
            owner_id=None,
            filename="ready.txt",
            content_type="text/plain",
            storage_path=".data/uploads/ready.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        indexing_document = DocumentRepository(session).create(
            owner_id=None,
            filename="indexing.txt",
            content_type="text/plain",
            storage_path=".data/uploads/indexing.txt",
            metadata={},
            status=DocumentStatus.INDEXING,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=indexing_document.id,
                source_file=indexing_document.storage_path,
                blocks=[
                    DocumentBlock(
                        block_id=f"{indexing_document.id}-block-1",
                        document_id=indexing_document.id,
                        type="paragraph",
                        text="Hidden.",
                    )
                ],
            )
        )
        ready_document_id = ready_document.id
        indexing_document_id = indexing_document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        missing_structure = client.get(
            f"/documents/{ready_document_id}/structure-quality",
            headers=user_headers,
        )
        hidden_document = client.get(
            f"/documents/{indexing_document_id}/structure-quality",
            headers=user_headers,
        )

    assert missing_structure.status_code == 404
    assert hidden_document.status_code == 404


def test_structure_route_returns_404_without_rich_structure() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get(f"/documents/{document_id}/structure", headers=user_headers)

    assert response.status_code == 404


def test_user_can_read_source_section_detail() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        section_id = f"{document.id}-sec-1"
        block_id = f"{document.id}-block-1"
        chunk_id = f"{document.id}-source-chunk-1"
        asset_id = f"{document.id}-asset-1"
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                sections=[
                    DocumentSection(
                        section_id=section_id,
                        document_id=document.id,
                        title="Safety",
                        level=1,
                        page_start=1,
                        page_end=2,
                        block_ids=[block_id],
                    )
                ],
                blocks=[
                    DocumentBlock(
                        block_id=block_id,
                        document_id=document.id,
                        section_id=section_id,
                        type="paragraph",
                        text="Wear eye protection.",
                        page_start=1,
                        page_end=1,
                        asset_ids=[asset_id],
                    )
                ],
                source_chunks=[
                    SourceChunk(
                        chunk_id=chunk_id,
                        document_id=document.id,
                        section_id=section_id,
                        block_ids=[block_id],
                        text="Wear eye protection.",
                        page_start=1,
                        page_end=1,
                        asset_ids=[asset_id],
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id=asset_id,
                        document_id=document.id,
                        section_id=section_id,
                        block_id=block_id,
                        chunk_id=chunk_id,
                        asset_type="figure",
                        storage_path=f"documents/{document.id}/assets/figure.png",
                        content_hash="hash-1",
                    )
                ],
            )
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get(
            f"/documents/{document_id}/sections/{document_id}-sec-1",
            headers=user_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["section"]["section_id"] == f"{document_id}-sec-1"
    assert body["blocks"][0]["block_id"] == f"{document_id}-block-1"
    assert body["source_chunks"][0]["chunk_id"] == f"{document_id}-source-chunk-1"
    assert body["assets"][0]["asset_id"] == f"{document_id}-asset-1"


def test_user_can_list_document_chunks_assets_and_ingestion_status() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={
                "lightrag": {"domain_id": "fatigue", "status": "ready", "track_id": "track-1"},
                "navigation": {"status": "ready"},
            },
            status=DocumentStatus.READY,
        )
        chunk_id = f"{document.id}-source-chunk-1"
        asset_id = f"{document.id}-asset-1"
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                source_chunks=[
                    SourceChunk(
                        chunk_id=chunk_id,
                        document_id=document.id,
                        block_ids=[f"{document.id}-block-1"],
                        text="See figure.",
                        asset_ids=[asset_id],
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id=asset_id,
                        document_id=document.id,
                        asset_type="figure",
                        storage_path=f"documents/{document.id}/assets/figure.png",
                        content_hash="hash-1",
                        chunk_id=chunk_id,
                    )
                ],
            )
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        chunks = client.get(f"/documents/{document_id}/chunks", headers=user_headers)
        assets = client.get(f"/documents/{document_id}/assets", headers=user_headers)
        status = client.get(f"/documents/{document_id}/ingestion-status", headers=user_headers)

    assert chunks.status_code == 200
    assert chunks.json()[0]["chunk_id"] == chunk_id
    assert assets.status_code == 200
    assert assets.json()[0]["asset_id"] == asset_id
    assert status.status_code == 200
    assert status.json()["lightrag"]["track_id"] == "track-1"
    assert status.json()["navigation"]["status"] == "ready"


def test_source_section_route_hides_missing_and_non_ready_documents() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        ready_document = DocumentRepository(session).create(
            owner_id=None,
            filename="ready.txt",
            content_type="text/plain",
            storage_path=".data/uploads/ready.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        indexing_document = DocumentRepository(session).create(
            owner_id=None,
            filename="indexing.txt",
            content_type="text/plain",
            storage_path=".data/uploads/indexing.txt",
            metadata={},
            status=DocumentStatus.INDEXING,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=indexing_document.id,
                source_file=indexing_document.storage_path,
                sections=[
                    DocumentSection(
                        section_id=f"{indexing_document.id}-hidden-sec",
                        document_id=indexing_document.id,
                        title="Hidden",
                        level=1,
                    )
                ],
            )
        )
        ready_document_id = ready_document.id
        indexing_document_id = indexing_document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        missing_section = client.get(
            f"/documents/{ready_document_id}/sections/missing-sec",
            headers=user_headers,
        )
        hidden_document = client.get(
            f"/documents/{indexing_document_id}/sections/{indexing_document_id}-hidden-sec",
            headers=user_headers,
        )

    assert missing_section.status_code == 404
    assert hidden_document.status_code == 404


def test_user_can_read_source_chunk_detail() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                source_chunks=[
                    SourceChunk(
                        chunk_id=f"{document.id}-source-chunk-1",
                        document_id=document.id,
                        section_id=f"{document.id}-sec-1",
                        block_ids=[f"{document.id}-block-1"],
                        text="Wear eye protection.",
                        page_start=1,
                        page_end=2,
                        asset_ids=["asset-1"],
                    )
                ],
            )
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get(
            f"/documents/{document_id}/chunks/{document_id}-source-chunk-1",
            headers=user_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["chunk_id"] == f"{document_id}-source-chunk-1"
    assert body["document_id"] == document_id
    assert body["section_id"] == f"{document_id}-sec-1"
    assert body["block_ids"] == [f"{document_id}-block-1"]
    assert body["page_start"] == 1
    assert body["page_end"] == 2
    assert body["asset_ids"] == ["asset-1"]
    assert body["text"] == "Wear eye protection."


def test_source_chunk_route_hides_missing_and_non_ready_documents() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        ready_document = DocumentRepository(session).create(
            owner_id=None,
            filename="ready.txt",
            content_type="text/plain",
            storage_path=".data/uploads/ready.txt",
            metadata={},
            status=DocumentStatus.READY,
        )
        indexing_document = DocumentRepository(session).create(
            owner_id=None,
            filename="indexing.txt",
            content_type="text/plain",
            storage_path=".data/uploads/indexing.txt",
            metadata={},
            status=DocumentStatus.INDEXING,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=indexing_document.id,
                source_file=indexing_document.storage_path,
                source_chunks=[
                    SourceChunk(
                        chunk_id=f"{indexing_document.id}-hidden-chunk",
                        document_id=indexing_document.id,
                        block_ids=[f"{indexing_document.id}-block-1"],
                        text="Hidden.",
                    )
                ],
            )
        )
        ready_document_id = ready_document.id
        indexing_document_id = indexing_document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        missing_chunk = client.get(
            f"/documents/{ready_document_id}/chunks/missing-chunk",
            headers=user_headers,
        )
        hidden_document = client.get(
            f"/documents/{indexing_document_id}/chunks/{indexing_document_id}-hidden-chunk",
            headers=user_headers,
        )

    assert missing_chunk.status_code == 404
    assert hidden_document.status_code == 404


def test_user_can_stream_ready_document_asset_without_path_leakage(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=str(tmp_path / "manual.txt"),
            metadata={},
            status=DocumentStatus.READY,
        )
        asset_path = tmp_path / "documents" / document.id / "assets" / "figure.png"
        asset_path.parent.mkdir(parents=True)
        asset_path.write_bytes(b"figure-bytes")
        thumbnail_path = tmp_path / "documents" / document.id / "assets" / "figure_thumb.png"
        thumbnail_path.write_bytes(b"thumb-bytes")
        asset_id = f"asset-{document.id}"
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                assets=[
                    DocumentAsset(
                        asset_id=asset_id,
                        document_id=document.id,
                        asset_type="figure",
                        storage_path=str(asset_path),
                        thumbnail_path=str(thumbnail_path),
                        content_hash="hash-1",
                    )
                ],
            )
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        asset = client.get(f"/documents/{document_id}/assets/{asset_id}", headers=user_headers)
        thumbnail = client.get(
            f"/documents/{document_id}/assets/{asset_id}/thumbnail",
            headers=user_headers,
        )
        unauthenticated = client.get(f"/documents/{document_id}/assets/{asset_id}")

    assert asset.status_code == 200
    assert asset.content == b"figure-bytes"
    assert str(asset_path) not in asset.text
    assert thumbnail.status_code == 200
    assert thumbnail.content == b"thumb-bytes"
    assert unauthenticated.status_code == 401


def test_asset_route_hides_non_ready_documents(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=str(tmp_path / "manual.txt"),
            metadata={},
            status=DocumentStatus.INDEXING,
        )
        asset_path = tmp_path / "documents" / document.id / "assets" / "figure.png"
        asset_path.parent.mkdir(parents=True)
        asset_path.write_bytes(b"figure-bytes")
        asset_id = f"asset-{document.id}"
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                assets=[
                    DocumentAsset(
                        asset_id=asset_id,
                        document_id=document.id,
                        asset_type="figure",
                        storage_path=str(asset_path),
                        content_hash="hash-1",
                    )
                ],
            )
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get(f"/documents/{document_id}/assets/{asset_id}", headers=user_headers)

    assert response.status_code == 404


def test_retrieve_uses_remote_lightrag_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    get_settings.cache_clear()

    document_id = "11111111-1111-4111-8111-111111111111"

    def fake_retrieve(
        self: LightRAGRemoteAdapter,
        *,
        query: str,
        mode,
        top_k: int,
        document_ids: list[str] | None,
        domain: str | None = None,
    ):
        del self, mode, top_k, document_ids
        assert domain == "default"
        from uuid import UUID

        from app.domain.models import Evidence, PageRef

        return [
            Evidence(
                id="chunk-1",
                document_id=UUID(document_id),
                source_engine="lightrag",
                text=f"Remote context for {query}",
                score=0.91,
                page_ref=PageRef(document_id=UUID(document_id), page_start=2, page_end=3),
                metadata={"source_path": "manual.pdf"},
            )
        ]

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")

        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={"query": "summarize remote context", "mode": "auto", "top_k": 3},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["evidence"][0]["source_engine"] == "lightrag"
    assert body["evidence"][0]["text"] == "Remote context for summarize remote context"


def test_admin_upload_queues_lightrag_ingestion_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "domains.json"
    manifest_path.write_text('{"domains":[{"id":"default","status":"ready"}]}', encoding="utf-8")
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    monkeypatch.setenv("INDEX_JOBS_INLINE", "false")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_MANIFEST", str(manifest_path))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", str(manifest_path))
    get_settings.cache_clear()

    class FakeQueue:
        def enqueue(self, function: object, job_id: str):
            del function

            class FakeQueuedJob:
                id = f"rq-{job_id}"

            return FakeQueuedJob()

    monkeypatch.setattr(JobService, "_queue", lambda self: FakeQueue())

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        user_headers = _login(client, "user@example.com")

        blocked = client.post(
            "/admin/documents/upload",
            headers=user_headers,
            files={"file": ("blocked.txt", b"blocked", "text/plain")},
        )
        assert blocked.status_code == 403

        response = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            data={"semantic_engine": "lightrag"},
            files={"file": ("manual.txt", b"Remote document body.", "text/plain")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] is not None
    assert body["document"]["status"] == "indexing"
    assert body["document"]["metadata"]["semantic_engine"] == "lightrag"
    assert body["document"]["metadata"]["lightrag"]["domain_id"] == "default"
    assert body["document"]["metadata"]["lightrag"]["status"] == "queued"
    with SessionLocal() as session:
        job = JobRepository(session).get(body["job_id"])
        assert job is not None
        assert job.kind == "lightrag_ingest_document"
        assert job.document_id == body["document"]["id"]


def test_admin_upload_requires_lightrag_domain_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_MANIFEST", ".data/missing-lightrag-domains.json")
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", ".data/missing-lightrag-domains.json")
    get_settings.cache_clear()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            data={"semantic_engine": "lightrag"},
            files={"file": ("manual.txt", b"Remote document body.", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "LightRAG domain manifest is required for uploads."


def test_admin_upload_to_selected_lightrag_domain_records_domain_metadata(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = LightRAGDeploySettings(
        enabled=True,
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag/domains",
        manifest_path=tmp_path / "lightrag/domains.json",
        compose_file=tmp_path / "lightrag/compose.yml",
        deleted_root=tmp_path / "lightrag/deleted",
    )
    LightRAGDomainService(settings=settings).create_domain(
        LightRAGDomainCreateRequest(domain_id="fatigue", display_name="Fatigue Manuals")
    )
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    monkeypatch.setenv("INDEX_JOBS_INLINE", "false")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_MANIFEST", str(settings.manifest_path))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", str(settings.manifest_path))
    get_settings.cache_clear()

    class FakeQueue:
        def enqueue(self, function: object, job_id: str):
            del function

            class FakeQueuedJob:
                id = f"rq-{job_id}"

            return FakeQueuedJob()

    monkeypatch.setattr(JobService, "_queue", lambda self: FakeQueue())

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            data={"lightrag_domain_id": "fatigue"},
            files={"file": ("manual.txt", b"Remote document body.", "text/plain")},
        )

    assert response.status_code == 200
    metadata = response.json()["document"]["metadata"]["lightrag"]
    assert metadata["domain_id"] == "fatigue"
    assert metadata["status"] == "queued"


def test_lightrag_ingestion_job_uploads_polls_and_marks_document_ready(tmp_path: Path) -> None:
    create_db_and_tables()
    upload_path = tmp_path / "manual.txt"
    upload_path.write_text("Safety steps", encoding="utf-8")

    class FakeLock:
        acquired = False
        released = False

        def acquire(self) -> bool:
            self.acquired = True
            return True

        def release(self) -> None:
            self.released = True

    lock = FakeLock()

    class FakeAdapter:
        def ingest_source_chunks(self, *, domain: str, chunks: list) -> dict:
            assert domain == "fatigue"
            assert len(chunks) == 1
            return {"document_id": "remote-doc", "track_id": "track-1", "status": "indexing"}

        def document_status(self, track_id: str) -> dict:
            assert track_id == "track-1"
            return {"document_id": "remote-doc", "track_id": "track-1", "status": "ready"}

    with SessionLocal() as session:
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
            adapter_factory=lambda domain_id: FakeAdapter(),
            lock_factory=lambda domain_id: lock,
            structure_parser=TextDoclingParser(),
        ).ingest_document(document.id)

        refreshed = DocumentRepository(session).get(document.id)

    assert lock.acquired is True
    assert lock.released is True
    assert refreshed is not None
    assert refreshed.status == DocumentStatus.READY.value
    assert refreshed.meta["lightrag"]["document_id"] == "remote-doc"
    assert refreshed.meta["lightrag"]["track_id"] == "track-1"
    assert refreshed.meta["lightrag"]["status"] == "ready"


def test_admin_refresh_lightrag_status_marks_document_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    create_db_and_tables()
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    get_settings.cache_clear()

    def fake_document_status(self: LightRAGRemoteAdapter, track_id: str) -> dict:
        del self
        assert track_id == "track-1"
        return {"document_id": "remote-doc", "track_id": track_id, "status": "ready"}

    monkeypatch.setattr(LightRAGRemoteAdapter, "document_status", fake_document_status)
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={
                "semantic_engine": "lightrag",
                "lightrag": {"domain_id": "default", "track_id": "track-1", "status": "indexing"},
            },
            status=DocumentStatus.INDEXING,
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(
            f"/admin/documents/{document_id}/refresh-lightrag-status",
            headers=admin_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["metadata"]["lightrag"]["document_id"] == "remote-doc"


def test_admin_refresh_lightrag_status_rejects_unknown_upstream_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_db_and_tables()
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    get_settings.cache_clear()

    def fake_document_status(self: LightRAGRemoteAdapter, track_id: str) -> dict:
        del self
        assert track_id == "track-1"
        return {"document_id": "remote-doc", "track_id": track_id, "status": "mystery"}

    monkeypatch.setattr(LightRAGRemoteAdapter, "document_status", fake_document_status)
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={
                "semantic_engine": "lightrag",
                "lightrag": {"domain_id": "default", "track_id": "track-1", "status": "indexing"},
            },
            status=DocumentStatus.INDEXING,
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(
            f"/admin/documents/{document_id}/refresh-lightrag-status",
            headers=admin_headers,
        )

    assert response.status_code == 502
    assert "Unknown LightRAG status" in response.json()["detail"]


def test_admin_upload_to_missing_lightrag_domain_fails_before_forwarding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = LightRAGDeploySettings(
        enabled=True,
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag/domains",
        manifest_path=tmp_path / "lightrag/domains.json",
        compose_file=tmp_path / "lightrag/compose.yml",
        deleted_root=tmp_path / "lightrag/deleted",
    )
    LightRAGDomainService(settings=settings).create_domain(
        LightRAGDomainCreateRequest(domain_id="fatigue")
    )
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_MANIFEST", str(settings.manifest_path))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", str(settings.manifest_path))
    get_settings.cache_clear()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            data={"lightrag_domain_id": "missing"},
            files={"file": ("manual.txt", b"Remote document body.", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "LightRAG domain 'missing' does not exist"


def test_retrieve_uses_selected_lightrag_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    get_settings.cache_clear()
    seen_domains: list[str | None] = []

    def fake_retrieve(
        self: LightRAGRemoteAdapter,
        *,
        query: str,
        mode,
        top_k: int,
        document_ids: list[str] | None,
        domain: str | None = None,
    ):
        del self, query, mode, top_k, document_ids
        seen_domains.append(domain)
        return []

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={"query": "fatigue limits", "mode": "semantic", "lightrag_domain_id": "fatigue"},
        )

    assert response.status_code == 200
    assert seen_domains == ["fatigue"]


def test_retrieve_rejects_document_ids_from_different_lightrag_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    get_settings.cache_clear()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=".data/uploads/manual.txt",
            metadata={"lightrag": {"domain_id": "abaqus"}},
            status=DocumentStatus.READY,
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={
                "query": "fatigue limits",
                "mode": "semantic",
                "lightrag_domain_id": "fatigue",
                "document_ids": [document_id],
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Selected documents must belong to LightRAG domain 'fatigue'"


def test_lightrag_graph_proxy_uses_upstream_route_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    get_settings.cache_clear()

    seen_paths: list[str] = []

    def fake_get_json(self: LightRAGRemoteAdapter, path: str, *, params: dict | None = None):
        del self, params
        seen_paths.append(path)
        return {"path": path, "nodes": [], "edges": []}

    monkeypatch.setattr(LightRAGRemoteAdapter, "get_json", fake_get_json)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        graph = client.get("/graphs?label=Pump", headers=user_headers)
        labels = client.get("/graph/label/list", headers=user_headers)

    assert graph.status_code == 200
    assert labels.status_code == 200
    assert seen_paths == ["/graphs", "/graph/label/list"]


def test_lightrag_failures_return_stable_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    get_settings.cache_clear()

    def fake_retrieve(self: LightRAGRemoteAdapter, **kwargs):
        del self, kwargs
        from app.integrations.lightrag_remote_adapter import LightRAGServiceUnavailable

        raise LightRAGServiceUnavailable("LightRAG service unavailable")

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={"query": "summarize remote context", "mode": "semantic"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "LightRAG service unavailable"


def test_lightrag_domain_admin_api_requires_admin_and_enabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ENABLED", "false")
    get_settings.cache_clear()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        user_headers = _login(client, "user@example.com")

        blocked = client.post(
            "/admin/lightrag/domains",
            headers=user_headers,
            json={"domain_id": "fatigue"},
        )
        disabled = client.post(
            "/admin/lightrag/domains",
            headers=admin_headers,
            json={"domain_id": "fatigue"},
        )

    assert blocked.status_code == 403
    assert disabled.status_code == 400
    assert disabled.json()["detail"] == "LightRAG deployment is disabled"


def test_lightrag_domain_admin_api_create_list_and_operate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ENABLED", "true")
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ROOT", str(tmp_path / "lightrag"))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_ROOT", str(tmp_path / "lightrag/domains"))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", str(tmp_path / "lightrag/domains.json"))
    monkeypatch.setenv("LIGHTRAG_COMPOSE_FILE", str(tmp_path / "lightrag/compose.yml"))
    monkeypatch.setenv("LIGHTRAG_DELETED_ROOT", str(tmp_path / "lightrag/deleted"))
    get_settings.cache_clear()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")

        create = client.post(
            "/admin/lightrag/domains",
            headers=admin_headers,
            json={"domain_id": "fatigue", "display_name": "Fatigue Manuals"},
        )
        listing = client.get("/admin/lightrag/domains", headers=admin_headers)
        detail = client.get("/admin/lightrag/domains/fatigue", headers=admin_headers)
        regenerate = client.post(
            "/admin/lightrag/domains/fatigue/regenerate",
            headers=admin_headers,
        )

    assert create.status_code == 200
    assert create.json()["id"] == "fatigue"
    assert listing.status_code == 200
    assert listing.json()["domains"][0]["display_name"] == "Fatigue Manuals"
    assert detail.status_code == 200
    assert detail.json()["service_name"] == "lightrag_fatigue"
    assert regenerate.status_code == 200
    assert regenerate.json() == {"status": "ok"}


def test_lightrag_admin_and_user_domain_responses_do_not_leak_provider_secrets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bedrock_key = "test-bedrock-key"
    embedding_key = "test-openai-key"
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ENABLED", "true")
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ROOT", str(tmp_path / "lightrag"))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_ROOT", str(tmp_path / "lightrag/domains"))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", str(tmp_path / "lightrag/domains.json"))
    monkeypatch.setenv("LIGHTRAG_COMPOSE_FILE", str(tmp_path / "lightrag/compose.yml"))
    monkeypatch.setenv("LIGHTRAG_DELETED_ROOT", str(tmp_path / "lightrag/deleted"))
    monkeypatch.setenv("LIGHTRAG_LLM_BINDING_HOST", "https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1")
    monkeypatch.setenv("LIGHTRAG_LLM_BINDING_API_KEY", bedrock_key)
    monkeypatch.setenv("LIGHTRAG_EMBEDDING_BINDING_HOST", "https://api.openai.com/v1")
    monkeypatch.setenv("LIGHTRAG_EMBEDDING_BINDING_API_KEY", embedding_key)
    get_settings.cache_clear()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        user_headers = _login(client, "user@example.com")
        create = client.post(
            "/admin/lightrag/domains",
            headers=admin_headers,
            json={"domain_id": "fatigue"},
        )
        admin_list = client.get("/admin/lightrag/domains", headers=admin_headers)
        admin_detail = client.get("/admin/lightrag/domains/fatigue", headers=admin_headers)
        user_list = client.get("/lightrag/domains", headers=user_headers)

    assert create.status_code == 200
    assert admin_list.status_code == 200
    assert admin_detail.status_code == 200
    assert user_list.status_code == 200
    assert bedrock_key not in admin_list.text
    assert embedding_key not in admin_list.text
    assert bedrock_key not in admin_detail.text
    assert embedding_key not in admin_detail.text
    assert bedrock_key not in user_list.text
    assert embedding_key not in user_list.text


def test_lightrag_domain_user_safe_list_hides_paths_and_container_details(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = LightRAGDeploySettings(
        enabled=True,
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag/domains",
        manifest_path=tmp_path / "lightrag/domains.json",
        compose_file=tmp_path / "lightrag/compose.yml",
        deleted_root=tmp_path / "lightrag/deleted",
    )
    LightRAGDomainService(settings=settings).create_domain(
        LightRAGDomainCreateRequest(domain_id="fatigue", display_name="Fatigue Manuals")
    )
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", str(settings.manifest_path))
    get_settings.cache_clear()

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get("/lightrag/domains", headers=user_headers)
        unauthenticated = client.get("/lightrag/domains")

    assert response.status_code == 200
    domain = response.json()["domains"][0]
    assert domain == {
        "id": "fatigue",
        "display_name": "Fatigue Manuals",
        "is_healthy": None,
        "is_default": True,
    }
    assert "paths" not in domain
    assert "container_name" not in domain
    assert unauthenticated.status_code == 401


def test_lightrag_ingest_job_can_be_enqueued_without_running_inline() -> None:
    class FakeQueue:
        def __init__(self) -> None:
            self.enqueued: list[tuple[object, str]] = []

        def enqueue(self, function: object, job_id: str):
            self.enqueued.append((function, job_id))
            return type("QueuedJob", (), {"id": "rq-job-1"})()

    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="missing-document.txt",
            content_type="text/plain",
            storage_path=".data/uploads/missing-document.txt",
            metadata={"lightrag": {"domain_id": "default", "status": "queued"}},
            status=DocumentStatus.INDEXING,
        )
        queue = FakeQueue()
        job_id = JobService(session, queue=queue, run_inline=False).enqueue_lightrag_ingest_document(
            document_id=document.id
        )
        job = JobRepository(session).get(job_id)

    assert len(queue.enqueued) == 1
    assert queue.enqueued[0][1] == job_id
    assert job.status == "queued"
    assert job.meta["rq_job_id"] == "rq-job-1"


def test_worker_marks_failed_lightrag_ingest_job_when_document_is_missing() -> None:
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="missing-document.txt",
            content_type="text/plain",
            storage_path=".data/uploads/missing-document.txt",
            metadata={"lightrag": {"domain_id": "default", "status": "queued"}},
            status=DocumentStatus.INDEXING,
        )
        job = JobRepository(session).create(kind="lightrag_ingest_document", document_id=document.id)
        DocumentRepository(session).mark_deleted(document)
        job_id = job.id

    with pytest.raises(ValueError, match="Structure-aware ingestion failed"):
        run_lightrag_ingest_job(job_id)

    with SessionLocal() as session:
        refreshed = JobRepository(session).get(job_id)

    assert refreshed.status == "failed"
    assert "Structure-aware ingestion failed" in refreshed.error_message

