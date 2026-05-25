from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.lightrag_deploy.docker_runner import CommandResult
from app.lightrag_deploy.errors import DomainNotFoundError, PermanentDeleteDisabledError
from app.lightrag_deploy.models import LightRAGDomainCreateRequest
from app.lightrag_deploy.service import LightRAGDomainService
from app.lightrag_deploy.settings import LightRAGDeploySettings


class FakeRunner:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def up(self, service_name: str) -> CommandResult:
        self.calls.append(("up", service_name))
        return self._result()

    def stop(self, service_name: str) -> CommandResult:
        self.calls.append(("stop", service_name))
        return self._result()

    def recreate(self, service_name: str) -> CommandResult:
        self.calls.append(("recreate", service_name))
        return self._result()

    def ps(self) -> CommandResult:
        self.calls.append(("ps", ""))
        return self._result()

    def _result(self) -> CommandResult:
        if self.fail:
            return CommandResult(exit_code=1, stdout="", stderr="docker failed")
        return CommandResult(exit_code=0, stdout="ok", stderr="")


def _settings(tmp_path: Path, *, allow_permanent_delete: bool = False) -> LightRAGDeploySettings:
    return LightRAGDeploySettings(
        enabled=True,
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag" / "domains",
        manifest_path=tmp_path / "lightrag" / "domains.json",
        compose_file=tmp_path / "lightrag" / "docker-compose.lightrag-domains.yml",
        deleted_root=tmp_path / "lightrag" / "deleted",
        allow_permanent_delete=allow_permanent_delete,
        image="example/lightrag:test",
    )


def _settings_with_provider(tmp_path: Path) -> LightRAGDeploySettings:
    return replace(
        _settings(tmp_path),
        llm_binding="openai",
        llm_binding_host="https://bedrock-runtime.us-west-2.amazonaws.com/openai/v1",
        llm_binding_api_key="test-bedrock-key",
        llm_model="openai.gpt-oss-20b-1:0",
        embedding_binding="openai",
        embedding_binding_host="https://api.openai.com/v1",
        embedding_binding_api_key="test-openai-key",
        embedding_model="text-embedding-3-large",
        embedding_dim=3072,
        embedding_token_limit=8192,
        embedding_send_dim=False,
        embedding_use_base64=True,
    )


def _service(tmp_path: Path, runner: FakeRunner | None = None) -> LightRAGDomainService:
    return LightRAGDomainService(
        settings=_settings(tmp_path),
        runner=runner or FakeRunner(),
        now=lambda: datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )


def test_create_domain_generates_manifest_env_and_compose(tmp_path: Path) -> None:
    service = _service(tmp_path)

    domain = service.create_domain(
        LightRAGDomainCreateRequest(domain_id="fatigue", display_name="Fatigue Manuals")
    )

    assert domain.id == "fatigue"
    assert domain.host_port == 9621
    assert domain.is_default is True
    assert service.list_domains() == [domain]
    assert (tmp_path / "lightrag/domains/fatigue/domain.env").is_file()
    assert "lightrag_fatigue:" in (tmp_path / "lightrag/docker-compose.lightrag-domains.yml").read_text(
        encoding="utf-8"
    )


def test_create_domain_renders_postgres_owned_lightrag_storage_without_manifest_secrets(
    tmp_path: Path,
) -> None:
    service = _service(tmp_path)

    service.create_domain(LightRAGDomainCreateRequest(domain_id="manual-domain"))

    env_text = (tmp_path / "lightrag/domains/manual-domain/domain.env").read_text(
        encoding="utf-8"
    )
    manifest_text = (tmp_path / "lightrag/domains.json").read_text(encoding="utf-8")
    assert "WORKSPACE=manual-domain" in env_text
    assert "LIGHTRAG_KV_STORAGE=PGKVStorage" in env_text
    assert "LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage" in env_text
    assert "LIGHTRAG_GRAPH_STORAGE=PGGraphStorage" in env_text
    assert "LIGHTRAG_VECTOR_STORAGE=PGVectorStorage" in env_text
    assert "POSTGRES_HOST=postgres" in env_text
    assert "POSTGRES_DATABASE=lightrag_manual_domain" in env_text
    assert "POSTGRES_USER=lightrag_manual_domain" in env_text
    assert "POSTGRES_PASSWORD=" in env_text
    assert "postgres_database" in manifest_text
    assert "POSTGRES_PASSWORD" not in manifest_text


def test_create_domain_keeps_provider_keys_in_domain_env_only(tmp_path: Path) -> None:
    settings = _settings_with_provider(tmp_path)
    service = LightRAGDomainService(
        settings=settings,
        runner=FakeRunner(),
        now=lambda: datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )

    service.create_domain(LightRAGDomainCreateRequest(domain_id="manual-domain"))

    env_text = (tmp_path / "lightrag/domains/manual-domain/domain.env").read_text(
        encoding="utf-8"
    )
    manifest_text = (tmp_path / "lightrag/domains.json").read_text(encoding="utf-8")
    compose_text = (tmp_path / "lightrag/docker-compose.lightrag-domains.yml").read_text(
        encoding="utf-8"
    )

    assert "LLM_BINDING_API_KEY=test-bedrock-key" in env_text
    assert "EMBEDDING_BINDING_API_KEY=test-openai-key" in env_text
    assert "test-bedrock-key" not in manifest_text
    assert "test-openai-key" not in manifest_text
    assert "test-bedrock-key" not in compose_text
    assert "test-openai-key" not in compose_text


def test_create_domain_auto_selects_next_available_port(tmp_path: Path) -> None:
    service = _service(tmp_path)

    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))
    second = service.create_domain(LightRAGDomainCreateRequest(domain_id="abaqus"))

    assert second.host_port == 9622


def test_show_missing_domain_raises_typed_error(tmp_path: Path) -> None:
    with pytest.raises(DomainNotFoundError):
        _service(tmp_path).get_domain("missing")


def test_remove_archives_domain_directory_by_default(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    result = service.remove("fatigue")

    assert result.id == "fatigue"
    assert result.archived is True
    assert result.permanent is False
    assert result.archive_path is not None
    assert Path(result.archive_path).is_dir()
    assert service.list_domains() == []


def test_permanent_delete_requires_config_opt_in(tmp_path: Path) -> None:
    service = _service(tmp_path)
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    with pytest.raises(PermanentDeleteDisabledError):
        service.remove("fatigue", permanent=True)


def test_permanent_delete_removes_domain_when_allowed(tmp_path: Path) -> None:
    service = LightRAGDomainService(
        settings=_settings(tmp_path, allow_permanent_delete=True),
        runner=FakeRunner(),
        now=lambda: datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    result = service.remove("fatigue", permanent=True)

    assert result.archived is False
    assert result.permanent is True
    assert not (tmp_path / "lightrag/domains/fatigue").exists()


def test_docker_operations_call_runner_with_domain_service_name(tmp_path: Path) -> None:
    runner = FakeRunner()
    service = _service(tmp_path, runner)
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    assert service.up("fatigue").status == "succeeded"
    assert service.down("fatigue").status == "succeeded"
    assert service.recreate("fatigue").status == "succeeded"

    assert runner.calls == [
        ("up", "lightrag_fatigue"),
        ("stop", "lightrag_fatigue"),
        ("recreate", "lightrag_fatigue"),
    ]


def test_docker_operations_update_manifest_runtime_status(tmp_path: Path) -> None:
    service = _service(tmp_path, FakeRunner())
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    service.up("fatigue")
    running = service.get_domain("fatigue")

    service.down("fatigue")
    stopped = service.get_domain("fatigue")

    assert running.status == "running"
    assert running.is_healthy is True
    assert stopped.status == "stopped"
    assert stopped.is_healthy is False


def test_docker_error_returns_failed_operation_result(tmp_path: Path) -> None:
    service = _service(tmp_path, FakeRunner(fail=True))
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    result = service.up("fatigue")

    assert result.status == "failed"
    assert result.message == "docker failed"
