from typing import Any

from cli.services.admin_documents import AdminDocumentService
from cli.services.auth import AuthService
from cli.services.documents import DocumentService
from cli.services.health import HealthService
from cli.services.jobs import JobService
from cli.services.lightrag import LightRagService
from cli.services.lightrag_domains import LightRAGDomainService
from cli.services.observability import ObservabilityService
from cli.services.retrieval import RetrievalService


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Any]] = []

    def get(self, path: str) -> Any:
        self.calls.append(("GET", path, None))
        return {"status": "ok"}

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append(("POST", path, payload))
        return {"status": "ok", "payload": payload}

    def delete(self, path: str) -> Any:
        self.calls.append(("DELETE", path, None))
        return {"status": "deleted"}

    def post_file(
        self,
        path: str,
        field_name: str,
        filename: str,
        content: bytes,
        fields: dict[str, str] | None = None,
    ) -> Any:
        self.calls.append(
            (
                "POST_FILE",
                path,
                {"field_name": field_name, "filename": filename, "size": len(content), "fields": fields},
            )
        )
        return {"document": {"id": "doc-1"}, "job_id": "job-1"}


def test_auth_service_routes() -> None:
    client = FakeClient()
    service = AuthService(client)  # type: ignore[arg-type]

    service.login("admin", "secret")
    service.current_user()

    assert ("POST", "/auth/login", {"username": "admin", "password": "secret"}) in client.calls
    assert ("GET", "/auth/me", None) in client.calls


def test_document_service_routes() -> None:
    client = FakeClient()
    service = DocumentService(client)  # type: ignore[arg-type]

    service.list_documents()
    service.get_document("doc-1")
    service.get_structure("doc-1", include_blocks=True, include_assets=True)
    service.get_ingestion_status("doc-1")
    service.get_structure_quality("doc-1")
    service.get_section("doc-1", "sec-1")
    service.get_chunk("doc-1", "chunk-1")
    service.list_chunks("doc-1")
    service.list_assets("doc-1")
    service.get_page("doc-1", 3)

    assert ("GET", "/documents", None) in client.calls
    assert ("GET", "/documents/doc-1", None) in client.calls
    assert (
        "GET",
        "/documents/doc-1/structure?include_blocks=true&include_assets=true",
        None,
    ) in client.calls
    assert ("GET", "/documents/doc-1/ingestion-status", None) in client.calls
    assert ("GET", "/documents/doc-1/structure-quality", None) in client.calls
    assert ("GET", "/documents/doc-1/sections/sec-1", None) in client.calls
    assert ("GET", "/documents/doc-1/chunks/chunk-1", None) in client.calls
    assert ("GET", "/documents/doc-1/chunks", None) in client.calls
    assert ("GET", "/documents/doc-1/assets", None) in client.calls
    assert ("GET", "/documents/doc-1/pages/3", None) in client.calls


def test_admin_document_service_routes() -> None:
    client = FakeClient()
    service = AdminDocumentService(client)  # type: ignore[arg-type]

    service.list_documents()
    service.upload_document("manual.pdf", b"pdf-bytes")
    service.reingest("doc-1")
    service.refresh_status("doc-1")
    service.delete_document("doc-1")

    assert ("GET", "/admin/documents", None) in client.calls
    assert (
        "POST_FILE",
        "/admin/documents/upload",
        {"field_name": "file", "filename": "manual.pdf", "size": 9, "fields": None},
    ) in client.calls
    assert ("POST", "/admin/documents/doc-1/reingest", None) in client.calls
    assert ("POST", "/admin/documents/doc-1/refresh-status", None) in client.calls
    assert ("DELETE", "/admin/documents/doc-1", None) in client.calls


def test_retrieval_service_routes() -> None:
    client = FakeClient()
    service = RetrievalService(client)  # type: ignore[arg-type]

    service.retrieve(
        query="reset procedure",
        mode="hybrid",
        top_k=5,
        include_debug=True,
        lightrag_domain_id="fatigue",
    )

    retrieve_call = next(call for call in client.calls if call[1] == "/retrieve")
    assert retrieve_call[0] == "POST"
    assert retrieve_call[2]["query"] == "reset procedure"
    assert retrieve_call[2]["mode"] == "hybrid"
    assert retrieve_call[2]["top_k"] == 5
    assert retrieve_call[2]["include_debug"] is True
    assert retrieve_call[2]["lightrag_domain_id"] == "fatigue"


def test_job_service_routes() -> None:
    client = FakeClient()
    service = JobService(client)  # type: ignore[arg-type]

    service.list_jobs()
    service.get_job("job-1")
    service.retry_job("job-1")

    assert ("GET", "/jobs", None) in client.calls
    assert ("GET", "/jobs/job-1", None) in client.calls
    assert ("POST", "/jobs/job-1/retry", None) in client.calls


def test_lightrag_service_routes() -> None:
    client = FakeClient()
    service = LightRagService(client)  # type: ignore[arg-type]

    service.list_labels()
    service.popular_labels(limit=7)
    service.search_labels(query="reset", limit=5)
    service.get_graph(label="manual", max_depth=2, max_nodes=100)

    assert ("GET", "/graph/label/list", None) in client.calls
    assert ("GET", "/graph/label/popular?limit=7", None) in client.calls
    assert ("GET", "/graph/label/search?q=reset&limit=5", None) in client.calls
    assert ("GET", "/graphs?label=manual&max_depth=2&max_nodes=100", None) in client.calls


def test_lightrag_domain_service_routes() -> None:
    client = FakeClient()
    service = LightRAGDomainService(client)  # type: ignore[arg-type]

    service.list_user_domains()
    service.list_admin_domains()
    service.create_domain({"domain_id": "fatigue"})
    service.show_domain("fatigue")
    service.up_domain("fatigue")
    service.down_domain("fatigue")
    service.recreate_domain("fatigue")
    service.regenerate_domain("fatigue")
    service.remove_domain("fatigue", permanent=True)

    assert ("GET", "/lightrag/domains", None) in client.calls
    assert ("GET", "/admin/lightrag/domains", None) in client.calls
    assert ("POST", "/admin/lightrag/domains", {"domain_id": "fatigue"}) in client.calls
    assert ("GET", "/admin/lightrag/domains/fatigue", None) in client.calls
    assert ("POST", "/admin/lightrag/domains/fatigue/up", None) in client.calls
    assert ("POST", "/admin/lightrag/domains/fatigue/down", None) in client.calls
    assert ("POST", "/admin/lightrag/domains/fatigue/recreate", None) in client.calls
    assert ("POST", "/admin/lightrag/domains/fatigue/regenerate", None) in client.calls
    assert ("DELETE", "/admin/lightrag/domains/fatigue?permanent=true", None) in client.calls


def test_observability_service_routes() -> None:
    client = FakeClient()
    service = ObservabilityService(client)  # type: ignore[arg-type]

    service.query_logs()
    service.audit_logs()

    assert ("GET", "/admin/query-logs", None) in client.calls
    assert ("GET", "/admin/audit-logs", None) in client.calls


def test_health_service_routes() -> None:
    client = FakeClient()
    service = HealthService(client)  # type: ignore[arg-type]

    service.health()
    service.readiness()

    assert ("GET", "/health", None) in client.calls
    assert ("GET", "/health/readiness", None) in client.calls
