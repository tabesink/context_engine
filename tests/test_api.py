import json
import os
from datetime import UTC, datetime
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./.data/test_context_engine.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["INDEX_JOBS_INLINE"] = "true"
Path(".data").mkdir(parents=True, exist_ok=True)
Path(".data/test_context_engine.db").unlink(missing_ok=True)

import pytest  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.core.config import Settings, get_settings  # noqa: E402
from app.document_processing.models import (  # noqa: E402
    DocumentAsset,
    DocumentBlock,
    DocumentPage,
    DocumentSection,
    DocumentStructure,
    SourceChunk,
)
from app.document_processing.pipeline import TextDoclingParser  # noqa: E402
from app.document_processing.storage_paths import DocumentStoragePaths  # noqa: E402
from app.domain.models import DocumentStatus, JobStatus, UserRole  # noqa: E402
from app.integrations.lightrag_remote_adapter import LightRAGRemoteAdapter  # noqa: E402
from app.lightrag_deploy.models import (  # noqa: E402
    LightRAGDomain,
    LightRAGDomainCreateRequest,
    LightRAGDomainOperationResult,
    LightRAGDomainRemoveResponse,
)
from app.lightrag_deploy.service import LightRAGDomainService  # noqa: E402
from app.lightrag_deploy.settings import LightRAGDeploySettings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.lightrag_ingestion_service import LightRAGIngestionService, RedisIngestLock  # noqa: E402
from app.services.job_service import JobService  # noqa: E402
from app.storage.db import SessionLocal, create_db_and_tables  # noqa: E402
from app.storage.repositories.document_processing import DocumentProcessingRepository  # noqa: E402
from app.storage.repositories.jobs import JobRepository  # noqa: E402
from app.storage.repositories.lightrag_domain_lifecycle import (  # noqa: E402
    LightRAGDomainLifecycleRepository,
)
from app.storage.repositories.documents import DocumentRepository  # noqa: E402
from app.storage.repositories.logs import LogRepository  # noqa: E402
from app.storage.repositories.users import UserRepository  # noqa: E402
from app.storage.tables import LightRAGDomainLifecycleRow  # noqa: E402
from app.workers.tasks import poll_lightrag_statuses, run_document_ingest_job  # noqa: E402


@pytest.fixture(autouse=True)
def _settings_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    manifest_root = tmp_path_factory.mktemp("lightrag-manifest")
    manifest_path = manifest_root / "domains.json"
    manifest_path.write_text(
        (
            '{"domains":['
            '{"id":"default","display_name":"Default","base_url":"http://lightrag-default.local","status":"ready","is_default":true},'
            '{"id":"fatigue","display_name":"Fatigue","base_url":"http://lightrag-fatigue.local","status":"ready"}'
            "]}"
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(manifest_path))
    get_settings.cache_clear()
    create_db_and_tables()
    with SessionLocal() as session:
        session.query(LightRAGDomainLifecycleRow).delete()
        session.commit()
    yield
    get_settings.cache_clear()


def _seed_users() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        users = UserRepository(session)
        if not users.get_by_email("admin@example.com"):
            users.create(email="admin@example.com", password="secret", role=UserRole.ADMIN)
        if not users.get_by_email("user@example.com"):
            users.create(email="user@example.com", password="secret", role=UserRole.USER)


def _login(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": username, "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _configure_lightrag_manifest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    domains: dict[str, str],
) -> None:
    settings = LightRAGDeploySettings(
        enabled=True,
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag/domains",
        manifest_path=tmp_path / "lightrag/domains.json",
        compose_file=tmp_path / "lightrag/compose.yml",
        deleted_root=tmp_path / "lightrag/deleted",
    )
    service = LightRAGDomainService(settings=settings)
    for domain_id, display_name in domains.items():
        service.create_domain(
            LightRAGDomainCreateRequest(domain_id=domain_id, display_name=display_name)
        )
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(settings.manifest_path))
    get_settings.cache_clear()


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_auth_login_returns_bearer_token_contract() -> None:
    with TestClient(app) as client:
        _seed_users()
        response = client.post(
            "/auth/login",
            json={"username": "admin@example.com", "password": "secret"},
        )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert body["token_type"] == "bearer"


def test_auth_login_rejects_missing_username() -> None:
    with TestClient(app) as client:
        _seed_users()
        response = client.post("/auth/login", json={"password": "secret"})

    assert response.status_code == 422


def test_auth_login_rejects_invalid_credentials() -> None:
    with TestClient(app) as client:
        _seed_users()
        response = client.post(
            "/auth/login",
            json={"username": "admin@example.com", "password": "bad-password"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}


def test_auth_me_requires_bearer_token() -> None:
    with TestClient(app) as client:
        _seed_users()
        response = client.get("/auth/me")

    assert response.status_code == 401


def test_auth_me_rejects_invalid_token() -> None:
    with TestClient(app) as client:
        _seed_users()
        response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication token"}


def test_auth_me_returns_current_user_with_valid_token() -> None:
    with TestClient(app) as client:
        _seed_users()
        headers = _login(client, "admin@example.com")
        response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["id"], str)
    assert body["id"]
    assert body["username"] == "admin@example.com"
    assert body["role"] == "admin"
    assert body["is_active"] is True


def test_auth_me_rejects_inactive_user() -> None:
    with TestClient(app) as client:
        _seed_users()
        headers = _login(client, "user@example.com")
        with SessionLocal() as session:
            user = UserRepository(session).get_by_email("user@example.com")
            assert user is not None
            user.is_active = False
            session.add(user)
            session.commit()
        response = client.get("/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"detail": "User is inactive or missing"}


def test_admin_users_routes_require_admin() -> None:
    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get("/admin/users", headers=user_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_users_role_only_lifecycle() -> None:
    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")

        listing = client.get("/admin/users", headers=admin_headers)
        assert listing.status_code == 200
        existing_users = listing.json()
        assert len(existing_users) >= 2

        created = client.post(
            "/admin/users",
            headers=admin_headers,
            json={
                "username": "operator@example.com",
                "password": "operator-secret",
                "role": "user",
            },
        )
        assert created.status_code == 200
        created_user = created.json()
        assert created_user["username"] == "operator@example.com"
        assert created_user["role"] == "user"

        promoted = client.patch(
            f"/admin/users/{created_user['id']}",
            headers=admin_headers,
            json={"role": "admin"},
        )
        assert promoted.status_code == 200
        assert promoted.json()["role"] == "admin"

        reset_password = client.post(
            f"/admin/users/{created_user['id']}/reset-password",
            headers=admin_headers,
            json={"new_password": "operator-secret-updated"},
        )
        assert reset_password.status_code == 204

        removed = client.delete(
            f"/admin/users/{created_user['id']}",
            headers=admin_headers,
        )
        assert removed.status_code == 204


def test_readiness_checks_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeHealthResponse:
        status_code = 200

    monkeypatch.setattr("app.services.readiness_service.httpx.get", lambda *args, **kwargs: FakeHealthResponse())
    with TestClient(app) as client:
        response = client.get("/health/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["services"]["database"] == "healthy"
    assert body["services"]["redis"] == "healthy"
    assert body["services"]["lightrag"] == "healthy"
    assert body["services"]["domain_registry"] == "healthy"
    assert list(body["services"].keys()) == ["database", "redis", "lightrag", "domain_registry"]
    assert list(body["details"].keys()) == ["database", "redis", "lightrag", "domain_registry"]
    assert body["details"]["database"]["status"] == "healthy"
    assert body["details"]["database"]["reason"] is None
    assert isinstance(body["details"]["database"]["latency_ms"], int)
    assert body["details"]["database"]["latency_ms"] >= 0
    assert isinstance(body["details"]["database"]["checked_at"], str)
    assert body["details"]["database"]["checked_at"]
    assert body["details"]["redis"]["status"] == "healthy"
    assert body["details"]["redis"]["reason"] == "Redis check skipped because inline jobs are enabled."


def test_readiness_reports_not_ready_when_default_lightrag_unhealthy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeHealthResponse:
        status_code = 503

    monkeypatch.setattr("app.services.readiness_service.httpx.get", lambda *args, **kwargs: FakeHealthResponse())
    with TestClient(app) as client:
        response = client.get("/health/readiness")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["services"]["database"] == "healthy"
    assert body["services"]["domain_registry"] == "healthy"
    assert body["services"]["lightrag"] == "unhealthy"
    assert body["details"]["lightrag"]["status"] == "unhealthy"
    assert body["details"]["lightrag"]["reason"] == "LightRAG health endpoint returned HTTP 503."


def test_readiness_reports_not_ready_when_database_unhealthy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeHealthResponse:
        status_code = 200

    def broken_execute(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("db is down")

    monkeypatch.setattr("app.services.readiness_service.httpx.get", lambda *args, **kwargs: FakeHealthResponse())
    monkeypatch.setattr("sqlalchemy.orm.session.Session.execute", broken_execute)
    with TestClient(app) as client:
        response = client.get("/health/readiness")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["services"]["database"] == "unhealthy"
    assert body["details"]["database"]["status"] == "unhealthy"
    assert body["details"]["database"]["reason"] == "Database query failed: RuntimeError (db is down)"


def test_readiness_reports_not_ready_when_registry_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(Path(".data/missing-domains.json")))
    get_settings.cache_clear()
    with TestClient(app) as client:
        response = client.get("/health/readiness")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["services"]["domain_registry"] == "unhealthy"
    assert body["services"]["lightrag"] == "unhealthy"
    assert body["details"]["domain_registry"]["status"] == "unhealthy"
    assert body["details"]["domain_registry"]["reason"].startswith("Domain registry is unavailable:")
    assert body["details"]["lightrag"]["reason"] == "Default LightRAG domain is unavailable."


def test_readiness_reports_not_ready_when_redis_unhealthy_in_queue_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeHealthResponse:
        status_code = 200

    class BrokenRedis:
        def ping(self) -> bool:
            raise RuntimeError("redis down")

    monkeypatch.setenv("INDEX_JOBS_INLINE", "false")
    get_settings.cache_clear()
    monkeypatch.setattr("app.services.readiness_service.httpx.get", lambda *args, **kwargs: FakeHealthResponse())
    monkeypatch.setattr(
        "app.services.readiness_service.redis.Redis.from_url",
        lambda *args, **kwargs: BrokenRedis(),
    )

    with TestClient(app) as client:
        response = client.get("/health/readiness")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["services"]["database"] == "healthy"
    assert body["services"]["redis"] == "unhealthy"
    assert body["details"]["redis"]["status"] == "unhealthy"
    assert body["details"]["redis"]["reason"] == "Redis ping failed: RuntimeError (redis down)"


def test_readiness_reports_queue_consumer_warning_when_workers_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeHealthResponse:
        status_code = 200

    class FakeRedis:
        def ping(self) -> bool:
            return True

        def scard(self, key: str) -> int:
            assert key == "rq:workers"
            return 0

        def llen(self, key: str) -> int:
            assert key == "rq:queue:indexing"
            return 3

    monkeypatch.setenv("INDEX_JOBS_INLINE", "false")
    get_settings.cache_clear()
    monkeypatch.setattr("app.services.readiness_service.httpx.get", lambda *args, **kwargs: FakeHealthResponse())
    monkeypatch.setattr("app.services.readiness_service.redis.Redis.from_url", lambda *args, **kwargs: FakeRedis())

    with TestClient(app) as client:
        response = client.get("/health/readiness")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["details"]["queue_consumers"]["status"] == "unhealthy"
    assert body["details"]["queue_consumers"]["reason"] == "No indexing workers detected; queue depth=3."
    assert body["warnings"] == [
        "No indexing workers detected while INDEX_JOBS_INLINE=false. Start docker compose (recommended) or run worker and status poller manually."
    ]


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
            data={"lightrag_domain_id": "default"},
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
            json={
                "query": "where are installation steps",
                "mode": "navigation",
                "top_k": 3,
                "lightrag_domain_id": "default",
            },
        )
        assert retrieve.status_code == 200
        body = retrieve.json()
        assert body["mode"] == "navigation"
        assert body["evidence"][0]["source_engine"] == "navigation"
        assert "answer" not in body

    with SessionLocal() as session:
        latest_query_log = LogRepository(session).list_queries(limit=1)[0]
        assert latest_query_log.query == ""


def test_removed_query_routes_return_404() -> None:
    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        payload = {"query": "where are installation steps", "mode": "navigation", "top_k": 3}

        assert client.post("/query", headers=user_headers, json=payload).status_code == 404
        assert client.post("/query/answer", headers=user_headers, json=payload).status_code == 404
        assert client.post("/query/retrieve", headers=user_headers, json=payload).status_code == 404


def test_admin_list_endpoints_are_paginated() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        users = UserRepository(session)
        admin = users.get_by_email("admin@example.com") or users.create(
            email="admin@example.com", password="secret", role=UserRole.ADMIN
        )
        for index in range(3):
            document = DocumentRepository(session).create(
                owner_id=admin.id,
                filename=f"manual-{index}.txt",
                content_type="text/plain",
                storage_path=f".data/uploads/manual-{index}.txt",
                metadata={},
            )
            JobRepository(session).create(kind="document_ingest", document_id=document.id)
        logs = LogRepository(session)
        logs.record_audit(actor_id=admin.id, event="test", target_id=None, metadata={})
        logs.record_audit(actor_id=admin.id, event="test", target_id=None, metadata={})
        logs.record_query(
            user_id=admin.id,
            query="stored query",
            mode="navigation",
            latency_ms=1,
            evidence_count=0,
        )
        logs.record_query(
            user_id=admin.id,
            query="stored query",
            mode="navigation",
            latency_ms=1,
            evidence_count=0,
        )

    with TestClient(app) as client:
        admin_headers = _login(client, "admin@example.com")
        assert len(client.get("/admin/documents?limit=2", headers=admin_headers).json()) == 2
        assert len(client.get("/jobs?limit=2", headers=admin_headers).json()) == 2
        assert len(client.get("/admin/audit-logs?limit=1", headers=admin_headers).json()) == 1
        assert len(client.get("/admin/query-logs?limit=1", headers=admin_headers).json()) == 1


def test_retrieve_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/retrieve",
            json={"query": "where are installation steps", "mode": "navigation", "top_k": 3},
        )

    assert response.status_code == 401


def test_lightrag_settings_default_to_registry_required(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.lightrag_domain_registry.name == "domains.json"


def test_settings_reject_sqlite_outside_test() -> None:
    with pytest.raises(ValidationError, match="SQLite is only allowed"):
        Settings(_env_file=None, environment="local", database_url="sqlite:///./.data/local.db")


def test_settings_require_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None, environment="test")


def test_production_settings_reject_unsafe_defaults() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            environment="production",
            database_url="postgresql+psycopg://user:pass@db:5432/app",
            secret_key="dev-secret-change-me",
            allowed_origins=["https://app.example"],
            seed_admin_password="safe-production-password",
        )

    with pytest.raises(ValidationError, match="ALLOWED_ORIGINS"):
        Settings(
            _env_file=None,
            environment="production",
            database_url="postgresql+psycopg://user:pass@db:5432/app",
            secret_key="safe-production-secret",
            allowed_origins=["*"],
            seed_admin_password="safe-production-password",
        )

    with pytest.raises(ValidationError, match="SEED_ADMIN_PASSWORD"):
        Settings(
            _env_file=None,
            environment="production",
            database_url="postgresql+psycopg://user:pass@db:5432/app",
            secret_key="safe-production-secret",
            allowed_origins=["https://app.example"],
            seed_admin_password="admin123",
        )


def test_staging_settings_reject_unsafe_defaults() -> None:
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(
            _env_file=None,
            environment="staging",
            database_url="postgresql+psycopg://user:pass@db:5432/app",
            secret_key="dev-secret-change-me",
            allowed_origins=["https://staging.example"],
            seed_admin_password="safe-staging-password",
        )

    with pytest.raises(ValidationError, match="ALLOWED_ORIGINS"):
        Settings(
            _env_file=None,
            environment="staging",
            database_url="postgresql+psycopg://user:pass@db:5432/app",
            secret_key="safe-staging-secret",
            allowed_origins=["*"],
            seed_admin_password="safe-staging-password",
        )

    with pytest.raises(ValidationError, match="SEED_ADMIN_PASSWORD"):
        Settings(
            _env_file=None,
            environment="staging",
            database_url="postgresql+psycopg://user:pass@db:5432/app",
            secret_key="safe-staging-secret",
            allowed_origins=["https://staging.example"],
            seed_admin_password="admin",
        )


def test_lightrag_settings_use_registry_without_base_url(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "domains.json"
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(registry_path))
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.lightrag_domain_registry == registry_path


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
    assert "should_run_toc_refiner" not in body


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
            },
            status=DocumentStatus.READY,
        )
        chunk_id = f"{document.id}-source-chunk-1"
        asset_id = f"{document.id}-asset-1"
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=document.id,
                source_file=document.storage_path,
                pages=[DocumentPage(page_number=1, text="Page one content")],
                sections=[
                    DocumentSection(
                        section_id=f"{document.id}-sec-1",
                        document_id=document.id,
                        title="Safety",
                        level=1,
                    )
                ],
                source_chunks=[
                    SourceChunk(
                        chunk_id=chunk_id,
                        document_id=document.id,
                        section_id=f"{document.id}-sec-1",
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
    assert "track_id" not in status.json()["lightrag"]
    assert status.json()["structure"] == {
        "has_pages": True,
        "has_sections": True,
        "has_chunks": True,
        "has_assets": True,
    }
    assert "navigation" not in status.json()


def test_admin_ingestion_status_available_while_document_is_indexing() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="indexing.txt",
            content_type="text/plain",
            storage_path=".data/uploads/indexing.txt",
            metadata={
                "lightrag": {"domain_id": "default", "track_id": "track-indexing", "status": "indexing"}
            },
            status=DocumentStatus.INDEXING,
        )
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.get(
            f"/admin/documents/{document_id}/ingestion-status",
            headers=admin_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert body["status"] == "indexing"
    assert "track_id" not in body["lightrag"]


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


def test_retrieve_uses_remote_lightrag(monkeypatch: pytest.MonkeyPatch) -> None:
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
                metadata={
                    "source_path": "manual.pdf",
                    "document_title": "Service Manual",
                    "chunk_id": "chunk-1",
                    "reference_id": "ref-1",
                },
            )
        ]

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")

        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={
                "query": "summarize remote context",
                "mode": "auto",
                "top_k": 3,
                "lightrag_domain_id": "default",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["evidence"][0]["source_engine"] == "lightrag"
    assert body["evidence"][0]["text"] == "Remote context for summarize remote context"
    assert body["evidence"][0]["source_path"] == "manual.pdf"
    assert body["evidence"][0]["document_title"] == "Service Manual"
    assert body["evidence"][0]["chunk_id"] == "chunk-1"
    assert body["evidence"][0]["reference_id"] == "ref-1"


def test_admin_upload_queues_lightrag_ingestion_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "domains.json"
    manifest_path.write_text(
        '{"domains":[{"id":"default","display_name":"Default","base_url":"http://lightrag-default.local","status":"ready"}]}',
        encoding="utf-8",
    )
    monkeypatch.setenv("INDEX_JOBS_INLINE", "false")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(manifest_path))
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
            data={"lightrag_domain_id": "default"},
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
        assert job.kind == "document_ingest"
        assert job.document_id == body["document"]["id"]


def test_admin_upload_requires_lightrag_domain_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", ".data/missing-lightrag-domains.json")
    get_settings.cache_clear()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            files={"file": ("manual.txt", b"Remote document body.", "text/plain")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "lightrag_domain_id is required"


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
    monkeypatch.setenv("INDEX_JOBS_INLINE", "false")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(settings.manifest_path))
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
    body = response.json()
    metadata = body["document"]["metadata"]["lightrag"]
    assert metadata["domain_id"] == "fatigue"
    assert metadata["status"] == "queued"
    with SessionLocal() as session:
        stored = DocumentRepository(session).get(body["document"]["id"])
    assert stored is not None
    assert stored.lightrag_domain_id == "fatigue"


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
            f"/admin/documents/{document_id}/refresh-status",
            headers=admin_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["metadata"]["lightrag"]["document_id"] == "remote-doc"


def test_admin_refresh_lightrag_status_reports_missing_provider_secret_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_db_and_tables()
    get_settings.cache_clear()

    def fake_document_status(self: LightRAGRemoteAdapter, track_id: str) -> dict:
        del self
        assert track_id == "track-1"
        return {
            "document_id": "remote-doc",
            "track_id": track_id,
            "status": "failed",
            "error": "'OPENAI_API_KEY'",
        }

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
            f"/admin/documents/{document_id}/refresh-status",
            headers=admin_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert (
        body["error_message"]
        == "Missing provider secret: OPENAI_API_KEY. Configure it in AI Settings > Provider secrets and retry ingestion."
    )
    assert body["metadata"]["lightrag"]["failure_reason"] == "missing_provider_secrets"
    assert body["metadata"]["lightrag"]["missing_provider_secrets"] == ["OPENAI_API_KEY"]


def test_poller_refreshes_pending_lightrag_statuses(monkeypatch: pytest.MonkeyPatch) -> None:
    create_db_and_tables()
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

    poll_lightrag_statuses()

    with SessionLocal() as session:
        refreshed = DocumentRepository(session).get(document_id)

    assert refreshed is not None
    assert refreshed.status == "ready"
    assert refreshed.meta["lightrag"]["status"] == "ready"


def test_poller_continues_and_marks_missing_domain_document_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_db_and_tables()
    get_settings.cache_clear()

    def fake_document_status(self: LightRAGRemoteAdapter, track_id: str) -> dict:
        del self
        assert track_id == "track-ok"
        return {"document_id": "remote-doc", "track_id": track_id, "status": "ready"}

    monkeypatch.setattr(LightRAGRemoteAdapter, "document_status", fake_document_status)
    with SessionLocal() as session:
        missing_domain_doc = DocumentRepository(session).create(
            owner_id=None,
            filename="missing-domain.txt",
            content_type="text/plain",
            storage_path=".data/uploads/missing-domain.txt",
            metadata={
                "semantic_engine": "lightrag",
                "lightrag": {"domain_id": "missing-domain", "track_id": "track-missing", "status": "indexing"},
            },
            status=DocumentStatus.INDEXING,
        )
        healthy_doc = DocumentRepository(session).create(
            owner_id=None,
            filename="healthy.txt",
            content_type="text/plain",
            storage_path=".data/uploads/healthy.txt",
            metadata={
                "semantic_engine": "lightrag",
                "lightrag": {"domain_id": "default", "track_id": "track-ok", "status": "indexing"},
            },
            status=DocumentStatus.INDEXING,
        )
        missing_domain_doc_id = missing_domain_doc.id
        healthy_doc_id = healthy_doc.id

    poll_lightrag_statuses()

    with SessionLocal() as session:
        failed_doc = DocumentRepository(session).get(missing_domain_doc_id)
        refreshed_doc = DocumentRepository(session).get(healthy_doc_id)

    assert failed_doc is not None
    assert failed_doc.status == "failed"
    assert failed_doc.meta["lightrag"]["status"] == "failed"
    assert "does not exist" in (failed_doc.error_message or "")

    assert refreshed_doc is not None
    assert refreshed_doc.status == "ready"
    assert refreshed_doc.meta["lightrag"]["status"] == "ready"


def test_admin_refresh_lightrag_status_rejects_unknown_upstream_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_db_and_tables()
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
            f"/admin/documents/{document_id}/refresh-status",
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
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(settings.manifest_path))
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

    assert response.status_code == 404
    assert response.json()["detail"] == "LightRAG domain 'missing' does not exist"


def test_admin_upload_fails_when_domain_provider_secret_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "domains.json"
    now = "2026-05-18T14:30:00Z"
    manifest_path.write_text(
        json.dumps(
            {
                "domains": [
                    {
                        "id": "fatigue",
                        "display_name": "Fatigue",
                        "workspace": "fatigue",
                        "postgres_database": "lightrag_fatigue",
                        "postgres_user": "lightrag_fatigue",
                        "host": "127.0.0.1",
                        "host_port": 9621,
                        "container_port": 9621,
                        "base_url": "http://127.0.0.1:9621",
                        "host_base_url": "http://127.0.0.1:9621",
                        "container_base_url": "http://lightrag_fatigue:9621",
                        "container_name": "context_engine_lightrag_fatigue",
                        "service_name": "lightrag_fatigue",
                        "status": "ready",
                        "paths": {"root": str(tmp_path / "lightrag" / "domains" / "fatigue")},
                        "created_at": now,
                        "updated_at": now,
                        "embedding": {
                            "profile_id": "openai-text-embedding-3-small",
                            "provider": "openai",
                            "binding": "openai",
                            "base_url": "https://api.openai.com/v1",
                            "api_key_env_var": "OPENAI_API_KEY",
                            "model": "text-embedding-3-small",
                            "dimensions": 1536,
                            "token_limit": 8192,
                            "send_dimensions": False,
                            "use_base64": True,
                            "fingerprint": "openai:text-embedding-3-small:1536",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("INDEX_JOBS_INLINE", "false")
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(manifest_path))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            data={"lightrag_domain_id": "fatigue"},
            files={"file": ("manual.txt", b"Remote document body.", "text/plain")},
        )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "LightRAG domain 'fatigue' is missing required provider secret: OPENAI_API_KEY"
    )


def test_retrieve_uses_selected_lightrag_domain(monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_retrieve_rejects_unknown_lightrag_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()

    def fake_retrieve(self: LightRAGRemoteAdapter, **kwargs):
        del self, kwargs
        pytest.fail("retrieve should not call LightRAG for an unknown domain")

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={"query": "fatigue limits", "mode": "semantic", "lightrag_domain_id": "missing"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "LightRAG domain 'missing' does not exist"


def test_retrieve_empty_evidence_is_successful_empty_result(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()

    def fake_retrieve(self: LightRAGRemoteAdapter, **kwargs):
        del self, kwargs
        return []

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={
                "query": "missing evidence",
                "mode": "semantic",
                "include_assets": True,
                "lightrag_domain_id": "default",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "missing evidence"
    assert body["mode"] == "semantic"
    assert body["evidence"] == []
    assert body["assets"] == []
    assert body["debug"] is None


def test_retrieve_requires_lightrag_domain_id() -> None:
    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={"query": "missing evidence", "mode": "semantic"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "lightrag_domain_id is required"


def test_retrieve_debug_is_admin_only(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()

    def fake_retrieve(self: LightRAGRemoteAdapter, **kwargs):
        del self, kwargs
        return []

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        admin_headers = _login(client, "admin@example.com")

        user_response = client.post(
            "/retrieve",
            headers=user_headers,
            json={
                "query": "debug details",
                "mode": "semantic",
                "include_debug": True,
                "lightrag_domain_id": "default",
            },
        )
        admin_response = client.post(
            "/retrieve",
            headers=admin_headers,
            json={
                "query": "debug details",
                "mode": "semantic",
                "include_debug": True,
                "lightrag_domain_id": "default",
            },
        )

    assert user_response.status_code == 200
    assert user_response.json()["debug"] is None
    assert admin_response.status_code == 200
    assert admin_response.json()["debug"] == {
        "requested_mode": "semantic",
        "selected_engine": "lightrag",
    }


def test_retrieve_rejects_document_ids_from_different_lightrag_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    get_settings.cache_clear()

    seen_paths: list[str] = []
    seen_domains: list[str | None] = []

    def fake_for_domain(cls, domain: str | None = None):
        seen_domains.append(domain)
        return cls(base_url="http://lightrag.local")

    def fake_get_json(self: LightRAGRemoteAdapter, path: str, *, params: dict | None = None):
        del self, params
        seen_paths.append(path)
        if path == "/graphs":
            return {
                "nodes": [
                    {
                        "id": "n1",
                        "labels": ["Pump"],
                        "properties": {"entity_id": "Pump", "entity_type": "equipment"},
                    }
                ],
                "edges": [
                    {
                        "id": "e1",
                        "source": "n1",
                        "target": "n2",
                        "type": "connects",
                        "properties": {"weight": 2, "description": "connects to"},
                    }
                ],
                "is_truncated": True,
            }
        if path == "/graph/label/list":
            return ["Pump", "Valve"]
        if path == "/graph/label/popular":
            return ["Pump"]
        if path == "/graph/label/search":
            return ["Pump"]
        return {}

    monkeypatch.setattr(LightRAGRemoteAdapter, "for_domain", classmethod(fake_for_domain))
    monkeypatch.setattr(LightRAGRemoteAdapter, "get_json", fake_get_json)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        graph = client.get("/lightrag/domains/fatigue/graphs?label=Pump", headers=user_headers)
        labels = client.get("/lightrag/domains/fatigue/graph/labels", headers=user_headers)
        popular = client.get("/lightrag/domains/fatigue/graph/labels/popular?limit=2", headers=user_headers)
        search = client.get("/lightrag/domains/fatigue/graph/labels/search?q=Pu&limit=2", headers=user_headers)

    assert graph.status_code == 200
    assert labels.status_code == 200
    assert popular.status_code == 200
    assert search.status_code == 200
    assert seen_domains == ["fatigue", "fatigue", "fatigue", "fatigue"]
    assert seen_paths == ["/graphs", "/graph/label/list", "/graph/label/popular", "/graph/label/search"]
    assert graph.json() == {
        "nodes": [
            {
                "id": "n1",
                "labels": ["Pump"],
                "display_label": "Pump",
                "entity_type": "equipment",
                "properties": {"entity_id": "Pump", "entity_type": "equipment"},
            }
        ],
        "edges": [
            {
                "id": "e1",
                "source": "n1",
                "target": "n2",
                "relation": "connects",
                "weight": 2.0,
                "description": "connects to",
                "properties": {"weight": 2, "description": "connects to"},
            }
        ],
        "truncated": True,
    }
    assert labels.json() == {"labels": ["Pump", "Valve"]}
    assert popular.json() == {"labels": ["Pump"]}
    assert search.json() == {"query": "Pu", "limit": 2, "labels": ["Pump"]}


def test_lightrag_graph_proxy_rejects_unknown_domain_before_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()

    def fake_for_domain(cls, domain: str):
        del cls, domain
        pytest.fail("graph proxy should not resolve an adapter for an unknown domain")

    monkeypatch.setattr(LightRAGRemoteAdapter, "for_domain", classmethod(fake_for_domain))

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get("/lightrag/domains/missing/graphs?label=Pump", headers=user_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "LightRAG domain 'missing' does not exist"


def test_lightrag_failures_return_stable_errors(monkeypatch: pytest.MonkeyPatch) -> None:
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
            json={
                "query": "summarize remote context",
                "mode": "semantic",
                "lightrag_domain_id": "default",
            },
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "LightRAG service unavailable"


def test_lightrag_upstream_failures_return_bad_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()

    def fake_retrieve(self: LightRAGRemoteAdapter, **kwargs):
        del self, kwargs
        from app.integrations.lightrag_remote_adapter import LightRAGUpstreamError

        raise LightRAGUpstreamError("LightRAG upstream request failed", upstream_status=502)

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={
                "query": "summarize remote context",
                "mode": "semantic",
                "lightrag_domain_id": "default",
            },
        )

    assert response.status_code == 502
    assert response.json()["detail"] == "LightRAG upstream request failed"


def test_retrieve_response_contract_fields_are_stable(monkeypatch: pytest.MonkeyPatch) -> None:
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
        del self, mode, top_k, document_ids, domain
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
                metadata={
                    "source_path": "manual.pdf",
                    "document_title": "Service Manual",
                    "chunk_id": "chunk-1",
                    "reference_id": "ref-1",
                },
            )
        ]

    monkeypatch.setattr(LightRAGRemoteAdapter, "retrieve", fake_retrieve)

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.post(
            "/retrieve",
            headers=user_headers,
            json={
                "query": "summarize remote context",
                "mode": "semantic",
                "top_k": 3,
                "lightrag_domain_id": "default",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert "assets" in body
    assert isinstance(body["assets"], list)
    evidence = body["evidence"][0]
    assert set(evidence.keys()) == {
        "evidence_id",
        "document_id",
        "source_engine",
        "text",
        "score",
        "page_start",
        "page_end",
        "section_title",
        "source_path",
        "document_title",
        "chunk_id",
        "reference_id",
        "metadata",
    }
    assert evidence["source_path"] == "manual.pdf"
    assert evidence["document_title"] == "Service Manual"
    assert evidence["chunk_id"] == "chunk-1"
    assert evidence["reference_id"] == "ref-1"


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
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(tmp_path / "lightrag/domains.json"))
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


def test_lightrag_domain_admin_api_lifecycle_routes_remain_available() -> None:
    from app.api.routes import lightrag_admin

    now = datetime(2026, 5, 25, tzinfo=UTC)
    domains: dict[str, LightRAGDomain] = {}

    def domain_payload(domain_id: str, *, status: str = "configured") -> LightRAGDomain:
        return LightRAGDomain(
            id=domain_id,
            display_name=f"{domain_id.title()} Manuals",
            host_port=9621,
            base_url=f"http://lightrag-{domain_id}:9621",
            host_base_url="http://127.0.0.1:9621",
            container_base_url=f"http://lightrag-{domain_id}:9621",
            container_name=f"lightrag_{domain_id}",
            service_name=f"lightrag_{domain_id}",
            status=status,
            paths={"domain_root": f".data/lightrag/domains/{domain_id}"},
            created_at=now,
            updated_at=now,
        )

    class FakeDomainService:
        class _Settings:
            enabled = True

        settings = _Settings()

        def list_domains(self) -> list[LightRAGDomain]:
            return list(domains.values())

        def create_domain(self, request: LightRAGDomainCreateRequest) -> LightRAGDomain:
            domain = domain_payload(request.domain_id, status="configured")
            domains[request.domain_id] = domain
            return domain

        def get_domain(self, domain_id: str) -> LightRAGDomain:
            return domains[domain_id]

        def up(self, domain_id: str) -> LightRAGDomainOperationResult:
            domains[domain_id] = domain_payload(domain_id, status="running")
            return LightRAGDomainOperationResult(
                id=domain_id,
                operation="up",
                status="succeeded",
                service_name=f"lightrag_{domain_id}",
            )

        def down(self, domain_id: str) -> LightRAGDomainOperationResult:
            domains[domain_id] = domain_payload(domain_id, status="stopped")
            return LightRAGDomainOperationResult(
                id=domain_id,
                operation="down",
                status="succeeded",
                service_name=f"lightrag_{domain_id}",
            )

        def recreate(self, domain_id: str) -> LightRAGDomainOperationResult:
            domains[domain_id] = domain_payload(domain_id, status="running")
            return LightRAGDomainOperationResult(
                id=domain_id,
                operation="recreate",
                status="succeeded",
                service_name=f"lightrag_{domain_id}",
            )

        def regenerate(self, domain_id: str) -> None:
            domains[domain_id] = domain_payload(domain_id, status="configured")

        def remove(self, domain_id: str, *, permanent: bool = False) -> LightRAGDomainRemoveResponse:
            domains.pop(domain_id, None)
            return LightRAGDomainRemoveResponse(
                id=domain_id,
                archived=not permanent,
                permanent=permanent,
                archive_path=None if permanent else f".data/lightrag/deleted/{domain_id}",
            )

    app.dependency_overrides[lightrag_admin.get_domain_service] = lambda: FakeDomainService()
    try:
        with TestClient(app) as client:
            _seed_users()
            admin_headers = _login(client, "admin@example.com")

            create = client.post(
                "/admin/lightrag/domains",
                headers=admin_headers,
                json={"domain_id": "fatigue", "display_name": "Fatigue Manuals"},
            )
            up = client.post("/admin/lightrag/domains/fatigue/up", headers=admin_headers)
            down = client.post("/admin/lightrag/domains/fatigue/down", headers=admin_headers)
            recreate = client.post("/admin/lightrag/domains/fatigue/recreate", headers=admin_headers)
            remove = client.delete("/admin/lightrag/domains/fatigue", headers=admin_headers)

        assert create.status_code == 200
        assert create.json()["id"] == "fatigue"
        assert up.status_code == 200
        assert up.json()["operation"] == "up"
        assert down.status_code == 200
        assert down.json()["operation"] == "down"
        assert recreate.status_code == 200
        assert recreate.json()["operation"] == "recreate"
        assert remove.status_code == 200
        assert remove.json()["archived"] is True
    finally:
        app.dependency_overrides.pop(lightrag_admin.get_domain_service, None)


def test_operation_or_404_maps_failed_operation_to_502() -> None:
    from app.api.routes import lightrag_admin

    def failed_operation(domain_id: str) -> LightRAGDomainOperationResult:
        return LightRAGDomainOperationResult(
            id=domain_id,
            operation="up",
            status="failed",
            service_name="lightrag_test",
            message="port 9622 already allocated",
        )

    with pytest.raises(HTTPException) as exc_info:
        lightrag_admin._operation_or_404(failed_operation, "test")

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail["code"] == "lightrag_domain_operation_failed"
    assert exc_info.value.detail["domain_id"] == "test"
    assert exc_info.value.detail["operation"] == "up"
    assert exc_info.value.detail["status"] == "failed"
    assert exc_info.value.detail["service_name"] == "lightrag_test"
    assert exc_info.value.detail["message"] == "port 9622 already allocated"


def test_operation_or_404_returns_successful_operation() -> None:
    from app.api.routes import lightrag_admin

    def successful_operation(domain_id: str) -> LightRAGDomainOperationResult:
        return LightRAGDomainOperationResult(
            id=domain_id,
            operation="up",
            status="succeeded",
            service_name="lightrag_test",
            message=None,
        )

    result = lightrag_admin._operation_or_404(successful_operation, "test")

    assert result.status == "succeeded"


def test_lightrag_admin_and_user_domain_responses_do_not_leak_provider_secrets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bedrock_key = "test-bedrock-key"
    embedding_key = "test-openai-key"
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ENABLED", "true")
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ROOT", str(tmp_path / "lightrag"))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_ROOT", str(tmp_path / "lightrag/domains"))
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(tmp_path / "lightrag/domains.json"))
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
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(settings.manifest_path))
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
        "host_port": 9621,
        "is_healthy": None,
        "is_default": True,
        "status": "configured",
        "retrieval_defaults": {
            "top_k": 10,
            "chunk_top_k": 10,
            "chunk_rerank_top_k": 10,
            "max_token_for_text_unit": 4000,
            "max_token_for_global_context": 4000,
            "max_token_for_local_context": 4000,
        },
    }
    assert "paths" not in domain
    assert "container_name" not in domain
    assert unauthenticated.status_code == 401


def test_archived_domain_is_hidden_from_user_lists_and_document_reads() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        fatigue_document = DocumentRepository(session).create(
            owner_id=None,
            lightrag_domain_id="fatigue",
            filename="fatigue.txt",
            content_type="text/plain",
            storage_path=".data/uploads/fatigue.txt",
            metadata={"lightrag": {"domain_id": "fatigue"}},
            status=DocumentStatus.READY,
        )
        active_document = DocumentRepository(session).create(
            owner_id=None,
            lightrag_domain_id="default",
            filename="default.txt",
            content_type="text/plain",
            storage_path=".data/uploads/default.txt",
            metadata={"lightrag": {"domain_id": "default"}},
            status=DocumentStatus.READY,
        )
        fatigue_document_id = fatigue_document.id
        active_document_id = active_document.id
        LightRAGDomainLifecycleRepository(session).set_state(domain_id="fatigue", state="archived")

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        domains = client.get("/lightrag/domains", headers=user_headers)
        documents = client.get("/documents", headers=user_headers)
        hidden_detail = client.get(f"/documents/{fatigue_document_id}", headers=user_headers)
        hidden_chunks = client.get(f"/documents/{fatigue_document_id}/chunks", headers=user_headers)
        visible_detail = client.get(f"/documents/{active_document_id}", headers=user_headers)

    assert domains.status_code == 200
    domain_ids = {domain["id"] for domain in domains.json()["domains"]}
    assert "default" in domain_ids
    assert "fatigue" not in domain_ids
    assert documents.status_code == 200
    readable_ids = {item["id"] for item in documents.json()}
    assert active_document_id in readable_ids
    assert fatigue_document_id not in readable_ids
    assert hidden_detail.status_code == 404
    assert hidden_chunks.status_code == 404
    assert visible_detail.status_code == 200


def test_archived_domain_blocks_admin_upload_and_retrieval() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        LightRAGDomainLifecycleRepository(session).set_state(domain_id="fatigue", state="archived")

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        user_headers = _login(client, "user@example.com")
        upload = client.post(
            "/admin/documents/upload",
            headers=admin_headers,
            data={"lightrag_domain_id": "fatigue"},
            files={"file": ("blocked.txt", b"blocked", "text/plain")},
        )
        retrieve = client.post(
            "/retrieve",
            headers=user_headers,
            json={"query": "fatigue limits", "mode": "semantic", "lightrag_domain_id": "fatigue"},
        )

    assert upload.status_code == 400
    assert upload.json()["detail"] == "LightRAG domain 'fatigue' is not available"
    assert retrieve.status_code == 400
    assert retrieve.json()["detail"] == "LightRAG domain 'fatigue' is not available"


def test_lightrag_domain_purge_preview_counts_all_domain_documents(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    preview_domain_id = "fatiguepreview"
    storage_root = tmp_path / "uploads"
    storage_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))
    _configure_lightrag_manifest(
        monkeypatch,
        tmp_path,
        {"default": "Default Manuals", preview_domain_id: "Fatigue Manuals"},
    )
    create_db_and_tables()
    with SessionLocal() as session:
        documents = DocumentRepository(session)
        processing = DocumentProcessingRepository(session)
        fatigue_docs = []
        for index, status in enumerate(
            [DocumentStatus.UPLOADED, DocumentStatus.INDEXING, DocumentStatus.FAILED, DocumentStatus.DELETED]
        ):
            path = storage_root / f"fatigue-{index}.txt"
            path.write_text(f"fatigue-{index}", encoding="utf-8")
            fatigue_docs.append(
                documents.create(
                    owner_id=None,
                        lightrag_domain_id=preview_domain_id,
                    filename=path.name,
                    content_type="text/plain",
                    storage_path=str(path),
                        metadata={"lightrag": {"domain_id": preview_domain_id}},
                    status=status,
                )
            )
        default_path = storage_root / "default-0.txt"
        default_path.write_text("default", encoding="utf-8")
        documents.create(
            owner_id=None,
            lightrag_domain_id="default",
            filename=default_path.name,
            content_type="text/plain",
            storage_path=str(default_path),
            metadata={"lightrag": {"domain_id": "default"}},
            status=DocumentStatus.READY,
        )
        first_doc = fatigue_docs[0]
        processing.save_structure(
            DocumentStructure(
                document_id=first_doc.id,
                source_file=first_doc.storage_path,
                pages=[DocumentPage(page_number=1, text="Page one")],
                sections=[
                    DocumentSection(
                        section_id=f"{first_doc.id}-sec-1",
                        document_id=first_doc.id,
                        title="Section one",
                        level=1,
                    )
                ],
                blocks=[
                    DocumentBlock(
                        block_id=f"{first_doc.id}-block-1",
                        document_id=first_doc.id,
                        section_id=f"{first_doc.id}-sec-1",
                        type="paragraph",
                        text="block text",
                    )
                ],
                source_chunks=[
                    SourceChunk(
                        chunk_id=f"{first_doc.id}-chunk-1",
                        document_id=first_doc.id,
                        section_id=f"{first_doc.id}-sec-1",
                        block_ids=[f"{first_doc.id}-block-1"],
                        text="chunk text",
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id=f"{first_doc.id}-asset-1",
                        document_id=first_doc.id,
                        section_id=f"{first_doc.id}-sec-1",
                        block_id=f"{first_doc.id}-block-1",
                        chunk_id=f"{first_doc.id}-chunk-1",
                        asset_type="image",
                        storage_path=f"documents/{first_doc.id}/assets/asset-1.png",
                        thumbnail_path=f"documents/{first_doc.id}/assets/asset-1-thumb.png",
                        content_hash="hash-1",
                    )
                ],
            )
        )

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        preview = client.post(
            f"/admin/lightrag/domains/{preview_domain_id}/purge-preview",
            headers=admin_headers,
        )

    assert preview.status_code == 200
    body = preview.json()
    assert body["domain_id"] == preview_domain_id
    assert body["documents"] == 4
    assert body["original_uploads"] == 4
    assert body["assets"] == 1
    assert body["chunks"] == 1
    assert body["pages"] == 1
    assert body["sections"] == 1
    assert body["blocks"] == 1
    assert body["estimated_bytes"] > 0


def test_lightrag_domain_purge_rejects_confirm_domain_id_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LIGHTRAG_ALLOW_PERMANENT_DELETE", "true")
    _configure_lightrag_manifest(monkeypatch, tmp_path, {"fatigue": "Fatigue Manuals"})
    create_db_and_tables()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.delete(
            "/admin/lightrag/domains/fatigue/purge?confirm_domain_id=wrong",
            headers=admin_headers,
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "confirm_domain_id must match domain_id"


def test_lightrag_domain_purge_requires_permanent_delete_opt_in(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("LIGHTRAG_ALLOW_PERMANENT_DELETE", "false")
    _configure_lightrag_manifest(monkeypatch, tmp_path, {"fatigue": "Fatigue Manuals"})
    create_db_and_tables()

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.delete(
            "/admin/lightrag/domains/fatigue/purge?confirm_domain_id=fatigue",
            headers=admin_headers,
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Permanent LightRAG domain delete is disabled"


def test_lightrag_domain_purge_hard_deletes_domain_documents_and_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    purge_domain_id = "fatiguepurge"
    storage_root = tmp_path / "uploads"
    storage_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ENABLED", "true")
    monkeypatch.setenv("LIGHTRAG_ALLOW_PERMANENT_DELETE", "true")
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ROOT", str(tmp_path / "lightrag"))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_ROOT", str(tmp_path / "lightrag/domains"))
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(tmp_path / "lightrag/domains.json"))
    monkeypatch.setenv("LIGHTRAG_COMPOSE_FILE", str(tmp_path / "lightrag/compose.yml"))
    monkeypatch.setenv("LIGHTRAG_DELETED_ROOT", str(tmp_path / "lightrag/deleted"))
    get_settings.cache_clear()

    deploy_settings = LightRAGDeploySettings.from_app_settings(get_settings())
    domain_service = LightRAGDomainService(settings=deploy_settings)
    domain_service.create_domain(
        LightRAGDomainCreateRequest(domain_id=purge_domain_id, display_name="Fatigue")
    )
    domain_service.create_domain(LightRAGDomainCreateRequest(domain_id="default", display_name="Default"))

    create_db_and_tables()
    with SessionLocal() as session:
        documents = DocumentRepository(session)
        processing = DocumentProcessingRepository(session)
        jobs = JobRepository(session)

        fatigue_path = storage_root / "fatigue.txt"
        fatigue_path.write_text("fatigue", encoding="utf-8")
        default_path = storage_root / "default.txt"
        default_path.write_text("default", encoding="utf-8")

        fatigue_doc = documents.create(
            owner_id=None,
            lightrag_domain_id=purge_domain_id,
            filename="fatigue.txt",
            content_type="text/plain",
            storage_path=str(fatigue_path),
            metadata={"lightrag": {"domain_id": purge_domain_id}},
            status=DocumentStatus.READY,
        )
        default_doc = documents.create(
            owner_id=None,
            lightrag_domain_id="default",
            filename="default.txt",
            content_type="text/plain",
            storage_path=str(default_path),
            metadata={"lightrag": {"domain_id": "default"}},
            status=DocumentStatus.READY,
        )
        processing.save_structure(
            DocumentStructure(
                document_id=fatigue_doc.id,
                source_file=fatigue_doc.storage_path,
                source_chunks=[
                    SourceChunk(
                        chunk_id=f"{fatigue_doc.id}-chunk-1",
                        document_id=fatigue_doc.id,
                        block_ids=[],
                        text="chunk text",
                    )
                ],
            )
        )
        artifact_root = DocumentStoragePaths(storage_root=storage_root).document_root(fatigue_doc.id)
        artifact_file = artifact_root / "assets" / "artifact.png"
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("binary", encoding="utf-8")

        fatigue_job = jobs.create(kind="document_ingest", document_id=fatigue_doc.id)
        jobs.set_status(fatigue_job, JobStatus.RUNNING)
        default_job = jobs.create(kind="document_ingest", document_id=default_doc.id)
        jobs.set_status(default_job, JobStatus.QUEUED)
        fatigue_doc_id = fatigue_doc.id
        default_doc_id = default_doc.id
        fatigue_job_id = fatigue_job.id
        default_job_id = default_job.id

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.delete(
            f"/admin/lightrag/domains/{purge_domain_id}/purge?confirm_domain_id={purge_domain_id}",
            headers=admin_headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["domain_id"] == purge_domain_id
    assert body["state"] == "purged"
    assert body["purged_documents"] == 1
    assert body["purged_original_uploads"] == 1
    assert body["purged_artifact_roots"] == 1
    assert body["canceled_jobs"] == 1
    assert body["deleted_domain_root"] is True

    with SessionLocal() as session:
        documents = DocumentRepository(session)
        jobs = JobRepository(session)
        fatigue_after = documents.get(fatigue_doc_id)
        default_after = documents.get(default_doc_id)
        assert fatigue_after is None
        assert default_after is not None
        assert jobs.get(fatigue_job_id).document_id is None
        assert jobs.get(default_job_id).document_id == default_doc_id

    assert not fatigue_path.exists()
    assert default_path.exists()
    assert not artifact_root.exists()
    assert not (tmp_path / f"lightrag/domains/{purge_domain_id}").exists()
    assert (tmp_path / "lightrag/domains/default").exists()


def test_archive_domain_is_non_destructive_and_blocks_user_document_reads(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / "uploads"
    storage_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("STORAGE_ROOT", str(storage_root))
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ENABLED", "true")
    monkeypatch.setenv("LIGHTRAG_DEPLOY_ROOT", str(tmp_path / "lightrag"))
    monkeypatch.setenv("LIGHTRAG_DOMAINS_ROOT", str(tmp_path / "lightrag/domains"))
    monkeypatch.setenv("LIGHTRAG_DOMAIN_REGISTRY", str(tmp_path / "lightrag/domains.json"))
    monkeypatch.setenv("LIGHTRAG_COMPOSE_FILE", str(tmp_path / "lightrag/compose.yml"))
    monkeypatch.setenv("LIGHTRAG_DELETED_ROOT", str(tmp_path / "lightrag/deleted"))
    get_settings.cache_clear()

    deploy_settings = LightRAGDeploySettings.from_app_settings(get_settings())
    domain_service = LightRAGDomainService(settings=deploy_settings)
    domain_service.create_domain(LightRAGDomainCreateRequest(domain_id="archivecase", display_name="Archive"))
    create_db_and_tables()
    with SessionLocal() as session:
        documents = DocumentRepository(session)
        document_path = storage_root / "archive.txt"
        document_path.write_text("archive", encoding="utf-8")
        document = documents.create(
            owner_id=None,
            lightrag_domain_id="archivecase",
            filename="archive.txt",
            content_type="text/plain",
            storage_path=str(document_path),
            metadata={"lightrag": {"domain_id": "archivecase"}},
            status=DocumentStatus.READY,
        )
        artifact_root = DocumentStoragePaths(storage_root=storage_root).document_root(document.id)
        artifact_file = artifact_root / "assets" / "artifact.png"
        artifact_file.parent.mkdir(parents=True, exist_ok=True)
        artifact_file.write_text("binary", encoding="utf-8")
        document_id = document.id

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        user_headers = _login(client, "user@example.com")
        archive = client.delete("/admin/lightrag/domains/archivecase", headers=admin_headers)
        user_detail = client.get(f"/documents/{document_id}", headers=user_headers)

    assert archive.status_code == 200
    assert archive.json()["archived"] is True
    assert document_path.exists()
    assert artifact_root.exists()
    assert user_detail.status_code == 404


def test_workspace_tree_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/lightrag/domains/default/workspace-tree")

    assert response.status_code == 401


def test_workspace_tree_returns_empty_root_for_valid_domain(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_lightrag_manifest(monkeypatch, tmp_path, {"emptytree": "Empty Tree"})

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get("/lightrag/domains/emptytree/workspace-tree", headers=user_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["domain_id"] == "emptytree"
    assert body["display_name"] == "Empty Tree"
    assert body["document_count"] == 0
    assert body["root"]["id"] == "domain:emptytree"
    assert body["root"]["kind"] == "domain"
    assert body["root"]["children"] == []


def test_workspace_tree_unknown_domain_returns_404(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _configure_lightrag_manifest(monkeypatch, tmp_path, {"manuals404": "Manuals"})

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get("/lightrag/domains/missing/workspace-tree", headers=user_headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "LightRAG domain 'missing' does not exist"


def test_workspace_tree_filters_domain_and_returns_structure_references(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    create_db_and_tables()
    _configure_lightrag_manifest(
        monkeypatch,
        tmp_path,
        {"manualtree": "Manual Tree", "policytree": "Policy Tree"},
    )
    with SessionLocal() as session:
        documents = DocumentRepository(session)
        manual = documents.create(
            owner_id=None,
            filename="manual.pdf",
            content_type="application/pdf",
            storage_path=".data/uploads/manual.pdf",
            metadata={"lightrag": {"domain_id": "manualtree"}},
            status=DocumentStatus.READY,
        )
        fallback = documents.create(
            owner_id=None,
            filename="legacy-manual.pdf",
            content_type="application/pdf",
            storage_path=".data/uploads/legacy-manual.pdf",
            metadata={"lightrag": {"domain": "manualtree"}},
            status=DocumentStatus.READY,
        )
        documents.create(
            owner_id=None,
            filename="policy.pdf",
            content_type="application/pdf",
            storage_path=".data/uploads/policy.pdf",
            metadata={"lightrag": {"domain_id": "policytree"}},
            status=DocumentStatus.READY,
        )
        documents.create(
            owner_id=None,
            filename="indexing.pdf",
            content_type="application/pdf",
            storage_path=".data/uploads/indexing.pdf",
            metadata={"lightrag": {"domain_id": "manualtree"}},
            status=DocumentStatus.INDEXING,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=manual.id,
                source_file=manual.storage_path,
                pages=[DocumentPage(page_number=1, text="Full page text must not leak")],
                sections=[
                    DocumentSection(
                        section_id="intro",
                        document_id=manual.id,
                        title="Introduction",
                        level=1,
                        page_start=1,
                        page_end=1,
                    )
                ],
                source_chunks=[
                    SourceChunk(
                        chunk_id="chunk-1",
                        document_id=manual.id,
                        section_id="intro",
                        block_ids=[],
                        text=(
                            "Short reference label with enough harmless words to form the display "
                            "snippet before the hidden tail appears. "
                            "SECRET_CHUNK_TAIL_SHOULD_NOT_APPEAR_IN_TREE_RESPONSE"
                        ),
                        page_start=1,
                        page_end=1,
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id="asset-1",
                        document_id=manual.id,
                        asset_type="figure",
                        storage_path=".data/assets/asset-1.png",
                        thumbnail_path=".data/assets/asset-1-thumb.png",
                        mime_type="image/png",
                        content_hash="hash-asset-1",
                        page_number=1,
                        section_id="intro",
                        caption="Pump diagram",
                    )
                ],
            )
        )
        manual_id = manual.id
        fallback_id = fallback.id

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        response = client.get("/lightrag/domains/manualtree/workspace-tree", headers=user_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["domain_id"] == "manualtree"
    assert body["document_count"] == 2
    document_nodes = body["root"]["children"]
    document_ids = {node["document_id"] for node in document_nodes}
    assert document_ids == {manual_id, fallback_id}
    assert all(node["filename"] != "policy.pdf" for node in document_nodes)
    assert all(node["filename"] != "indexing.pdf" for node in document_nodes)

    manual_node = next(node for node in document_nodes if node["document_id"] == manual_id)
    fallback_node = next(node for node in document_nodes if node["document_id"] == fallback_id)
    assert fallback_node["metadata"]["structure_available"] is False
    section_node = manual_node["children"][0]
    page_node = section_node["children"][0]
    chunk_node = page_node["children"][0]
    asset_node = page_node["children"][1]
    assert section_node["kind"] == "section"
    assert section_node["section_id"] == "intro"
    assert page_node["kind"] == "page"
    assert page_node["page_number"] == 1
    assert chunk_node["kind"] == "chunk"
    assert chunk_node["chunk_id"] == "chunk-1"
    assert "SECRET_CHUNK_TAIL_SHOULD_NOT_APPEAR_IN_TREE_RESPONSE" not in response.text
    assert "Full page text must not leak" not in response.text
    assert asset_node["kind"] == "asset"
    assert asset_node["asset_id"] == "asset-1"
    assert asset_node["thumbnail_url"] == f"/documents/{manual_id}/assets/asset-1/thumbnail"


def test_workspace_tree_supports_depth_and_asset_query_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    create_db_and_tables()
    _configure_lightrag_manifest(monkeypatch, tmp_path, {"contracttree": "Contract Tree"})
    with SessionLocal() as session:
        documents = DocumentRepository(session)
        manual = documents.create(
            owner_id=None,
            filename="contract-manual.pdf",
            content_type="application/pdf",
            storage_path=".data/uploads/contract-manual.pdf",
            metadata={"lightrag": {"domain_id": "contracttree"}},
            status=DocumentStatus.READY,
        )
        DocumentProcessingRepository(session).save_structure(
            DocumentStructure(
                document_id=manual.id,
                source_file=manual.storage_path,
                pages=[
                    DocumentPage(
                        page_number=1,
                        text="Full page text must stay out of workspace tree",
                        metadata={"text": "Page metadata text must also stay out"},
                    )
                ],
                sections=[
                    DocumentSection(
                        section_id="overview",
                        document_id=manual.id,
                        title="Overview",
                        level=1,
                        page_start=1,
                        page_end=1,
                    )
                ],
                source_chunks=[
                    SourceChunk(
                        chunk_id="contract-chunk",
                        document_id=manual.id,
                        section_id="overview",
                        block_ids=[],
                        text=(
                            "Compact label for navigation with enough harmless words before the "
                            "hidden tail marker appears in the source chunk. "
                            "SECRET_DEPTH_CONTRACT_TAIL_SHOULD_NOT_APPEAR"
                        ),
                        page_start=1,
                        page_end=1,
                    )
                ],
                assets=[
                    DocumentAsset(
                        asset_id="contract-asset",
                        document_id=manual.id,
                        asset_type="figure",
                        storage_path=".data/assets/contract-asset.png",
                        thumbnail_path=".data/assets/contract-asset-thumb.png",
                        mime_type="image/png",
                        content_hash="hash-contract-asset",
                        page_number=1,
                        section_id="overview",
                        caption="Contract figure",
                    )
                ],
            )
        )

    with TestClient(app) as client:
        _seed_users()
        user_headers = _login(client, "user@example.com")
        default_response = client.get(
            "/lightrag/domains/contracttree/workspace-tree",
            headers=user_headers,
        )
        depth_response = client.get(
            "/lightrag/domains/contracttree/workspace-tree?depth=2&include_assets=true",
            headers=user_headers,
        )
        no_assets_response = client.get(
            "/lightrag/domains/contracttree/workspace-tree?include_assets=false",
            headers=user_headers,
        )

    assert default_response.status_code == 200
    default_body = default_response.json()
    default_document = default_body["root"]["children"][0]
    default_section = default_document["children"][0]
    default_page = default_section["children"][0]
    assert default_page["children"][0]["kind"] == "chunk"
    assert default_page["children"][1]["kind"] == "asset"
    assert "SECRET_DEPTH_CONTRACT_TAIL_SHOULD_NOT_APPEAR" not in default_response.text
    assert "Full page text must stay out of workspace tree" not in default_response.text
    assert "Page metadata text must also stay out" not in default_response.text

    assert depth_response.status_code == 200
    depth_document = depth_response.json()["root"]["children"][0]
    assert depth_document["kind"] == "document"
    assert [child["kind"] for child in depth_document["children"]] == ["section"]
    assert depth_document["children"][0]["children"] == []
    assert "contract-chunk" not in depth_response.text
    assert "contract-asset" not in depth_response.text

    assert no_assets_response.status_code == 200
    no_assets_document = no_assets_response.json()["root"]["children"][0]
    no_assets_page = no_assets_document["children"][0]["children"][0]
    assert [child["kind"] for child in no_assets_page["children"]] == ["chunk"]
    assert "contract-asset" not in no_assets_response.text


def test_document_ingest_job_can_be_enqueued_without_running_inline() -> None:
    create_db_and_tables()

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
        job_id = JobService(session, queue=queue, run_inline=False).enqueue_document_ingest(
            document_id=document.id
        )
        job = JobRepository(session).get(job_id)

    assert len(queue.enqueued) == 1
    assert queue.enqueued[0][1] == job_id
    assert job.status == "queued"
    assert job.meta["rq_job_id"] == "rq-job-1"


def test_worker_marks_failed_document_ingest_job_when_document_is_deleted() -> None:
    create_db_and_tables()

    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="missing-document.txt",
            content_type="text/plain",
            storage_path=".data/uploads/missing-document.txt",
            metadata={"lightrag": {"domain_id": "default", "status": "queued"}},
            status=DocumentStatus.INDEXING,
        )
        job = JobRepository(session).create(kind="document_ingest", document_id=document.id)
        DocumentRepository(session).mark_deleted(document)
        job_id = job.id

    with pytest.raises(ValueError, match="Structure-aware ingestion failed"):
        run_document_ingest_job(job_id)

    with SessionLocal() as session:
        refreshed = JobRepository(session).get(job_id)

    assert refreshed.status == "failed"
    assert "Structure-aware ingestion failed" in refreshed.error_message


def test_admin_can_retry_document_ingest_job(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    create_db_and_tables()
    upload_path = tmp_path / "manual.txt"
    upload_path.write_text("Retryable document body.", encoding="utf-8")
    monkeypatch.setattr(RedisIngestLock, "acquire", lambda self: True)
    monkeypatch.setattr(RedisIngestLock, "release", lambda self: None)

    def fake_ingest_source_chunks(
        self: LightRAGRemoteAdapter,
        *,
        domain: str,
        chunks: list[SourceChunk],
    ) -> dict:
        del self
        assert domain == "default"
        assert chunks
        return {"document_id": "remote-doc", "track_id": "track-1", "status": "ready"}

    monkeypatch.setattr(LightRAGRemoteAdapter, "ingest_source_chunks", fake_ingest_source_chunks)

    with SessionLocal() as session:
        document = DocumentRepository(session).create(
            owner_id=None,
            filename="manual.txt",
            content_type="text/plain",
            storage_path=str(upload_path),
            metadata={"lightrag": {"domain_id": "default", "status": "queued"}},
            status=DocumentStatus.INDEXING,
        )
        job = JobRepository(session).create(kind="document_ingest", document_id=document.id)
        job_id = job.id

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(f"/jobs/{job_id}/retry", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "document_ingest"
    assert body["status"] == "succeeded"


def test_admin_retry_rejects_non_document_ingest_job() -> None:
    create_db_and_tables()
    with SessionLocal() as session:
        job = JobRepository(session).create(kind="other_job", document_id=None)
        job_id = job.id

    with TestClient(app) as client:
        _seed_users()
        admin_headers = _login(client, "admin@example.com")
        response = client.post(f"/jobs/{job_id}/retry", headers=admin_headers)

    assert response.status_code == 400
    assert response.json()["detail"] == "Only document_ingest jobs can be retried"

