import re
from dataclasses import dataclass
from pathlib import Path

from app.lightrag_deploy.settings import LightRAGDeploySettings

_DOMAIN_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}$")


@dataclass(frozen=True)
class DomainPaths:
    root: Path
    env_file: Path
    inputs: Path
    rag_storage: Path
    artifacts: Path
    logs: Path

    def as_manifest_paths(self) -> dict[str, str]:
        return {
            "root": self.root.as_posix(),
            "env_file": self.env_file.as_posix(),
            "inputs": self.inputs.as_posix(),
            "rag_storage": self.rag_storage.as_posix(),
            "artifacts": self.artifacts.as_posix(),
            "logs": self.logs.as_posix(),
        }


def validate_domain_id(domain_id: str) -> str:
    if not _DOMAIN_ID_PATTERN.fullmatch(domain_id):
        raise ValueError("Invalid LightRAG domain ID")
    return domain_id


class DomainPathResolver:
    def __init__(self, settings: LightRAGDeploySettings):
        self.settings = settings

    def domain_paths(self, domain_id: str) -> DomainPaths:
        safe_id = validate_domain_id(domain_id)
        root = self.settings.domains_root / safe_id
        return DomainPaths(
            root=root,
            env_file=root / self.settings.domain_env_filename,
            inputs=root / "inputs",
            rag_storage=root / "rag_storage",
            artifacts=root / "artifacts",
            logs=root / "logs",
        )

    def ensure_domain_paths(self, domain_id: str) -> DomainPaths:
        paths = self.domain_paths(domain_id)
        for path in [paths.inputs, paths.rag_storage, paths.artifacts, paths.logs]:
            path.mkdir(parents=True, exist_ok=True)
        return paths
