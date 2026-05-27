from app.lightrag_deploy.compose import render_domain_env
from app.lightrag_deploy.models import LightRAGDomain, DomainRetrievalDefaults
from app.lightrag_deploy.settings import LightRAGDeploySettings
from datetime import datetime, UTC


def _domain():
    return LightRAGDomain(
        id="fatigue",
        display_name="fatigue",
        workspace="fatigue",
        postgres_database="lightrag_fatigue",
        postgres_user="lightrag_fatigue",
        host_port=9622,
        container_port=9621,
        base_url="http://lightrag_fatigue:9621",
        host_base_url="http://127.0.0.1:9622",
        container_base_url="http://lightrag_fatigue:9621",
        container_name="context_engine_lightrag_fatigue",
        service_name="lightrag_fatigue",
        paths={},
        retrieval_defaults=DomainRetrievalDefaults(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_per_domain_env_uses_lightrag_domain_credentials():
    settings = LightRAGDeploySettings(
        storage_backend="postgres",
        postgres_provisioning_mode="per_domain",
        postgres_password="lightrag",
        runtime_postgres_database="context_engine",
        runtime_postgres_user="context_engine",
        runtime_postgres_password="context_engine",
    )
    env = render_domain_env(_domain(), settings)
    assert "POSTGRES_DATABASE=lightrag_fatigue" in env
    assert "POSTGRES_USER=lightrag_fatigue" in env
    assert "POSTGRES_USER=context_engine" not in env
    assert "TIKTOKEN_CACHE_DIR=/app/.cache/tiktoken" in env


def test_compat_env_uses_legacy_lightrag_credentials():
    settings = LightRAGDeploySettings(
        storage_backend="postgres",
        postgres_provisioning_mode="compat",
        postgres_compat_database="lightrag",
        postgres_compat_user="lightrag",
        postgres_compat_password="lightrag",
    )
    env = render_domain_env(_domain(), settings)
    assert "POSTGRES_DATABASE=lightrag" in env
    assert "POSTGRES_USER=lightrag" in env
