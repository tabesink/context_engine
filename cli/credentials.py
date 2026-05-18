"""Credential storage for the terminal app."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StoredCredentials:
    base_url: str
    access_token: str


class CredentialStore:
    """Keyring-first token store with local file fallback."""

    def __init__(
        self,
        config_dir: Path,
        *,
        service_name: str = "context-engine-cli",
        keyring_enabled: bool = True,
    ):
        self.config_dir = config_dir
        self.service_name = service_name
        self.username = "default"
        self.fallback_file = config_dir / "credentials.json"
        self._keyring = None
        if keyring_enabled:
            try:
                import keyring  # type: ignore
            except Exception:
                keyring = None
            self._keyring = keyring

    def save(self, creds: StoredCredentials) -> str | None:
        value = json.dumps({"base_url": creds.base_url, "access_token": creds.access_token})
        if self._keyring is not None:
            try:
                self._keyring.set_password(self.service_name, self.username, value)
                return None
            except Exception:
                pass
        self._write_fallback(value)
        return f"OS keyring unavailable; credentials stored at {self.fallback_file}"

    def load(self) -> StoredCredentials | None:
        raw: str | None = None
        if self._keyring is not None:
            try:
                raw = self._keyring.get_password(self.service_name, self.username)
            except Exception:
                raw = None
        if raw is None and self.fallback_file.exists():
            raw = self.fallback_file.read_text(encoding="utf-8")
        if not raw:
            return None
        data = json.loads(raw)
        return StoredCredentials(base_url=str(data["base_url"]), access_token=str(data["access_token"]))

    def clear(self) -> None:
        if self._keyring is not None:
            try:
                self._keyring.delete_password(self.service_name, self.username)
            except Exception:
                pass
        self.fallback_file.unlink(missing_ok=True)

    def _write_fallback(self, value: str) -> None:
        self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
        self.fallback_file.write_text(value, encoding="utf-8")
        try:
            os.chmod(self.fallback_file, 0o600)
        except Exception:
            pass

