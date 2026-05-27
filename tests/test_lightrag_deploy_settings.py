from pathlib import Path

import pytest

from app.core.config import Settings
from app.lightrag_deploy.paths import DomainPathResolver, validate_domain_id
from app.lightrag_deploy.settings import LightRAGDeploySettings


def test_env_example_declares_lightrag_deployment_settings() -> None:
    env_examples = "\n".join(
        [
            Path(".env.example").read_text(encoding="utf-8"),
            Path(".env.lightrag-deploy.example").read_text(encoding="utf-8"),
            Path(".env.lightrag-provider.example").read_text(encoding="utf-8"),
        ]
    )

    for key in [
        "LIGHTRAG_DEPLOY_ENABLED",
        "LIGHTRAG_DEPLOY_ROOT",
        "LIGHTRAG_DOMAINS_ROOT",
        "LIGHTRAG_DOMAIN_REGISTRY",
        "LIGHTRAG_COMPOSE_FILE",
        "LIGHTRAG_DELETED_ROOT",
        "LIGHTRAG_DEFAULT_PORT_START",
        "LIGHTRAG_DEFAULT_CONTAINER_PORT",
        "LIGHTRAG_DOCKER_NETWORK",
        "LIGHTRAG_DOMAIN_ENV_FILENAME",
        "LIGHTRAG_DOCKERFILE",
        "LIGHTRAG_BUILD_CONTEXT",
        "LIGHTRAG_DOCKER_EXECUTION_MODE",
        "LIGHTRAG_DOCKER_COMPOSE_BIN",
        "LIGHTRAG_DOCKER_TIMEOUT_SECONDS",
        "LIGHTRAG_STORAGE_BACKEND",
        "LIGHTRAG_POSTGRES_HOST",
        "LIGHTRAG_POSTGRES_PORT",
        "LIGHTRAG_POSTGRES_DATABASE_PREFIX",
        "LIGHTRAG_POSTGRES_USER_PREFIX",
        "LIGHTRAG_POSTGRES_PASSWORD",
        "LIGHTRAG_POSTGRES_PROVISIONING_MODE",
        "LIGHTRAG_POSTGRES_ADMIN_DATABASE",
        "LIGHTRAG_POSTGRES_VECTOR_EXTENSION",
        "LIGHTRAG_POSTGRES_AGE_EXTENSION",
        "LIGHTRAG_POSTGRES_VECTOR_INDEX_TYPE",
        "LIGHTRAG_TOKENIZER_OFFLINE",
        "LIGHTRAG_TIKTOKEN_CACHE_DIR",
        "LIGHTRAG_LLM_BINDING",
        "LIGHTRAG_LLM_BINDING_HOST",
        "LIGHTRAG_LLM_BINDING_API_KEY",
        "LIGHTRAG_LLM_MODEL",
        "LIGHTRAG_KEYWORD_LLM_MODEL",
        "LIGHTRAG_QUERY_LLM_MODEL",
        "LIGHTRAG_VLM_LLM_MODEL",
        "LIGHTRAG_EMBEDDING_BINDING",
        "LIGHTRAG_EMBEDDING_BINDING_HOST",
        "LIGHTRAG_EMBEDDING_BINDING_API_KEY",
        "LIGHTRAG_EMBEDDING_MODEL",
        "LIGHTRAG_EMBEDDING_DIM",
        "LIGHTRAG_EMBEDDING_TOKEN_LIMIT",
        "LIGHTRAG_EMBEDDING_SEND_DIM",
        "LIGHTRAG_EMBEDDING_USE_BASE64",
        "LIGHTRAG_OPENAI_LLM_MAX_TOKENS",
        "LIGHTRAG_OPENAI_LLM_MAX_COMPLETION_TOKENS",
        "LIGHTRAG_OPENAI_LLM_TEMPERATURE",
        "LIGHTRAG_OPENAI_LLM_EXTRA_BODY",
    ]:
        assert f"{key}=" in env_examples


def test_settings_parse_lightrag_deployment_fields(tmp_path: Path) -> None:
    settings = Settings(
        environment="test",
        database_url="postgresql+psycopg://app_user:app_pw@localhost:5438/test_context_engine",
        lightrag_deploy_enabled=True,
        lightrag_domain_registry=tmp_path / "lightrag" / "domains.json",
        lightrag_deploy_root=tmp_path / "lightrag",
        lightrag_domains_root=tmp_path / "lightrag" / "domains",
        lightrag_compose_file=tmp_path / "lightrag" / "compose.yml",
        lightrag_deleted_root=tmp_path / "lightrag" / "deleted",
        lightrag_default_port_start=9700,
        lightrag_default_container_port=9621,
        lightrag_docker_network="ce_lightrag",
        lightrag_domain_env_filename="domain.env",
        lightrag_dockerfile=Path("docker/lightrag.Dockerfile"),
        lightrag_build_context=Path("."),
        lightrag_docker_execution_mode="socket",
        lightrag_docker_compose_bin="docker compose",
        lightrag_docker_timeout_seconds=30,
        lightrag_storage_backend="postgres",
        lightrag_postgres_host="postgres",
        lightrag_postgres_port=5432,
        lightrag_postgres_database_prefix="lr",
        lightrag_postgres_user_prefix="lr_user",
        lightrag_postgres_password="secret",
        lightrag_postgres_provisioning_mode="per_domain",
        lightrag_postgres_admin_database="ctx_admin",
        lightrag_postgres_vector_extension="vector",
        lightrag_postgres_age_extension="age",
        lightrag_postgres_vector_index_type="IVFFlat",
        lightrag_tokenizer_offline=True,
        lightrag_tiktoken_cache_dir="/app/.cache/tiktoken",
        lightrag_llm_binding="openai",
        lightrag_llm_binding_host="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1",
        lightrag_llm_binding_api_key="bedrock-key",
        lightrag_llm_model="openai.gpt-oss-20b-1:0",
        lightrag_keyword_llm_model="keyword-model",
        lightrag_query_llm_model="query-model",
        lightrag_vlm_llm_model="vlm-model",
        lightrag_embedding_binding="openai",
        lightrag_embedding_binding_host="https://api.openai.com/v1",
        lightrag_embedding_binding_api_key="openai-key",
        lightrag_embedding_model="text-embedding-3-large",
        lightrag_embedding_dim=3072,
        lightrag_embedding_token_limit=8192,
        lightrag_embedding_send_dim=False,
        lightrag_embedding_use_base64=True,
        lightrag_openai_llm_max_tokens=9000,
        lightrag_openai_llm_max_completion_tokens=1200,
        lightrag_openai_llm_temperature=0.2,
        lightrag_openai_llm_extra_body='{"top_p":0.95}',
    )

    deploy = LightRAGDeploySettings.from_app_settings(settings)

    assert deploy.enabled is True
    assert deploy.domains_root == tmp_path / "lightrag" / "domains"
    assert deploy.manifest_path == tmp_path / "lightrag" / "domains.json"
    assert deploy.default_port_start == 9700
    assert deploy.dockerfile == Path("docker/lightrag.Dockerfile")
    assert deploy.build_context == Path(".")
    assert deploy.docker_execution_mode == "socket"
    assert deploy.storage_backend == "postgres"
    assert deploy.postgres_host == "postgres"
    assert deploy.postgres_database_prefix == "lr"
    assert deploy.postgres_user_prefix == "lr_user"
    assert deploy.postgres_provisioning_mode == "per_domain"
    assert deploy.postgres_admin_database == "ctx_admin"
    assert deploy.postgres_vector_extension == "vector"
    assert deploy.postgres_age_extension == "age"
    assert deploy.postgres_vector_index_type == "IVFFlat"
    assert deploy.tokenizer_offline is True
    assert deploy.tiktoken_cache_dir == "/app/.cache/tiktoken"
    assert deploy.database_url_for_admin == "postgresql+psycopg://app_user:app_pw@localhost:5438/test_context_engine"
    assert deploy.runtime_postgres_database == "test_context_engine"
    assert deploy.runtime_postgres_user == "app_user"
    assert deploy.runtime_postgres_password == "app_pw"
    assert deploy.llm_binding == "openai"
    assert deploy.llm_binding_host == "https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1"
    assert deploy.llm_binding_api_key == "bedrock-key"
    assert deploy.llm_model == "openai.gpt-oss-20b-1:0"
    assert deploy.keyword_llm_model == "keyword-model"
    assert deploy.query_llm_model == "query-model"
    assert deploy.vlm_llm_model == "vlm-model"
    assert deploy.embedding_binding == "openai"
    assert deploy.embedding_binding_host == "https://api.openai.com/v1"
    assert deploy.embedding_binding_api_key == "openai-key"
    assert deploy.embedding_model == "text-embedding-3-large"
    assert deploy.embedding_dim == 3072
    assert deploy.embedding_token_limit == 8192
    assert deploy.embedding_send_dim is False
    assert deploy.embedding_use_base64 is True
    assert deploy.openai_llm_max_tokens == 9000
    assert deploy.openai_llm_max_completion_tokens == 1200
    assert deploy.openai_llm_temperature == 0.2
    assert deploy.openai_llm_extra_body == '{"top_p":0.95}'


def test_settings_default_to_internal_lightrag_build_paths() -> None:
    settings = Settings(
        environment="test",
        database_url="postgresql+psycopg://app_user:app_pw@localhost:5438/test_context_engine",
    )

    deploy = LightRAGDeploySettings.from_app_settings(settings)

    assert deploy.dockerfile == Path("docker/lightrag.Dockerfile")
    assert deploy.build_context == Path(".")


def test_domain_path_resolver_creates_expected_domain_tree(tmp_path: Path) -> None:
    deploy = LightRAGDeploySettings(
        enabled=True,
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag" / "domains",
        manifest_path=tmp_path / "lightrag" / "domains.json",
        compose_file=tmp_path / "lightrag" / "docker-compose.yml",
        deleted_root=tmp_path / "lightrag" / "deleted",
    )
    paths = DomainPathResolver(deploy).ensure_domain_paths("fatigue")

    assert paths.root == tmp_path / "lightrag" / "domains" / "fatigue"
    assert paths.env_file == paths.root / "domain.env"
    assert paths.inputs.is_dir()
    assert paths.rag_storage.is_dir()
    assert paths.artifacts.is_dir()
    assert paths.logs.is_dir()


@pytest.mark.parametrize("domain_id", ["fatigue", "abaqus_2026", "manual-domain"])
def test_validate_domain_id_accepts_safe_ids(domain_id: str) -> None:
    assert validate_domain_id(domain_id) == domain_id


@pytest.mark.parametrize("domain_id", ["Abaqus", "../escape", "x", "-bad", "bad space", "bad.domain"])
def test_validate_domain_id_rejects_unsafe_ids(domain_id: str) -> None:
    with pytest.raises(ValueError):
        validate_domain_id(domain_id)
