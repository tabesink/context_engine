from pathlib import Path
from uuid import UUID

import httpx
import pytest

from app.core.config import Settings
from app.document_processing.models import SourceChunk
from app.domain.models import RetrievalMode
from app.integrations.lightrag_domains import resolve_lightrag_domain
from app.integrations.lightrag_remote_adapter import (
    LightRAGAuthenticationError,
    LightRAGInvalidResponse,
    LightRAGRemoteAdapter,
    LightRAGServiceUnavailable,
    LightRAGUpstreamError,
)
from app.services.lightrag_domain_registry import (
    LightRAGDomainNotFoundError,
    LightRAGDomainRegistryInvalidError,
)


def test_domain_resolver_requires_registered_domain(tmp_path: Path) -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite:///./.data/test_context_engine.db",
        lightrag_domain_registry=tmp_path / "missing.json",
    )

    with pytest.raises(LightRAGDomainNotFoundError, match="LightRAG domain 'default' does not exist"):
        resolve_lightrag_domain(settings=settings, domain="default")


def test_domain_resolver_uses_registered_runtime_connection(tmp_path: Path) -> None:
    registry_path = tmp_path / "domains.json"
    registry_path.write_text(
        '{"domains":[{"id":"default","host_base_url":"http://127.0.0.1:9623","container_base_url":"http://lightrag.example:9621","api_key":"secret","status":"ready"}]}',
        encoding="utf-8",
    )
    settings = Settings(
        environment="test",
        database_url="sqlite:///./.data/test_context_engine.db",
        lightrag_domain_registry=registry_path,
    )

    domain = resolve_lightrag_domain(settings=settings, domain="default")

    assert domain.name == "default"
    assert domain.base_url == "http://127.0.0.1:9623"
    assert domain.api_key == "secret"


def test_domain_resolver_prefers_container_url_in_socket_mode(tmp_path: Path) -> None:
    registry_path = tmp_path / "domains.json"
    registry_path.write_text(
        (
            '{"domains":[{"id":"default","base_url":"http://127.0.0.1:9623",'
            '"host_base_url":"http://127.0.0.1:9623",'
            '"container_base_url":"http://lightrag_default:9621","status":"ready"}]}'
        ),
        encoding="utf-8",
    )
    settings = Settings(
        environment="test",
        database_url="sqlite:///./.data/test_context_engine.db",
        lightrag_domain_registry=registry_path,
        lightrag_docker_execution_mode="socket",
    )

    domain = resolve_lightrag_domain(settings=settings, domain="default")

    assert domain.base_url == "http://lightrag_default:9621"


def test_domain_resolver_prefers_host_url_in_host_mode(tmp_path: Path) -> None:
    registry_path = tmp_path / "domains.json"
    registry_path.write_text(
        (
            '{"domains":[{"id":"default","base_url":"http://legacy.example",'
            '"host_base_url":"http://127.0.0.1:9623",'
            '"container_base_url":"http://lightrag_default:9621","status":"ready"}]}'
        ),
        encoding="utf-8",
    )
    settings = Settings(
        environment="test",
        database_url="sqlite:///./.data/test_context_engine.db",
        lightrag_domain_registry=registry_path,
        lightrag_docker_execution_mode="host",
    )

    domain = resolve_lightrag_domain(settings=settings, domain="default")

    assert domain.base_url == "http://127.0.0.1:9623"


def test_domain_resolver_rejects_manifest_without_runtime_url(tmp_path: Path) -> None:
    registry_path = tmp_path / "domains.json"
    registry_path.write_text(
        '{"domains":[{"id":"default","status":"ready"}]}',
        encoding="utf-8",
    )
    settings = Settings(
        environment="test",
        database_url="sqlite:///./.data/test_context_engine.db",
        lightrag_domain_registry=registry_path,
    )

    with pytest.raises(LightRAGDomainRegistryInvalidError):
        resolve_lightrag_domain(settings=settings, domain="default")


def test_remote_adapter_normalizes_query_data_chunks_to_evidence() -> None:
    document_id = "22222222-2222-4222-8222-222222222222"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/query/data"
        assert request.headers["x-api-key"] == "token"
        body = request.read().decode()
        assert '"mode":"mix"' in body
        return httpx.Response(
            200,
            json={
                "status": "success",
                "message": "ok",
                "data": {
                    "chunks": [
                        {
                            "content": "Retrieved remote context.",
                            "file_path": "manual.pdf",
                            "chunk_id": "chunk-abc",
                            "reference_id": "1",
                            "document_id": document_id,
                            "page_start": 4,
                            "page_end": 5,
                            "metadata": {"source_chunk_id": "source-chunk-1"},
                        }
                    ],
                    "entities": [],
                    "relationships": [],
                    "references": [{"reference_id": "1", "file_path": "manual.pdf"}],
                },
                "metadata": {"query_mode": "mix"},
            },
        )

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        api_key="token",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    evidence = adapter.retrieve(
        query="remote",
        mode=RetrievalMode.SEMANTIC,
        top_k=3,
        document_ids=None,
    )

    assert len(evidence) == 1
    assert evidence[0].id == "chunk-abc"
    assert evidence[0].document_id == UUID(document_id)
    assert evidence[0].source_engine == "lightrag"
    assert evidence[0].text == "Retrieved remote context."
    assert evidence[0].page_ref.page_start == 4
    assert evidence[0].metadata["source_path"] == "manual.pdf"
    assert evidence[0].metadata["source_chunk_id"] == "source-chunk-1"


def test_remote_adapter_preserves_ingested_chunk_metadata() -> None:
    document_id = "22222222-2222-4222-8222-222222222222"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/query/data"
        return httpx.Response(
            200,
            json={
                "data": {
                    "chunks": [
                        {
                            "content": "Retrieved remote context.",
                            "chunk_id": "remote-result-1",
                            "document_id": document_id,
                            "metadata": {"chunk_id": "source-chunk-1", "asset_ids": ["asset-1"]},
                        }
                    ],
                    "references": [],
                },
            },
        )

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    evidence = adapter.retrieve(
        query="remote",
        mode=RetrievalMode.SEMANTIC,
        top_k=3,
        document_ids=None,
    )

    assert evidence[0].metadata["chunk_id"] == "source-chunk-1"
    assert evidence[0].metadata["asset_ids"] == ["asset-1"]


def test_remote_adapter_uses_metadata_when_chunk_fields_are_partial() -> None:
    document_id = "22222222-2222-4222-8222-222222222222"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/query/data"
        return httpx.Response(
            200,
            json={
                "data": {
                    "chunks": [
                        {
                            "content": "Retrieved remote context.",
                            "chunk_id": "remote-result-1",
                            "metadata": {
                                "document_id": document_id,
                                "chunk_id": "source-chunk-1",
                                "page_start": 3,
                                "page_end": 4,
                            },
                        }
                    ],
                    "references": [],
                },
            },
        )

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    evidence = adapter.retrieve(
        query="remote",
        mode=RetrievalMode.SEMANTIC,
        top_k=3,
        document_ids=None,
    )

    assert evidence[0].document_id == UUID(document_id)
    assert evidence[0].page_ref.page_start == 3
    assert evidence[0].metadata["chunk_id"] == "source-chunk-1"


def test_remote_adapter_includes_domain_when_provided() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/query/data"
        body = request.read().decode()
        assert '"domain":"manuals"' in body
        return httpx.Response(200, json={"data": {"chunks": [], "references": []}})

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    evidence = adapter.retrieve(
        query="remote",
        mode=RetrievalMode.SEMANTIC,
        top_k=3,
        document_ids=None,
        domain="manuals",
    )

    assert evidence == []


def test_remote_adapter_normalizes_upload_response(tmp_path: Path) -> None:
    upload = tmp_path / "manual.txt"
    upload.write_text("manual body")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/documents/upload"
        assert request.headers["x-api-key"] == "token"
        return httpx.Response(
            200,
            json={"status": "success", "track_id": "track-1", "message": "accepted"},
        )

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        api_key="token",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    response = adapter.upload_document(
        file_path=upload,
        filename="manual.txt",
        content_type="text/plain",
    )

    assert response == {
        "document_id": None,
        "track_id": "track-1",
        "status": "indexing",
        "message": "accepted",
    }


def test_remote_adapter_ingests_source_chunks_with_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/documents/ingest_chunks"
        payload = request.read().decode()
        assert '"domain":"manuals"' in payload
        assert '"chunk_id":"chunk-1"' in payload
        assert '"block_ids":["block-1"]' in payload
        assert '"asset_ids":["asset-1"]' in payload
        assert '"semantic_owner":"lightrag"' in payload
        assert '"section_title":"Safety"' in payload
        assert '"section_path":["Manual","Safety"]' in payload
        return httpx.Response(200, json={"status": "success", "track_id": "track-chunks"})

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    response = adapter.ingest_source_chunks(
        domain="manuals",
        chunks=[
            SourceChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                section_id="sec-1",
                block_ids=["block-1"],
                text="See figure.",
                page_start=1,
                page_end=1,
                asset_ids=["asset-1"],
                metadata={
                    "semantic_owner": "lightrag",
                    "section_title": "Safety",
                    "section_path": ["Manual", "Safety"],
                },
            )
        ],
    )

    assert response["status"] == "indexing"
    assert response["track_id"] == "track-chunks"


def test_remote_adapter_falls_back_to_texts_when_ingest_chunks_not_supported() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/documents/ingest_chunks":
            return httpx.Response(404, json={"detail": "Not Found"})

        assert request.url.path == "/documents/texts"
        payload = request.read().decode()
        assert '"texts":["See figure."]' in payload
        assert '"file_sources":["manual.pdf#chunk=chunk-1"]' in payload
        return httpx.Response(200, json={"status": "success", "track_id": "track-texts"})

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    response = adapter.ingest_source_chunks(
        domain="manuals",
        chunks=[
            SourceChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                section_id="sec-1",
                block_ids=["block-1"],
                text="See figure.",
                page_start=1,
                page_end=1,
                asset_ids=["asset-1"],
                metadata={"source_path": "manual.pdf"},
            )
        ],
    )

    assert paths == ["/documents/ingest_chunks", "/documents/texts"]
    assert response["status"] == "indexing"
    assert response["track_id"] == "track-texts"


def test_remote_adapter_normalizes_track_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/documents/track_status/track-1"
        return httpx.Response(
            200,
            json={
                "track_id": "track-1",
                "documents": [
                    {
                        "id": "external-doc",
                        "status": "PROCESSED",
                        "error_msg": None,
                        "metadata": {"source": "manual.pdf"},
                    }
                ],
            },
        )

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    status = adapter.document_status("track-1")

    assert status["track_id"] == "track-1"
    assert status["document_id"] == "external-doc"
    assert status["status"] == "ready"
    assert status["error"] is None


def test_remote_adapter_treats_missing_track_status_as_indexing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/documents/track_status/track-1"
        return httpx.Response(200, json={"track_id": "track-1", "documents": []})

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    status = adapter.document_status("track-1")

    assert status["track_id"] == "track-1"
    assert status["document_id"] is None
    assert status["status"] == "indexing"


def test_remote_adapter_rejects_unknown_track_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/documents/track_status/track-1"
        return httpx.Response(
            200,
            json={
                "track_id": "track-1",
                "documents": [{"id": "external-doc", "status": "mystery", "error_msg": None}],
            },
        )

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    with pytest.raises(LightRAGInvalidResponse, match="Unknown LightRAG status"):
        adapter.document_status("track-1")


def test_remote_adapter_rejects_unknown_upload_status(tmp_path: Path) -> None:
    upload = tmp_path / "manual.txt"
    upload.write_text("manual body")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/documents/upload"
        return httpx.Response(200, json={"status": "mystery", "track_id": "track-1"})

    adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(transport=httpx.MockTransport(handler), base_url="http://lightrag.local"),
    )

    with pytest.raises(LightRAGInvalidResponse, match="Unknown LightRAG upload status"):
        adapter.upload_document(
            file_path=upload,
            filename="manual.txt",
            content_type="text/plain",
        )


def test_remote_adapter_maps_timeout_and_invalid_json() -> None:
    timeout_adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: (_ for _ in ()).throw(httpx.TimeoutException("slow"))),
            base_url="http://lightrag.local",
        ),
    )

    with pytest.raises(LightRAGServiceUnavailable):
        timeout_adapter.get_json("/graphs")

    invalid_adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(200, text="not-json")),
            base_url="http://lightrag.local",
        ),
    )

    with pytest.raises(LightRAGInvalidResponse):
        invalid_adapter.get_json("/graphs")


def test_remote_adapter_maps_auth_and_upstream_failures() -> None:
    auth_adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(401, json={"detail": "no"})),
            base_url="http://lightrag.local",
        ),
    )

    with pytest.raises(LightRAGAuthenticationError):
        auth_adapter.get_json("/graphs")

    upstream_adapter = LightRAGRemoteAdapter(
        base_url="http://lightrag.local",
        client=httpx.Client(
            transport=httpx.MockTransport(lambda request: httpx.Response(500, json={"detail": "boom"})),
            base_url="http://lightrag.local",
        ),
    )

    with pytest.raises(LightRAGUpstreamError):
        upstream_adapter.get_json("/graphs")
