"""Credential storage for CLI auth tokens."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StoredCredentials:
    """Stored authentication record."""

    base_url: str
    access_token: str


class CredentialStore:
    """Keyring-first credential store with file fallback."""

    def __init__(self, workspace_path: Path, service_name: str = "clawagent"):
        self.workspace_path = workspace_path
        self.service_name = service_name
        self.username = "default"
        self.fallback_file = workspace_path / ".claw" / "credentials.json"
        try:
            import keyring  # type: ignore
        except Exception:
            keyring = None
        self._keyring = keyring

    @property
    def supports_keyring(self) -> bool:
        return self._keyring is not None

    def save(self, creds: StoredCredentials) -> str | None:
        """Save credentials and return optional warning string."""

        value = json.dumps({"base_url": creds.base_url, "access_token": creds.access_token})
        if self._keyring is not None:
            self._keyring.set_password(self.service_name, self.username, value)
            return None
        self._write_fallback(value)
        return f"OS keyring unavailable; credentials stored at {self.fallback_file}"

    def load(self) -> StoredCredentials | None:
        """Load credentials from keyring or fallback file."""

        raw: str | None = None
        if self._keyring is not None:
            raw = self._keyring.get_password(self.service_name, self.username)
        if raw is None and self.fallback_file.exists():
            raw = self.fallback_file.read_text(encoding="utf-8")
        if not raw:
            return None
        data = json.loads(raw)
        return StoredCredentials(
            base_url=str(data["base_url"]),
            access_token=str(data["access_token"]),
        )

    def clear(self) -> None:
        """Clear saved credentials from all stores."""

        if self._keyring is not None:
            try:
                self._keyring.delete_password(self.service_name, self.username)
            except Exception:
                pass
        if self.fallback_file.exists():
            self.fallback_file.unlink()

    def _write_fallback(self, value: str) -> None:
        self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
        self.fallback_file.write_text(value, encoding="utf-8")
        try:
            os.chmod(self.fallback_file, 0o600)
        except Exception:
            # Windows ACL behavior differs; best effort only.
            pass
