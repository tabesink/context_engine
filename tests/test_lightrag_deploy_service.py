from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.lightrag_deploy.docker_runner import CommandResult
from app.lightrag_deploy.errors import DomainNotFoundError, PermanentDeleteDisabledError
from app.lightrag_deploy.models import LightRAGDomainCreateRequest
from app.lightrag_deploy.postgres_provisioner import (
    LightRAGPostgresProvisionResult,
    PostgresExtensionStatus,
)
from app.lightrag_deploy.service import LightRAGDomainService
from app.lightrag_deploy.settings import LightRAGDeploySettings
from app.services.lightrag_reachability_service import LightRAGReachabilityReport


class FakeProfile:
    def __init__(
        self,
        *,
        profile_id: str,
        provider: str,
        binding: str,
        base_url: str,
        model: str,
        dimensions: int,
    ) -> None:
        self.id = profile_id
        self.kind = "embedding"
        self.provider = provider
        self.binding = binding
        self.base_url = base_url
        self.api_key_env_var = None
        self.model = model
        self.dimensions = dimensions
        self.token_limit = 8192
        self.send_dimensions = False
        self.use_base64 = True
        self.is_enabled = True


class FakeProfileResolver:
    def __init__(self) -> None:
        self.default = FakeProfile(
            profile_id="openai-text-embedding-3-small",
            provider="openai",
            binding="openai",
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-small",
            dimensions=1536,
        )
        self.alt = FakeProfile(
            profile_id="openai-text-embedding-3-large",
            provider="openai",
            binding="openai",
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-large",
            dimensions=3072,
        )

    def resolve_embedding_profile(self, embedding_profile_id: str | None = None) -> FakeProfile:
        if embedding_profile_id == self.alt.id:
            return self.alt
        return self.default


class FakeRunner:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, str]] = []

    def up(self, service_name: str) -> CommandResult:
        self.calls.append(("up", service_name))
        return self._result()

    def build(self, service_name: str) -> CommandResult:
        self.calls.append(("build", service_name))
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


class FakePostgresProvisioner:
    def __init__(self, env_file: Path | None = None) -> None:
        self.env_file = env_file
        self.calls: list[tuple[str | None, str | None]] = []

    def provision_domain(self, domain) -> LightRAGPostgresProvisionResult:
        if self.env_file is not None:
            assert not self.env_file.exists()
        self.calls.append((domain.postgres_database, domain.postgres_user))
        return LightRAGPostgresProvisionResult(
            database=domain.postgres_database or "",
            user=domain.postgres_user or "",
            role_exists=True,
            database_exists=True,
            extensions={"vector": PostgresExtensionStatus(name="vector", status="ok")},
        )


class FakeReachability:
    def __init__(self, healthy: bool = True) -> None:
        self.healthy = healthy
        self.calls: list[str] = []

    def probe(self, domain_id: str) -> LightRAGReachabilityReport:
        self.calls.append(domain_id)
        return LightRAGReachabilityReport(
            domain_id=domain_id,
            base_url=f"http://lightrag_{domain_id}:9621",
            healthy=self.healthy,
            code=None if self.healthy else "lightrag_domain_unreachable",
            reason_code=None if self.healthy else "connection_refused",
            reason=None if self.healthy else "Connection refused",
            status_code=200 if self.healthy else None,
        )


def _settings(tmp_path: Path, *, allow_permanent_delete: bool = False) -> LightRAGDeploySettings:
    return LightRAGDeploySettings(
        enabled=True,
        deploy_root=tmp_path / "lightrag",
        domains_root=tmp_path / "lightrag" / "domains",
        manifest_path=tmp_path / "lightrag" / "domains.json",
        compose_file=tmp_path / "lightrag" / "docker-compose.lightrag-domains.yml",
        deleted_root=tmp_path / "lightrag" / "deleted",
        allow_permanent_delete=allow_permanent_delete,
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
    assert domain.host_port == 9622
    assert domain.is_default is True
    assert service.list_domains() == [domain]
    assert (tmp_path / "lightrag/domains/fatigue/domain.env").is_file()
    assert "lightrag_fatigue:" in (tmp_path / "lightrag/docker-compose.lightrag-domains.yml").read_text(
        encoding="utf-8"
    )


def test_create_domain_provisions_domain_postgres_identity_before_writing_env(
    tmp_path: Path,
) -> None:
    env_file = tmp_path / "lightrag/domains/fatigue/domain.env"
    provisioner = FakePostgresProvisioner(env_file)
    service = LightRAGDomainService(
        settings=_settings(tmp_path),
        runner=FakeRunner(),
        postgres_provisioner=provisioner,
        now=lambda: datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )

    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    assert provisioner.calls == [("lightrag_fatigue", "lightrag_fatigue")]
    assert "POSTGRES_DATABASE=lightrag_fatigue" in env_file.read_text(encoding="utf-8")


def test_create_domain_renders_per_domain_postgres_storage_without_manifest_secrets(
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
    assert "POSTGRES_PASSWORD=lightrag" in env_text
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

    assert second.host_port == 9623


def test_create_domain_persists_custom_retrieval_defaults(tmp_path: Path) -> None:
    service = _service(tmp_path)

    domain = service.create_domain(
        LightRAGDomainCreateRequest(
            domain_id="fatigue",
            top_k=24,
            chunk_top_k=12,
            chunk_rerank_top_k=8,
            max_token_for_text_unit=2048,
            max_token_for_global_context=1536,
            max_token_for_local_context=1024,
        )
    )
    env_text = (tmp_path / "lightrag/domains/fatigue/domain.env").read_text(encoding="utf-8")

    assert domain.retrieval_defaults.top_k == 24
    assert domain.retrieval_defaults.chunk_top_k == 12
    assert domain.retrieval_defaults.chunk_rerank_top_k == 8
    assert domain.retrieval_defaults.max_token_for_text_unit == 2048
    assert domain.retrieval_defaults.max_token_for_global_context == 1536
    assert domain.retrieval_defaults.max_token_for_local_context == 1024
    assert "TOP_K=24" in env_text
    assert "CHUNK_TOP_K=12" in env_text
    assert "CHUNK_RERANK_TOP_K=8" in env_text
    assert "MAX_TOKEN_TEXT_CHUNK=2048" in env_text
    assert "MAX_TOKEN_RELATION_DESC=1536" in env_text
    assert "MAX_TOKEN_ENTITY_DESC=1024" in env_text


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
        ("build", "lightrag_fatigue"),
        ("up", "lightrag_fatigue"),
        ("stop", "lightrag_fatigue"),
        ("build", "lightrag_fatigue"),
        ("recreate", "lightrag_fatigue"),
    ]


def test_docker_operations_update_manifest_runtime_status(tmp_path: Path) -> None:
    service = _service(tmp_path, FakeRunner())
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    service.up("fatigue")
    running = service.get_domain("fatigue")

    service.down("fatigue")
    stopped = service.get_domain("fatigue")

    assert running.status == "running_unverified"
    assert running.is_healthy is False
    assert stopped.status == "stopped"
    assert stopped.is_healthy is False


def test_docker_error_returns_failed_operation_result(tmp_path: Path) -> None:
    service = _service(tmp_path, FakeRunner(fail=True))
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    result = service.up("fatigue")

    assert result.status == "failed"
    assert result.message == "docker failed"


def test_repair_regenerates_recreates_probes_and_marks_healthy(tmp_path: Path) -> None:
    runner = FakeRunner()
    reachability = FakeReachability(healthy=True)
    service = _service(tmp_path, runner)
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    result = service.repair(
        "fatigue",
        reachability=reachability,
        attempts=1,
        sleep_seconds=0,
    )
    domain = service.get_domain("fatigue")

    assert runner.calls == [("build", "lightrag_fatigue"), ("recreate", "lightrag_fatigue")]
    assert reachability.calls == ["fatigue"]
    assert result.docker_operation == "succeeded"
    assert result.postgres_database == "lightrag_fatigue"
    assert result.postgres_user == "lightrag_fatigue"
    assert result.postgres_role_exists is None
    assert result.health == {
        "ok": True,
        "code": None,
        "reason_code": None,
        "reason": None,
        "status_code": 200,
    }
    assert domain.status == "running"
    assert domain.is_healthy is True


def test_repair_marks_domain_unhealthy_when_probe_fails(tmp_path: Path) -> None:
    service = _service(tmp_path, FakeRunner())
    service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))

    result = service.repair(
        "fatigue",
        reachability=FakeReachability(healthy=False),
        attempts=1,
        sleep_seconds=0,
    )
    domain = service.get_domain("fatigue")

    assert result.health["reason_code"] == "connection_refused"
    assert domain.status == "unhealthy"
    assert domain.is_healthy is False


def test_repair_provisions_missing_postgres_identity_and_rewrites_env(
    tmp_path: Path,
) -> None:
    runner = FakeRunner()
    reachability = FakeReachability(healthy=True)
    provisioner = FakePostgresProvisioner()
    service = LightRAGDomainService(
        settings=_settings(tmp_path),
        runner=runner,
        postgres_provisioner=provisioner,
        now=lambda: datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )
    created = service.create_domain(LightRAGDomainCreateRequest(domain_id="legacy-domain"))
    service.manifest.update_domain(
        created.model_copy(update={"postgres_database": None, "postgres_user": None})
    )

    result = service.repair(
        "legacy-domain",
        reachability=reachability,
        attempts=1,
        sleep_seconds=0,
    )

    repaired = service.get_domain("legacy-domain")
    env_text = (tmp_path / "lightrag/domains/legacy-domain/domain.env").read_text(
        encoding="utf-8"
    )
    assert provisioner.calls[-1] == ("lightrag_legacy_domain", "lightrag_legacy_domain")
    assert repaired.postgres_database == "lightrag_legacy_domain"
    assert repaired.postgres_user == "lightrag_legacy_domain"
    assert "POSTGRES_DATABASE=lightrag_legacy_domain" in env_text
    assert "POSTGRES_USER=lightrag_legacy_domain" in env_text
    assert runner.calls == [("build", "lightrag_legacy-domain"), ("recreate", "lightrag_legacy-domain")]
    assert result.postgres_role_exists is True
    assert result.postgres_database_exists is True
    assert result.extensions["vector"]["status"] == "ok"


def test_create_domain_persists_embedding_snapshot(tmp_path: Path) -> None:
    resolver = FakeProfileResolver()
    service = LightRAGDomainService(
        settings=_settings(tmp_path),
        runner=FakeRunner(),
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
    assert domain.embedding.model == "text-embedding-3-large"
    assert domain.embedding.dimensions == 3072


def test_changing_default_embedding_does_not_mutate_existing_snapshot(tmp_path: Path) -> None:
    resolver = FakeProfileResolver()
    service = LightRAGDomainService(
        settings=_settings(tmp_path),
        runner=FakeRunner(),
        profile_resolver=resolver,
        now=lambda: datetime(2026, 5, 18, 14, 30, tzinfo=UTC),
    )
    created = service.create_domain(LightRAGDomainCreateRequest(domain_id="fatigue"))
    assert created.embedding is not None
    assert created.embedding.profile_id == "openai-text-embedding-3-small"

    resolver.default = resolver.alt
    service.regenerate("fatigue")
    domain = service.get_domain("fatigue")

    assert domain.embedding is not None
    assert domain.embedding.profile_id == "openai-text-embedding-3-small"
