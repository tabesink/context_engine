import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
os.environ["INDEX_JOBS_INLINE"] = "true"
os.environ["LIGHTRAG_ENABLED"] = "false"
Path(".data/test_context_engine.db").unlink(missing_ok=True)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.domain.models import DocumentStatus, UserRole  # noqa: E402
from app.integrations.lightrag_remote_adapter import LightRAGRemoteAdapter  # noqa: E402
from app.lightrag_deploy.models import LightRAGDomainCreateRequest  # noqa: E402
from app.lightrag_deploy.service import LightRAGDomainService  # noqa: E402
from app.lightrag_deploy.settings import LightRAGDeploySettings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.lightrag_ingestion_service import LightRAGIngestionService  # noqa: E402
from app.services.job_service import JobService  # noqa: E402
from app.storage.db import SessionLocal, create_db_and_tables  # noqa: E402
from app.storage.repositories.jobs import JobRepository  # noqa: E402
from app.storage.repositories.documents import DocumentRepository  # noqa: E402
from app.storage.repositories.users import UserRepository  # noqa: E402
from app.workers.tasks import run_index_job  # noqa: E402


@pytest.fixture(autouse=True)
def _settings_cache() -> None:
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


def test_admin_guardrails_and_document_query_flow() -> None:
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
            "/query/retrieve",
            headers=user_headers,
            json={"query": "where are installation steps", "mode": "auto", "top_k": 3},
        )
        assert retrieve.status_code == 200
        body = retrieve.json()
        assert body["mode"] == "navigation"
        assert body["evidence"][0]["source_engine"] == "navigation"

        answer = client.post(
            "/query/answer",
            headers=user_headers,
            json={"query": "where are installation steps", "mode": "hybrid", "top_k": 3},
        )
        assert answer.status_code == 200
        assert "evidence item" in answer.json()["answer"]


def test_lightrag_settings_keep_remote_disabled_by_default() -> None:
    settings = get_settings()

    assert settings.lightrag_enabled is False
    assert settings.lightrag_base_url


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
        DocumentRepository(session).save_navigation_index(
            document_id=document.id,
            tree=[{"title": "Draft"}],
            version=1,
        )
        DocumentRepository(session).save_parsed(
            document_id=document.id,
            title="Draft",
            pages=[{"number": 1, "text": "draft", "metadata": {}}],
            full_text="draft",
            metadata={},
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


def test_query_retrieve_uses_remote_lightrag_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
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
            "/query/retrieve",
            headers=user_headers,
            json={"query": "summarize remote context", "mode": "auto", "top_k": 3},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["evidence"][0]["source_engine"] == "lightrag"
    assert body["evidence"][0]["text"] == "Remote context for summarize remote context"


def test_admin_upload_queues_lightrag_ingestion_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    monkeypatch.setenv("INDEX_JOBS_INLINE", "false")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_MANIFEST", ".data/missing-lightrag-domains.json")
    monkeypatch.setenv("LIGHTRAG_DOMAINS_MANIFEST", ".data/missing-lightrag-domains.json")
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
    upload_path.write_text("Remote document body.", encoding="utf-8")

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
        def upload_document(self, **kwargs) -> dict:
            assert kwargs["domain"] == "fatigue"
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


def test_query_retrieve_uses_selected_lightrag_domain(monkeypatch: pytest.MonkeyPatch) -> None:
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
            "/query/retrieve",
            headers=user_headers,
            json={"query": "fatigue limits", "mode": "semantic", "lightrag_domain_id": "fatigue"},
        )

    assert response.status_code == 200
    assert seen_domains == ["fatigue"]


def test_query_rejects_document_ids_from_different_lightrag_domain(
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
            "/query/retrieve",
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
            "/query/retrieve",
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


def test_index_job_can_be_enqueued_without_running_inline() -> None:
    class FakeQueue:
        def __init__(self) -> None:
            self.enqueued: list[tuple[object, str]] = []

        def enqueue(self, function: object, job_id: str):
            self.enqueued.append((function, job_id))
            return type("QueuedJob", (), {"id": "rq-job-1"})()

    with SessionLocal() as session:
        queue = FakeQueue()
        job_id = JobService(session, queue=queue, run_inline=False).enqueue_index_document(
            document_id="missing-document"
        )
        job = JobRepository(session).get(job_id)

    assert len(queue.enqueued) == 1
    assert queue.enqueued[0][1] == job_id
    assert job.status == "queued"
    assert job.meta["rq_job_id"] == "rq-job-1"


def test_worker_marks_failed_index_job_when_document_is_missing() -> None:
    with SessionLocal() as session:
        job = JobRepository(session).create(kind="index_document", document_id="missing-document")
        job_id = job.id

    run_index_job(job_id)

    with SessionLocal() as session:
        refreshed = JobRepository(session).get(job_id)

    assert refreshed.status == "failed"
    assert "not found" in refreshed.error_message

