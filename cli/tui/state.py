"""Runtime state shared by TUI screens."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from cli.credentials import CredentialStore

ClientFactory = Callable[[str, str | None], Any]


@dataclass
class TuiState:
    api_base_url: str
    credential_store: CredentialStore
    client_factory: ClientFactory
    client: Any | None = None
    user_email: str | None = None
    last_error: str | None = None

    def reset_anonymous_client(self) -> None:
        self.client = self.client_factory(self.api_base_url, None)
