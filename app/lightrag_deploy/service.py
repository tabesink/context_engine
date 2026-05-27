import shutil
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import Any

from app.core.config import get_settings
from app.lightrag_deploy.compose import ComposeGenerator, write_domain_env
from app.lightrag_deploy.docker_runner import (
    CommandResult,
    DockerComposeRunner,
    SubprocessDockerComposeRunner,
)
from app.lightrag_deploy.errors import DomainNotFoundError, PermanentDeleteDisabledError
from app.lightrag_deploy.manifest import DomainManifestStore
from app.lightrag_deploy.models import (
    DomainEmbeddingSnapshot,
    DomainLLMSnapshot,
    DomainRetrievalDefaults,
    LightRAGDomain,
    LightRAGDomainCreateRequest,
    LightRAGDomainOperationResult,
    LightRAGDomainRepairResult,
    LightRAGDomainRemoveResponse,
)
from app.lightrag_deploy.paths import DomainPathResolver, DomainPaths
from app.lightrag_deploy.postgres_provisioner import LightRAGPostgresProvisioner
from app.lightrag_deploy.settings import LightRAGDeploySettings
from app.services.model_profile_resolver import ModelProfileResolver
from app.services.lightrag_reachability_service import (
    LightRAGReachabilityReport,
    LightRAGReachabilityService,
)


class LightRAGDomainService:
    def __init__(
        self,
        *,
        settings: LightRAGDeploySettings | None = None,
        runner: DockerComposeRunner | None = None,
        profile_resolver: ModelProfileResolver | None = None,
        postgres_provisioner: Any | None = None,
        now: Callable[[], datetime] | None = None,
    ):
        self.settings = settings or LightRAGDeploySettings.from_app_settings(get_settings())
        self.paths = DomainPathResolver(self.settings)
        self.manifest = DomainManifestStore(self.settings.manifest_path)
        self.compose = ComposeGenerator(self.settings)
        self.runner = runner or SubprocessDockerComposeRunner(
            compose_file=self.settings.compose_file,
            compose_bin=self.settings.docker_compose_bin,
            timeout_seconds=self.settings.docker_timeout_seconds,
        )
        self.profile_resolver = profile_resolver
        self.postgres_provisioner = postgres_provisioner or self._default_postgres_provisioner()
        self.now = now or (lambda: datetime.now(UTC))

    def list_domains(self) -> list[LightRAGDomain]:
        return self.manifest.list_domains()

    def get_domain(self, domain_id: str) -> LightRAGDomain:
        domain = self.manifest.get_domain(domain_id)
        if domain is None:
            raise DomainNotFoundError(f"LightRAG domain '{domain_id}' does not exist")
        return domain

    def create_domain(self, request: LightRAGDomainCreateRequest) -> LightRAGDomain:
        existing = self.list_domains()
        domain_id = request.domain_id
        paths = self.paths.ensure_domain_paths(domain_id)
        host_port = request.host_port or self._next_port(existing)
        timestamp = self.now()
        service_name = f"lightrag_{domain_id}"
        postgres_suffix = self._postgres_identifier(domain_id)
        host_base_url = f"http://{self.settings.host}:{host_port}"
        container_base_url = f"http://{service_name}:{self.settings.default_container_port}"
        base_url = container_base_url if self.settings.docker_execution_mode == "socket" else host_base_url
        embedding_profile = (
            self.profile_resolver.resolve_embedding_profile(request.embedding_profile_id)
            if self.profile_resolver
            else None
        )
        embedding_snapshot = (
            DomainEmbeddingSnapshot(
                profile_id=embedding_profile.id,
                provider=embedding_profile.provider,
                binding=embedding_profile.binding,
                base_url=embedding_profile.base_url,
                api_key_env_var=embedding_profile.api_key_env_var,
                model=embedding_profile.model,
                dimensions=embedding_profile.dimensions,
                token_limit=embedding_profile.token_limit,
                send_dimensions=embedding_profile.send_dimensions,
                use_base64=embedding_profile.use_base64,
                fingerprint=f"{embedding_profile.provider}:{embedding_profile.model}:{embedding_profile.dimensions or 'unknown'}",
            )
            if embedding_profile
            else None
        )
        domain = LightRAGDomain(
            id=domain_id,
            display_name=request.display_name or domain_id,
            workspace=domain_id,
            postgres_database=f"{self.settings.postgres_database_prefix}_{postgres_suffix}",
            postgres_user=f"{self.settings.postgres_user_prefix}_{postgres_suffix}",
            host=self.settings.host,
            host_port=host_port,
            container_port=self.settings.default_container_port,
            base_url=base_url,
            host_base_url=host_base_url,
            container_base_url=container_base_url,
            container_name=f"context_engine_lightrag_{domain_id}",
            service_name=service_name,
            status="configured",
            paths=paths.as_manifest_paths(),
            embedding=embedding_snapshot,
            retrieval_defaults=DomainRetrievalDefaults(
                top_k=request.top_k,
                chunk_top_k=request.chunk_top_k,
                chunk_rerank_top_k=request.chunk_rerank_top_k,
                max_token_for_text_unit=request.max_token_for_text_unit,
                max_token_for_global_context=request.max_token_for_global_context,
                max_token_for_local_context=request.max_token_for_local_context,
            ),
            is_default=request.make_default or not any(domain.is_default for domain in existing),
            created_at=timestamp,
            updated_at=timestamp,
        )
        domain = self._ensure_postgres_identity(domain)
        self._provision_domain_postgres(domain)
        self._write_domain_env(domain, paths)
        self.manifest.add_domain(domain)
        self.compose.write(self.list_domains())
        return domain

    def regenerate(self, domain_id: str | None = None) -> None:
        domains = [self.get_domain(domain_id)] if domain_id else self.list_domains()
        for domain in domains:
            domain = self._ensure_postgres_identity(domain)
            self._provision_domain_postgres(domain)
            self._write_domain_env(domain, self.paths.ensure_domain_paths(domain.id))
        self.compose.write(self.list_domains())

    def lock_embedding_for_domain(
        self,
        *,
        domain_id: str,
        document_id: str,
        reason: str = "first_successful_ingestion",
    ) -> LightRAGDomain:
        domain = self.get_domain(domain_id)
        if domain.embedding is None:
            raise ValueError(
                f"LightRAG domain '{domain_id}' cannot be locked because embedding is not configured"
            )
        if domain.embedding_locked_at is not None:
            return domain
        updated = domain.model_copy(
            update={
                "embedding_locked_at": self.now(),
                "embedding_lock_reason": reason,
                "first_ingested_document_id": document_id,
                "updated_at": self.now(),
            }
        )
        self.manifest.update_domain(updated)
        return updated

    def up(
        self,
        domain_id: str,
        *,
        reachability: LightRAGReachabilityService | None = None,
        attempts: int = 5,
        sleep_seconds: float = 1.0,
    ) -> LightRAGDomainOperationResult:
        domain = self._ensure_postgres_identity(self.get_domain(domain_id))
        self._provision_domain_postgres(domain)
        self._write_domain_env(domain, self.paths.ensure_domain_paths(domain.id))
        self.compose.write(self.list_domains())
        build_result = self.runner.build(domain.service_name)
        if build_result.exit_code != 0:
            result = self._operation_result(domain, "up", build_result)
            self._persist_domain_status(domain, command_succeeded=False, running=False)
            return result
        result = self._operation_result(domain, "up", self.runner.up(domain.service_name))
        if result.status == "succeeded":
            health = self._probe_domain_health(
                domain.id,
                reachability=reachability,
                attempts=attempts,
                sleep_seconds=sleep_seconds,
            )
            self._persist_started_domain_health(domain, health)
        else:
            self._persist_domain_status(domain, command_succeeded=False, running=False)
        return result

    def down(self, domain_id: str) -> LightRAGDomainOperationResult:
        domain = self.get_domain(domain_id)
        result = self._operation_result(domain, "down", self.runner.stop(domain.service_name))
        self._persist_domain_status(domain, command_succeeded=result.status == "succeeded", running=False)
        return result

    def recreate(
        self,
        domain_id: str,
        *,
        reachability: LightRAGReachabilityService | None = None,
        attempts: int = 5,
        sleep_seconds: float = 1.0,
    ) -> LightRAGDomainOperationResult:
        domain = self._ensure_postgres_identity(self.get_domain(domain_id))
        self._provision_domain_postgres(domain)
        self._write_domain_env(domain, self.paths.ensure_domain_paths(domain.id))
        self.compose.write(self.list_domains())
        build_result = self.runner.build(domain.service_name)
        if build_result.exit_code != 0:
            result = self._operation_result(domain, "recreate", build_result)
            self._persist_domain_status(domain, command_succeeded=False, running=False)
            return result
        result = self._operation_result(domain, "recreate", self.runner.recreate(domain.service_name))
        if result.status == "succeeded":
            health = self._probe_domain_health(
                domain.id,
                reachability=reachability,
                attempts=attempts,
                sleep_seconds=sleep_seconds,
            )
            self._persist_started_domain_health(domain, health)
        else:
            self._persist_domain_status(domain, command_succeeded=False, running=False)
        return result

    def repair(
        self,
        domain_id: str,
        *,
        reachability: LightRAGReachabilityService | None = None,
        attempts: int = 5,
        sleep_seconds: float = 1.0,
    ) -> LightRAGDomainRepairResult:
        domain = self._ensure_postgres_identity(self.get_domain(domain_id))
        provision_result = self._provision_domain_postgres(domain)
        self._write_domain_env(domain, self.paths.ensure_domain_paths(domain.id))
        self.compose.write(self.list_domains())
        build_result = self.runner.build(domain.service_name)
        if build_result.exit_code != 0:
            result = self._operation_result(domain, "repair", build_result)
            updated = self._persist_domain_status(
                domain,
                command_succeeded=False,
                running=False,
            )
            return self._repair_response(
                domain=updated,
                operation=result,
                health=None,
                provision_result=provision_result,
            )
        result = self._operation_result(domain, "repair", self.runner.recreate(domain.service_name))
        if result.status != "succeeded":
            updated = self._persist_domain_status(
                domain,
                command_succeeded=False,
                running=False,
            )
            return self._repair_response(
                domain=updated,
                operation=result,
                health=None,
                provision_result=provision_result,
            )

        health = self._probe_domain_health(
            domain_id,
            reachability=reachability,
            attempts=attempts,
            sleep_seconds=sleep_seconds,
        )

        updated = self._persist_domain_health(domain, health)
        return self._repair_response(
            domain=updated,
            operation=result,
            health=health,
            provision_result=provision_result,
        )

    def remove(self, domain_id: str, *, permanent: bool = False) -> LightRAGDomainRemoveResponse:
        domain = self.get_domain(domain_id)
        if permanent and not self.settings.allow_permanent_delete:
            raise PermanentDeleteDisabledError("Permanent LightRAG domain delete is disabled")

        removed = self.manifest.remove_domain(domain_id)
        self.compose.write(self.list_domains())
        root = Path(removed.paths["root"])
        if permanent:
            shutil.rmtree(root, ignore_errors=True)
            return LightRAGDomainRemoveResponse(id=domain.id, archived=False, permanent=True)

        archive_path = self._archive_path(domain.id)
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if root.exists():
            shutil.move(str(root), str(archive_path))
        else:
            archive_path.mkdir(parents=True, exist_ok=True)
        return LightRAGDomainRemoveResponse(
            id=domain.id,
            archived=True,
            archive_path=str(archive_path),
            permanent=False,
        )

    def _next_port(self, domains: list[LightRAGDomain]) -> int:
        used_ports = {domain.host_port for domain in domains}
        port = self.settings.default_port_start
        while port in used_ports:
            port += 1
        return port

    def _write_domain_env(self, domain: LightRAGDomain, paths: DomainPaths) -> None:
        llm = self._default_llm_snapshot()
        write_domain_env(
            domain,
            self.settings,
            paths,
            self._provider_secrets_for_domain(domain, llm=llm),
            llm=llm,
        )

    def _default_llm_snapshot(self) -> DomainLLMSnapshot | None:
        if not self.profile_resolver or not hasattr(self.profile_resolver, "resolve_llm_profile"):
            return None
        profile = self.profile_resolver.resolve_llm_profile()
        return DomainLLMSnapshot(
            profile_id=profile.id,
            provider=profile.provider,
            binding=profile.binding,
            base_url=profile.base_url,
            api_key_env_var=profile.api_key_env_var,
            model=profile.model,
        )

    def _provider_secrets_for_domain(
        self,
        domain: LightRAGDomain,
        *,
        llm: DomainLLMSnapshot | None = None,
    ) -> dict[str, str] | None:
        if not self.profile_resolver:
            return None
        if not hasattr(self.profile_resolver, "get_provider_secret_value"):
            return None
        secrets: dict[str, str] = {}
        secret_names = [
            llm.api_key_env_var if llm else None,
            domain.embedding.api_key_env_var if domain.embedding else None,
        ]
        for secret_name in secret_names:
            if not secret_name or secret_name in secrets:
                continue
            secret_value = self.profile_resolver.get_provider_secret_value(secret_name)
            if secret_value:
                secrets[secret_name] = secret_value
        return secrets or None

    def _default_postgres_provisioner(self) -> LightRAGPostgresProvisioner | None:
        if self.settings.storage_backend != "postgres":
            return None
        if not self.settings.database_url_for_admin.startswith("postgresql"):
            return None
        return LightRAGPostgresProvisioner(self.settings)

    def _ensure_postgres_identity(self, domain: LightRAGDomain) -> LightRAGDomain:
        if self.settings.storage_backend != "postgres":
            return domain
        postgres_suffix = self._postgres_identifier(domain.id)
        updates: dict[str, Any] = {}
        if not domain.postgres_database:
            updates["postgres_database"] = f"{self.settings.postgres_database_prefix}_{postgres_suffix}"
        if not domain.postgres_user:
            updates["postgres_user"] = f"{self.settings.postgres_user_prefix}_{postgres_suffix}"
        if not updates:
            return domain

        updated = domain.model_copy(update={**updates, "updated_at": self.now()})
        if self.manifest.get_domain(domain.id) is not None:
            self.manifest.update_domain(updated)
        return updated

    def _provision_domain_postgres(self, domain: LightRAGDomain) -> Any | None:
        if self.settings.storage_backend != "postgres" or self.postgres_provisioner is None:
            return None
        return self.postgres_provisioner.provision_domain(domain)

    def _archive_path(self, domain_id: str) -> Path:
        timestamp = self.now().strftime("%Y-%m-%d-%H%M%S")
        return self.settings.deleted_root / f"{domain_id}-{timestamp}"

    def _postgres_identifier(self, domain_id: str) -> str:
        safe = re.sub(r"[^a-z0-9_]", "_", domain_id.lower())
        return safe[:48].strip("_") or "domain"

    def _operation_result(
        self,
        domain: LightRAGDomain,
        operation: str,
        command: CommandResult,
    ) -> LightRAGDomainOperationResult:
        return LightRAGDomainOperationResult(
            id=domain.id,
            operation=operation,
            status="succeeded" if command.exit_code == 0 else "failed",
            service_name=domain.service_name,
            message=command.stderr or command.stdout or None,
        )

    def _persist_domain_status(
        self,
        domain: LightRAGDomain,
        *,
        command_succeeded: bool,
        running: bool,
    ) -> LightRAGDomain:
        if not command_succeeded:
            updated = domain.model_copy(
                update={"status": "error", "is_healthy": False, "updated_at": self.now()}
            )
        else:
            updated = domain.model_copy(
                update={
                    "status": "running_unverified" if running else "stopped",
                    "is_healthy": False,
                    "updated_at": self.now(),
                }
            )
        self.manifest.update_domain(updated)
        return updated

    def _probe_domain_health(
        self,
        domain_id: str,
        *,
        reachability: LightRAGReachabilityService | None = None,
        attempts: int = 5,
        sleep_seconds: float = 1.0,
    ) -> LightRAGReachabilityReport | None:
        probe = reachability or LightRAGReachabilityService()
        health: LightRAGReachabilityReport | None = None
        for attempt in range(max(1, attempts)):
            health = probe.probe(domain_id)
            if health.healthy:
                break
            if attempt < attempts - 1:
                sleep(sleep_seconds)
        return health

    def _persist_started_domain_health(
        self,
        domain: LightRAGDomain,
        health: LightRAGReachabilityReport | None,
    ) -> LightRAGDomain:
        if health and health.healthy:
            return self._persist_domain_health(domain, health)
        return self._persist_domain_status(domain, command_succeeded=True, running=True)

    def _persist_domain_health(
        self,
        domain: LightRAGDomain,
        health: LightRAGReachabilityReport | None,
    ) -> LightRAGDomain:
        healthy = bool(health and health.healthy)
        updated = domain.model_copy(
            update={
                "status": "running" if healthy else "unhealthy",
                "is_healthy": healthy,
                "updated_at": self.now(),
            }
        )
        self.manifest.update_domain(updated)
        return updated

    def _repair_response(
        self,
        *,
        domain: LightRAGDomain,
        operation: LightRAGDomainOperationResult,
        health: LightRAGReachabilityReport | None,
        provision_result: Any | None,
    ) -> LightRAGDomainRepairResult:
        extensions = {}
        if provision_result is not None:
            extensions = {
                name: {
                    "name": status.name,
                    "status": status.status,
                    "message": status.message,
                }
                for name, status in getattr(provision_result, "extensions", {}).items()
            }
        return LightRAGDomainRepairResult(
            id=domain.id,
            domain_id=domain.id,
            operation=operation.operation,
            status=domain.status,
            service_name=domain.service_name,
            storage_backend=self.settings.storage_backend,
            postgres_database=domain.postgres_database,
            postgres_user=domain.postgres_user,
            postgres_role_exists=getattr(provision_result, "role_exists", None),
            postgres_database_exists=getattr(provision_result, "database_exists", None),
            extensions=extensions,
            host_base_url=domain.host_base_url,
            container_base_url=domain.container_base_url,
            runtime_base_url=health.base_url if health else domain.base_url,
            docker_operation=operation.status,
            health=health.as_dict() if health else None,
            is_healthy=domain.is_healthy,
            message=operation.message,
        )

