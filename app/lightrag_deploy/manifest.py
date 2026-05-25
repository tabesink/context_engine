import json
from pathlib import Path
from typing import Any

from app.lightrag_deploy.models import LightRAGDomain


class DomainManifestStore:
    def __init__(self, path: Path):
        self.path = path

    def list_domains(self) -> list[LightRAGDomain]:
        return self._read_domains()

    def get_domain(self, domain_id: str) -> LightRAGDomain | None:
        return next((domain for domain in self.list_domains() if domain.id == domain_id), None)

    def add_domain(self, domain: LightRAGDomain) -> None:
        domains = self._read_domains()
        if any(existing.id == domain.id for existing in domains):
            raise ValueError(f"LightRAG domain '{domain.id}' already exists")
        if any(existing.host_port == domain.host_port for existing in domains):
            raise ValueError(f"LightRAG domain port {domain.host_port} is already used")
        if domain.is_default:
            domains = [existing.model_copy(update={"is_default": False}) for existing in domains]
        self.write_domains([*domains, domain])

    def remove_domain(self, domain_id: str) -> LightRAGDomain:
        domains = self._read_domains()
        removed = next((domain for domain in domains if domain.id == domain_id), None)
        if removed is None:
            raise ValueError(f"LightRAG domain '{domain_id}' does not exist")
        self.write_domains([domain for domain in domains if domain.id != domain_id])
        return removed

    def update_domain(self, domain: LightRAGDomain) -> None:
        domains = self._read_domains()
        if not any(existing.id == domain.id for existing in domains):
            raise ValueError(f"LightRAG domain '{domain.id}' does not exist")
        self.write_domains([domain if existing.id == domain.id else existing for existing in domains])

    def write_domains(self, domains: list[LightRAGDomain]) -> None:
        payload = {
            "domains": [domain.to_manifest_dict() for domain in domains],
            "version": 1,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        tmp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        tmp_path.replace(self.path)

    def _read_domains(self) -> list[LightRAGDomain]:
        if not self.path.is_file():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        raw_domains = _domains_payload(payload)
        return [LightRAGDomain.model_validate(item) for item in raw_domains]


def _domains_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    domains = payload.get("domains", [])
    if isinstance(domains, list):
        return [item for item in domains if isinstance(item, dict)]
    if isinstance(domains, dict):
        return [
            {"id": key, **value}
            for key, value in domains.items()
            if isinstance(key, str) and isinstance(value, dict)
        ]
    return []
