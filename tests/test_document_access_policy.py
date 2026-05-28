from types import SimpleNamespace

from app.domain.models import DocumentStatus
from app.services.document_access_policy import DocumentAccessPolicy


class _StubDocumentRepository:
    def list_ready(self) -> list[object]:
        return []

    def get(self, document_id: str) -> object | None:
        del document_id
        return None


def _document(*, status: DocumentStatus, domain_id: str | None = None) -> object:
    return SimpleNamespace(
        status=status.value,
        lightrag_domain_id=domain_id,
        meta={},
    )


def test_filter_tree_documents_returns_only_ready_documents() -> None:
    policy = DocumentAccessPolicy(_StubDocumentRepository())
    user = SimpleNamespace()
    documents = [
        _document(status=DocumentStatus.UPLOADED),
        _document(status=DocumentStatus.INDEXING),
        _document(status=DocumentStatus.FAILED),
        _document(status=DocumentStatus.READY),
    ]

    filtered = policy.filter_tree_documents(user, documents)

    assert len(filtered) == 1
    assert filtered[0].status == DocumentStatus.READY.value


def test_filter_tree_documents_excludes_inactive_domain_documents() -> None:
    policy = DocumentAccessPolicy(_StubDocumentRepository())
    policy.lifecycle = SimpleNamespace(is_active=lambda domain_id: domain_id == "active")
    user = SimpleNamespace()
    documents = [
        _document(status=DocumentStatus.READY, domain_id="active"),
        _document(status=DocumentStatus.READY, domain_id="archived"),
    ]

    filtered = policy.filter_tree_documents(user, documents)

    assert len(filtered) == 1
    assert filtered[0].lightrag_domain_id == "active"
