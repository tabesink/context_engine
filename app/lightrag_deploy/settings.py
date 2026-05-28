from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.core.config import Settings


@dataclass(frozen=True)
class LightRAGDeploySettings:
    deploy_root: Path = Path(".data/lightrag")
    domains_root: Path = Path(".data/lightrag/domains")
    manifest_path: Path = Path(".data/lightrag/domains.json")
    compose_file: Path = Path(".data/lightrag/docker-compose.lightrag-domains.yml")
    deleted_root: Path = Path(".data/lightrag/deleted")
    default_port_start: int = 9622
    default_container_port: int = 9621
    host: str = "127.0.0.1"
    docker_network: str = "context_engine_lightrag"
    domain_env_filename: str = "domain.env"
    dockerfile: Path = Path("docker/lightrag.Dockerfile")
    build_context: Path = Path(".")
    storage_backend: str = "postgres"
    postgres_url: str | None = None
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_database_prefix: str = "lightrag"
    postgres_user_prefix: str = "lightrag"
    postgres_password: str = "lightrag"
    postgres_provisioning_mode: str = "per_domain"
    postgres_admin_database: str = "context_engine"
    postgres_vector_extension: str = "vector"
    postgres_age_extension: str = "age"
    postgres_vector_index_type: str = "HNSW"
    tokenizer_offline: bool = True
    tiktoken_cache_dir: str = "/app/.cache/tiktoken"
    database_url_for_admin: str = ""
    runtime_postgres_database: str = "context_engine"
    runtime_postgres_user: str = "context_engine"
    runtime_postgres_password: str = "context_engine"
    redis_url: str | None = None
    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    llm_binding: str = "openai"
    llm_binding_host: str | None = None
    llm_binding_api_key: str | None = None
    llm_model: str | None = None
    keyword_llm_model: str | None = None
    query_llm_model: str | None = None
    vlm_llm_model: str | None = None
    embedding_binding: str = "openai"
    embedding_binding_host: str | None = None
    embedding_binding_api_key: str | None = None
    embedding_model: str | None = None
    embedding_dim: int | None = None
    embedding_token_limit: int | None = None
    embedding_send_dim: bool | None = None
    embedding_use_base64: bool | None = None
    openai_llm_max_tokens: int | None = None
    openai_llm_max_completion_tokens: int | None = None
    openai_llm_temperature: float | None = None
    openai_llm_extra_body: str | None = None
    archive_deleted_domains: bool = True
    allow_permanent_delete: bool = False
    docker_execution_mode: str = "host"
    docker_compose_bin: str = "docker compose"
    docker_timeout_seconds: int = 120

    @classmethod
    def from_app_settings(cls, settings: Settings) -> "LightRAGDeploySettings":
        runtime_database, runtime_user, runtime_password = _runtime_postgres_credentials(
            settings.database_url
        )
        return cls(
            deploy_root=settings.lightrag_deploy_root,
            domains_root=settings.lightrag_domains_root,
            manifest_path=settings.lightrag_domain_registry,
            compose_file=settings.lightrag_compose_file,
            deleted_root=settings.lightrag_deleted_root,
            default_port_start=settings.lightrag_default_port_start,
            default_container_port=settings.lightrag_default_container_port,
            host=settings.lightrag_host,
            docker_network=settings.lightrag_docker_network,
            domain_env_filename=settings.lightrag_domain_env_filename,
            dockerfile=settings.lightrag_dockerfile or Path("docker/lightrag.Dockerfile"),
            build_context=settings.lightrag_build_context or Path("."),
            storage_backend=settings.lightrag_storage_backend,
            postgres_url=settings.lightrag_postgres_url,
            postgres_host=settings.lightrag_postgres_host,
            postgres_port=settings.lightrag_postgres_port,
            postgres_database_prefix=settings.lightrag_postgres_database_prefix,
            postgres_user_prefix=settings.lightrag_postgres_user_prefix,
            postgres_password=settings.lightrag_postgres_password,
            postgres_provisioning_mode=settings.lightrag_postgres_provisioning_mode,
            postgres_admin_database=settings.lightrag_postgres_admin_database,
            postgres_vector_extension=settings.lightrag_postgres_vector_extension,
            postgres_age_extension=settings.lightrag_postgres_age_extension,
            postgres_vector_index_type=settings.lightrag_postgres_vector_index_type,
            tokenizer_offline=settings.lightrag_tokenizer_offline,
            tiktoken_cache_dir=settings.lightrag_tiktoken_cache_dir,
            database_url_for_admin=settings.database_url,
            runtime_postgres_database=runtime_database,
            runtime_postgres_user=runtime_user,
            runtime_postgres_password=runtime_password or settings.lightrag_postgres_password,
            redis_url=settings.lightrag_redis_url,
            neo4j_uri=settings.lightrag_neo4j_uri,
            neo4j_username=settings.lightrag_neo4j_username,
            neo4j_password=settings.lightrag_neo4j_password,
            llm_binding=settings.lightrag_llm_binding,
            llm_binding_host=settings.lightrag_llm_binding_host,
            llm_binding_api_key=settings.lightrag_llm_binding_api_key,
            llm_model=settings.lightrag_llm_model,
            keyword_llm_model=settings.lightrag_keyword_llm_model,
            query_llm_model=settings.lightrag_query_llm_model,
            vlm_llm_model=settings.lightrag_vlm_llm_model,
            embedding_binding=settings.lightrag_embedding_binding,
            embedding_binding_host=settings.lightrag_embedding_binding_host,
            embedding_binding_api_key=settings.lightrag_embedding_binding_api_key,
            embedding_model=settings.lightrag_embedding_model,
            embedding_dim=settings.lightrag_embedding_dim,
            embedding_token_limit=settings.lightrag_embedding_token_limit,
            embedding_send_dim=settings.lightrag_embedding_send_dim,
            embedding_use_base64=settings.lightrag_embedding_use_base64,
            openai_llm_max_tokens=settings.lightrag_openai_llm_max_tokens,
            openai_llm_max_completion_tokens=settings.lightrag_openai_llm_max_completion_tokens,
            openai_llm_temperature=settings.lightrag_openai_llm_temperature,
            openai_llm_extra_body=settings.lightrag_openai_llm_extra_body,
            archive_deleted_domains=settings.lightrag_archive_deleted_domains,
            allow_permanent_delete=settings.lightrag_allow_permanent_delete,
            docker_execution_mode=settings.lightrag_docker_execution_mode,
            docker_compose_bin=settings.lightrag_docker_compose_bin,
            docker_timeout_seconds=settings.lightrag_docker_timeout_seconds,
        )


def _runtime_postgres_credentials(database_url: str) -> tuple[str, str, str | None]:
    parsed = urlparse(database_url)
    if not parsed.scheme.startswith("postgresql"):
        return "context_engine", "context_engine", None
    database = parsed.path.lstrip("/") or "context_engine"
    user = unquote(parsed.username) if parsed.username else "context_engine"
    password = unquote(parsed.password) if parsed.password else None
    return database, user, password
