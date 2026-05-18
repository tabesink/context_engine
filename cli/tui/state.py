"""Runtime state shared by TUI screens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from cli.credentials import CredentialStore

ClientFactory = Callable[[str, str | None], Any]


@dataclass
class TuiState:
    api_base_url: str
    credential_store: CredentialStore
    client_factory: ClientFactory
    client: Any | None = None
    user_email: str | None = None
    user_role: str | None = None
    last_error: str | None = None

    def reset_anonymous_client(self) -> None:
        self.client = self.client_factory(self.api_base_url, None)

    def get_client(self) -> Any:
        if self.client is None:
            self.reset_anonymous_client()
        return self.client

    def auth_service(self):  # noqa: ANN201
        from cli.services.auth import AuthService

        return AuthService(self.get_client())

    def document_service(self):  # noqa: ANN201
        from cli.services.documents import DocumentService

        return DocumentService(self.get_client())

    def admin_document_service(self):  # noqa: ANN201
        from cli.services.admin_documents import AdminDocumentService

        return AdminDocumentService(self.get_client())

    def retrieval_service(self):  # noqa: ANN201
        from cli.services.retrieval import RetrievalService

        return RetrievalService(self.get_client())

    def job_service(self):  # noqa: ANN201
        from cli.services.jobs import JobService

        return JobService(self.get_client())

    def lightrag_service(self):  # noqa: ANN201
        from cli.services.lightrag import LightRagService

        return LightRagService(self.get_client())

    def lightrag_domain_service(self):  # noqa: ANN201
        from cli.services.lightrag_domains import LightRAGDomainService

        return LightRAGDomainService(self.get_client())

    def observability_service(self):  # noqa: ANN201
        from cli.services.observability import ObservabilityService

        return ObservabilityService(self.get_client())

    def health_service(self):  # noqa: ANN201
        from cli.services.health import HealthService

        return HealthService(self.get_client())
