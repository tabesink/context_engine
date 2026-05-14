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
from app.main import app  # noqa: E402
from app.services.job_service import JobService  # noqa: E402
from app.storage.db import SessionLocal  # noqa: E402
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


def test_admin_upload_forwards_to_lightrag_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_ENABLED", "true")
    get_settings.cache_clear()

    def fake_upload_document(
        self: LightRAGRemoteAdapter,
        *,
        file_path,
        filename: str,
        content_type: str,
        metadata: dict | None = None,
        domain: str | None = None,
    ) -> dict:
        del self, file_path, content_type, metadata, domain
        return {
            "document_id": f"external-{filename}",
            "track_id": "track-123",
            "status": "indexing",
            "message": "Document accepted",
        }

    monkeypatch.setattr(LightRAGRemoteAdapter, "upload_document", fake_upload_document)

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
            files={"file": ("manual.txt", b"Remote document body.", "text/plain")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] is None
    assert body["document"]["status"] == "indexing"
    assert body["document"]["metadata"]["lightrag"]["track_id"] == "track-123"
    assert body["document"]["metadata"]["lightrag"]["document_id"] == "external-manual.txt"


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

