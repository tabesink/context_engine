from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from app.lightrag_deploy.compose import render_domain_env
from app.lightrag_deploy.models import DomainEmbeddingSnapshot, LightRAGDomain, LightRAGDomainCreateRequest
from app.lightrag_deploy.service import LightRAGDomainService
from app.lightrag_deploy.settings import LightRAGDeploySettings


def _settings(tmp_path: Path) -> LightRAGDeploySettings:
    return LightRAGDeploySettings(
        enabled=True,
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag" / "domains",
        manifest_path=tmp_path / "lightrag" / "domains.json",
        compose_file=tmp_path / "lightrag" / "docker-compose.lightrag-domains.yml",
        deleted_root=tmp_path / "lightrag" / "deleted",
        embedding_binding="openai",
        embedding_binding_host="https://api.openai.com/v1",
        embedding_model="text-embedding-3-small",
        embedding_dim=1536,
    )


class StaticResolver:
    def __init__(self, profile_id: str, model: str, dims: int) -> None:
        self.profile_id = profile_id
        self.model = model
        self.dims = dims

    def resolve_embedding_profile(self, embedding_profile_id: str | None = None):
        chosen = embedding_profile_id or self.profile_id
        model = self.model if chosen == self.profile_id else "text-embedding-3-large"
        dims = self.dims if chosen == self.profile_id else 3072

        class Profile:
            pass

        profile = Profile()
        profile.id = chosen
        profile.kind = "embedding"
        profile.provider = "openai"
        profile.binding = "openai"
        profile.base_url = "https://api.openai.com/v1"
        profile.api_key_env_var = "OPENAI_API_KEY"
        profile.model = model
        profile.dimensions = dims
        profile.token_limit = 8192
        profile.send_dimensions = False
        profile.use_base64 = True
        profile.is_enabled = True
        return profile


def test_domain_env_uses_snapshot_embedding_values_over_global_defaults(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    domain = LightRAGDomain(
        id="fatigue",
        display_name="Fatigue",
        workspace="fatigue",
        postgres_database="lightrag_fatigue",
        postgres_user="lightrag_fatigue",
        host="127.0.0.1",
        host_port=9621,
        container_port=9621,
        base_url="http://127.0.0.1:9621",
        host_base_url="http://127.0.0.1:9621",
        container_base_url="http://lightrag_fatigue:9621",
        container_name="context_engine_lightrag_fatigue",
        service_name="lightrag_fatigue",
        paths={},
        embedding=DomainEmbeddingSnapshot(
            profile_id="openai-text-embedding-3-large",
            provider="openai",
            binding="openai",
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-large",
            dimensions=3072,
            token_limit=8192,
            send_dimensions=False,
            use_base64=True,
            fingerprint="openai:text-embedding-3-large:3072",
        ),
        created_at=datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
        updated_at=datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )
    env_text = render_domain_env(domain, replace(settings, embedding_model="text-embedding-3-small", embedding_dim=1536))
    assert "EMBEDDING_MODEL=text-embedding-3-large" in env_text
    assert "EMBEDDING_DIM=3072" in env_text


def test_create_domain_uses_resolved_embedding_profile(tmp_path: Path) -> None:
    resolver = StaticResolver("openai-text-embedding-3-small", "text-embedding-3-small", 1536)
    service = LightRAGDomainService(
        settings=_settings(tmp_path),
        profile_resolver=resolver,
        now=lambda: datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )
    domain = service.create_domain(
        LightRAGDomainCreateRequest(
            domain_id="fatigue",
            embedding_profile_id="openai-text-embedding-3-large",
        )
    )
    assert domain.embedding is not None
    assert domain.embedding.profile_id == "openai-text-embedding-3-large"
    assert domain.embedding.dimensions == 3072


def test_domain_env_can_use_stored_provider_secret(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    domain = LightRAGDomain(
        id="fatigue",
        display_name="Fatigue",
        workspace="fatigue",
        postgres_database="lightrag_fatigue",
        postgres_user="lightrag_fatigue",
        host="127.0.0.1",
        host_port=9621,
        container_port=9621,
        base_url="http://127.0.0.1:9621",
        host_base_url="http://127.0.0.1:9621",
        container_base_url="http://lightrag_fatigue:9621",
        container_name="context_engine_lightrag_fatigue",
        service_name="lightrag_fatigue",
        paths={},
        embedding=DomainEmbeddingSnapshot(
            profile_id="openai-text-embedding-3-large",
            provider="openai",
            binding="openai",
            base_url="https://api.openai.com/v1",
            api_key_env_var="OPENAI_API_KEY",
            model="text-embedding-3-large",
            dimensions=3072,
            token_limit=8192,
            send_dimensions=False,
            use_base64=True,
            fingerprint="openai:text-embedding-3-large:3072",
        ),
        created_at=datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
        updated_at=datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )
    env_text = render_domain_env(domain, settings, {"OPENAI_API_KEY": "stored-openai-key"})

    assert "EMBEDDING_BINDING_API_KEY=stored-openai-key" in env_text

