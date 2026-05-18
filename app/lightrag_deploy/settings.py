from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings


@dataclass(frozen=True)
class LightRAGDeploySettings:
    enabled: bool = False
    deploy_root: Path = Path(".data/lightrag")
    domains_root: Path = Path(".data/lightrag/domains")
    manifest_path: Path = Path(".data/lightrag/domains.json")
    compose_file: Path = Path(".data/lightrag/docker-compose.lightrag-domains.yml")
    deleted_root: Path = Path(".data/lightrag/deleted")
    default_port_start: int = 9621
    default_container_port: int = 9621
    docker_network: str = "context_engine_lightrag"
    domain_env_filename: str = "domain.env"
    image: str = "ghcr.io/hkuds/lightrag:latest"
    dockerfile: Path | None = None
    build_context: Path | None = None
    postgres_url: str | None = None
    redis_url: str | None = None
    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    archive_deleted_domains: bool = True
    allow_permanent_delete: bool = False
    docker_execution_mode: str = "host"
    docker_compose_bin: str = "docker compose"
    docker_timeout_seconds: int = 120

    @classmethod
    def from_app_settings(cls, settings: Settings) -> "LightRAGDeploySettings":
        return cls(
            enabled=settings.lightrag_deploy_enabled,
            deploy_root=settings.lightrag_deploy_root,
            domains_root=settings.lightrag_domains_root,
            manifest_path=settings.lightrag_domains_manifest,
            compose_file=settings.lightrag_compose_file,
            deleted_root=settings.lightrag_deleted_root,
            default_port_start=settings.lightrag_default_port_start,
            default_container_port=settings.lightrag_default_container_port,
            docker_network=settings.lightrag_docker_network,
            domain_env_filename=settings.lightrag_domain_env_filename,
            image=settings.lightrag_image,
            dockerfile=settings.lightrag_dockerfile,
            build_context=settings.lightrag_build_context,
            postgres_url=settings.lightrag_postgres_url,
            redis_url=settings.lightrag_redis_url,
            neo4j_uri=settings.lightrag_neo4j_uri,
            neo4j_username=settings.lightrag_neo4j_username,
            neo4j_password=settings.lightrag_neo4j_password,
            archive_deleted_domains=settings.lightrag_archive_deleted_domains,
            allow_permanent_delete=settings.lightrag_allow_permanent_delete,
            docker_execution_mode=settings.lightrag_docker_execution_mode,
            docker_compose_bin=settings.lightrag_docker_compose_bin,
            docker_timeout_seconds=settings.lightrag_docker_timeout_seconds,
        )
