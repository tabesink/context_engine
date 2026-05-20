from pathlib import Path

import pytest

from app.core.config import Settings
from app.lightrag_deploy.paths import DomainPathResolver, validate_domain_id
from app.lightrag_deploy.settings import LightRAGDeploySettings


def test_env_example_declares_lightrag_deployment_settings() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")

    for key in [
        "LIGHTRAG_DEPLOY_ENABLED",
        "LIGHTRAG_DEPLOY_ROOT",
        "LIGHTRAG_DOMAINS_ROOT",
        "LIGHTRAG_DOMAINS_MANIFEST",
        "LIGHTRAG_COMPOSE_FILE",
        "LIGHTRAG_DELETED_ROOT",
        "LIGHTRAG_DEFAULT_PORT_START",
        "LIGHTRAG_DEFAULT_CONTAINER_PORT",
        "LIGHTRAG_DOCKER_NETWORK",
        "LIGHTRAG_DOMAIN_ENV_FILENAME",
        "LIGHTRAG_IMAGE",
        "LIGHTRAG_DOCKER_EXECUTION_MODE",
        "LIGHTRAG_DOCKER_COMPOSE_BIN",
        "LIGHTRAG_DOCKER_TIMEOUT_SECONDS",
        "LIGHTRAG_POSTGRES_HOST",
        "LIGHTRAG_POSTGRES_PORT",
        "LIGHTRAG_POSTGRES_DATABASE_PREFIX",
        "LIGHTRAG_POSTGRES_USER_PREFIX",
        "LIGHTRAG_POSTGRES_PASSWORD",
    ]:
        assert f"{key}=" in env_example


def test_settings_parse_lightrag_deployment_fields(tmp_path: Path) -> None:
    settings = Settings(
        lightrag_deploy_enabled=True,
        lightrag_deploy_root=tmp_path / "lightrag",
        lightrag_domains_root=tmp_path / "lightrag" / "domains",
        lightrag_domains_manifest=tmp_path / "lightrag" / "domains.json",
        lightrag_compose_file=tmp_path / "lightrag" / "compose.yml",
        lightrag_deleted_root=tmp_path / "lightrag" / "deleted",
        lightrag_default_port_start=9700,
        lightrag_default_container_port=9621,
        lightrag_docker_network="ce_lightrag",
        lightrag_domain_env_filename="domain.env",
        lightrag_image="example/lightrag:test",
        lightrag_docker_execution_mode="socket",
        lightrag_docker_compose_bin="docker compose",
        lightrag_docker_timeout_seconds=30,
        lightrag_postgres_host="postgres",
        lightrag_postgres_port=5432,
        lightrag_postgres_database_prefix="lr",
        lightrag_postgres_user_prefix="lr_user",
        lightrag_postgres_password="secret",
    )

    deploy = LightRAGDeploySettings.from_app_settings(settings)

    assert deploy.enabled is True
    assert deploy.domains_root == tmp_path / "lightrag" / "domains"
    assert deploy.manifest_path == tmp_path / "lightrag" / "domains.json"
    assert deploy.default_port_start == 9700
    assert deploy.image == "example/lightrag:test"
    assert deploy.docker_execution_mode == "socket"
    assert deploy.postgres_host == "postgres"
    assert deploy.postgres_database_prefix == "lr"
    assert deploy.postgres_user_prefix == "lr_user"


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
