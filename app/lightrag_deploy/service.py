import shutil
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

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
    DomainRetrievalDefaults,
    LightRAGDomain,
    LightRAGDomainCreateRequest,
    LightRAGDomainOperationResult,
    LightRAGDomainRemoveResponse,
)
from app.lightrag_deploy.paths import DomainPathResolver
from app.lightrag_deploy.settings import LightRAGDeploySettings
from app.services.model_profile_resolver import ModelProfileResolver


class LightRAGDomainService:
    def __init__(
        self,
        *,
        settings: LightRAGDeploySettings | None = None,
        runner: DockerComposeRunner | None = None,
        profile_resolver: ModelProfileResolver | None = None,
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
        write_domain_env(domain, self.settings, paths, self._provider_secrets_for_domain(domain))
        self.manifest.add_domain(domain)
        self.compose.write(self.list_domains())
        return domain

    def regenerate(self, domain_id: str | None = None) -> None:
        domains = [self.get_domain(domain_id)] if domain_id else self.list_domains()
        for domain in domains:
            write_domain_env(
                domain,
                self.settings,
                self.paths.ensure_domain_paths(domain.id),
                self._provider_secrets_for_domain(domain),
            )
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

    def up(self, domain_id: str) -> LightRAGDomainOperationResult:
        domain = self.get_domain(domain_id)
        self.compose.write(self.list_domains())
        result = self._operation_result(domain, "up", self.runner.up(domain.service_name))
        self._persist_domain_status(domain, command_succeeded=result.status == "succeeded", running=True)
        return result

    def down(self, domain_id: str) -> LightRAGDomainOperationResult:
        domain = self.get_domain(domain_id)
        result = self._operation_result(domain, "down", self.runner.stop(domain.service_name))
        self._persist_domain_status(domain, command_succeeded=result.status == "succeeded", running=False)
        return result

    def recreate(self, domain_id: str) -> LightRAGDomainOperationResult:
        domain = self.get_domain(domain_id)
        self.compose.write(self.list_domains())
        result = self._operation_result(domain, "recreate", self.runner.recreate(domain.service_name))
        self._persist_domain_status(domain, command_succeeded=result.status == "succeeded", running=True)
        return result

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

    def _provider_secrets_for_domain(self, domain: LightRAGDomain) -> dict[str, str] | None:
        if not self.profile_resolver or not domain.embedding or not domain.embedding.api_key_env_var:
            return None
        if not hasattr(self.profile_resolver, "get_provider_secret_value"):
            return None
        secret_value = self.profile_resolver.get_provider_secret_value(domain.embedding.api_key_env_var)
        if not secret_value:
            return None
        return {domain.embedding.api_key_env_var: secret_value}

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
                    "status": "running" if running else "stopped",
                    "is_healthy": True if running else False,
                    "updated_at": self.now(),
                }
            )
        self.manifest.update_domain(updated)
        return updated

    def _sync_runtime_status(self, domain: LightRAGDomain) -> LightRAGDomain:
        ps = self.runner.ps()
        if ps.exit_code != 0:
            return domain
        text = ps.stdout.lower()
        service_name = domain.service_name.lower()
        if service_name not in text:
            return domain
        running = "running" in text or "up" in text
        status = "running" if running else "stopped"
        if domain.status == status and domain.is_healthy is running:
            return domain
        updated = domain.model_copy(
            update={"status": status, "is_healthy": running, "updated_at": self.now()}
        )
        self.manifest.update_domain(updated)
        return updated
