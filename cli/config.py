"""Configuration helpers for the TUI launcher."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CliSettings:
    api_base_url: str
    config_dir: Path
    keyring_enabled: bool


def default_config_dir() -> Path:
    return Path.home() / ".context-engine" / "cli"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="context-engine", add_help=True)
    parser.add_argument(
        "--api-base-url",
        default=None,
        help="Base URL for the context-engine backend.",
    )
    parser.add_argument(
        "--config-dir",
        default=None,
        help="Directory used for credential storage.",
    )
    parser.add_argument(
        "--keyring",
        action="store_true",
        default=None,
        help="Enable OS keyring storage.",
    )
    parser.add_argument(
        "--no-keyring",
        action="store_true",
        default=None,
        help="Disable OS keyring storage.",
    )
    return parser


def _api_base_url_from_dotenv() -> str | None:
    env_path = Path(".env")
    if not env_path.exists():
        return None

    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("API_PORT"):
                key, sep, value = stripped.partition("=")
                if sep and key.strip() == "API_PORT":
                    port = value.strip().strip("'\"")
                    if port:
                        return f"http://127.0.0.1:{port}"
    except OSError:
        return None
    return None


def load_cli_settings(argv: list[str] | None = None) -> CliSettings:
    parser = _build_parser()
    args = parser.parse_args(argv)

    env_api_base_url = (
        os.getenv("CONTEXT_ENGINE_API_BASE_URL")
        or _api_base_url_from_dotenv()
        or "http://127.0.0.1:8000"
    )
    raw_api_base_url = args.api_base_url or env_api_base_url
    api_base_url = str(raw_api_base_url).rstrip("/")

    config_dir = Path(args.config_dir) if args.config_dir else default_config_dir()
    if args.no_keyring:
        keyring_enabled = False
    elif args.keyring:
        keyring_enabled = True
    else:
        keyring_enabled = True

    return CliSettings(
        api_base_url=api_base_url,
        config_dir=config_dir,
        keyring_enabled=keyring_enabled,
    )
