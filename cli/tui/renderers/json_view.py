"""Raw JSON rendering with CLI-safe redaction."""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console

SENSITIVE_KEY_PARTS = ("authorization", "api_key", "password", "secret", "token")
LONG_TEXT_LIMIT = 500


def safe_json(value: Any, *, full_ids: bool = True) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SENSITIVE_KEY_PARTS):
                cleaned[str(key)] = "redacted"
            elif not full_ids and normalized.endswith("id"):
                cleaned[str(key)] = _truncate_id(str(item))
            else:
                cleaned[str(key)] = safe_json(item, full_ids=full_ids)
        return cleaned
    if isinstance(value, list):
        return [safe_json(item, full_ids=full_ids) for item in value]
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>"
    if isinstance(value, str) and len(value) > LONG_TEXT_LIMIT:
        return f"{value[:LONG_TEXT_LIMIT]}...<truncated>"
    return value


def render_json_view(console: Console, value: Any, *, full_ids: bool = True) -> None:
    console.print(json.dumps(safe_json(value, full_ids=full_ids), indent=2, sort_keys=True))


def _truncate_id(value: str) -> str:
    if len(value) <= 23:
        return value
    return f"{value[:8]}...{value[-12:]}"
