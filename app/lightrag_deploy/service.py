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
    LightRAGDomain,
    LightRAGDomainCreateRequest,
    LightRAGDomainOperationResult,
    LightRAGDomainRemoveResponse,
)
from app.lightrag_deploy.paths import DomainPathResolver
from app.lightrag_deploy.settings import LightRAGDeploySettings


class LightRAGDomainService:
    def __init__(
        self,
        *,
        settings: LightRAGDeploySettings | None = None,
        runner: DockerComposeRunner | None = None,
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
        host_base_url = f"http://127.0.0.1:{host_port}"
        container_base_url = f"http://{service_name}:{self.settings.default_container_port}"
        base_url = container_base_url if self.settings.docker_execution_mode == "socket" else host_base_url
        domain = LightRAGDomain(
            id=domain_id,
            display_name=request.display_name or domain_id,
            workspace=domain_id,
            postgres_database=f"{self.settings.postgres_database_prefix}_{postgres_suffix}",
            postgres_user=f"{self.settings.postgres_user_prefix}_{postgres_suffix}",
            host="127.0.0.1",
            host_port=host_port,
            container_port=self.settings.default_container_port,
            base_url=base_url,
            host_base_url=host_base_url,
            container_base_url=container_base_url,
            container_name=f"context_engine_lightrag_{domain_id}",
            service_name=service_name,
            status="configured",
            paths=paths.as_manifest_paths(),
            is_default=request.make_default or not any(domain.is_default for domain in existing),
            created_at=timestamp,
            updated_at=timestamp,
        )
        write_domain_env(domain, self.settings, paths)
        self.manifest.add_domain(domain)
        self.compose.write(self.list_domains())
        return domain

    def regenerate(self, domain_id: str | None = None) -> None:
        domains = [self.get_domain(domain_id)] if domain_id else self.list_domains()
        for domain in domains:
            write_domain_env(domain, self.settings, self.paths.ensure_domain_paths(domain.id))
        self.compose.write(self.list_domains())

    def up(self, domain_id: str) -> LightRAGDomainOperationResult:
        domain = self.get_domain(domain_id)
        self.compose.write(self.list_domains())
        return self._operation_result(domain, "up", self.runner.up(domain.service_name))

    def down(self, domain_id: str) -> LightRAGDomainOperationResult:
        domain = self.get_domain(domain_id)
        return self._operation_result(domain, "down", self.runner.stop(domain.service_name))

    def recreate(self, domain_id: str) -> LightRAGDomainOperationResult:
        domain = self.get_domain(domain_id)
        self.compose.write(self.list_domains())
        return self._operation_result(domain, "recreate", self.runner.recreate(domain.service_name))

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
