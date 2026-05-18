"""TUI-only launcher for the context-engine CLI."""

from __future__ import annotations

import sys

from rich.console import Console

from cli.api_client import ApiClient
from cli.config import load_cli_settings
from cli.credentials import CredentialStore
from cli.tui.app import run_tui


def main() -> None:
    settings = load_cli_settings(sys.argv[1:])
    credential_store = CredentialStore(
        config_dir=settings.config_dir,
        keyring_enabled=settings.keyring_enabled,
    )
    console = Console(width=120)

    try:
        run_tui(
            api_base_url=settings.api_base_url,
            credential_store=credential_store,
            client_factory=ApiClient,
            console=console,
        )
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
