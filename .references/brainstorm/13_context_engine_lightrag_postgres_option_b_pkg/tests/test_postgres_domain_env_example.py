"""Example tests to adapt into tests/lightrag_deploy/test_postgres_domain_env.py."""

from datetime import UTC, datetime

from app.lightrag_deploy.compose import render_domain_env
from app.lightrag_deploy.models import LightRAGDomain
from app.lightrag_deploy.settings import LightRAGDeploySettings


def test_postgres_env_uses_domain_credentials_in_per_domain_mode():
    settings = LightRAGDeploySettings(
        storage_backend="postgres",
        postgres_provisioning_mode="per_domain",
        postgres_host="postgres",
        postgres_port=5432,
        postgres_password="secret",
        postgres_vector_index_type="HNSW",
    )
    now = datetime.now(UTC)
    domain = LightRAGDomain(
        id="fatigue",
        display_name="Fatigue",
        workspace="fatigue",
        postgres_database="lightrag_fatigue",
        postgres_user="lightrag_fatigue",
        host_port=9622,
        base_url="http://lightrag_fatigue:9621",
        host_base_url="http://127.0.0.1:9622",
        container_base_url="http://lightrag_fatigue:9621",
        container_name="context_engine_lightrag_fatigue",
        service_name="lightrag_fatigue",
        paths={
            "root": ".data/lightrag/domains/fatigue",
            "env_file": ".data/lightrag/domains/fatigue/domain.env",
            "inputs": ".data/lightrag/domains/fatigue/inputs",
            "rag_storage": ".data/lightrag/domains/fatigue/rag_storage",
            "artifacts": ".data/lightrag/domains/fatigue/artifacts",
            "logs": ".data/lightrag/domains/fatigue/logs",
        },
        created_at=now,
        updated_at=now,
    )

    rendered = render_domain_env(domain, settings)

    assert "LIGHTRAG_KV_STORAGE=PGKVStorage" in rendered
    assert "POSTGRES_DATABASE=lightrag_fatigue" in rendered
    assert "POSTGRES_USER=lightrag_fatigue" in rendered
    assert "POSTGRES_PASSWORD=secret" in rendered
    assert "POSTGRES_USER=lightrag\n" not in rendered
    assert "POSTGRES_USER=context_engine" not in rendered
