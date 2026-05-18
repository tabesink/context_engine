"""Shared visual helpers and semantic style names for the TUI."""

from __future__ import annotations

from typing import Iterable

from rich.console import Console

SESSION = "blue"
DOCUMENTS = "cyan"
RETRIEVAL = "green"
LIGHTRAG = "magenta"
ADMIN = "yellow"
JOBS = "yellow"
OBSERVABILITY = "blue"
GAPS = "dim"
ERROR = "red"
WARNING = "yellow"
SUCCESS = "green"


def breadcrumb(*segments: str) -> str:
    """Build a strict-global breadcrumb label."""
    return " / ".join(part.strip().upper() for part in segments if part.strip())


def render_breadcrumb(console: Console, *segments: str) -> None:
    console.print(breadcrumb(*segments))
    console.print("")


def status_label(level: str) -> str:
    normalized = level.strip().lower()
    if normalized in {"ok", "success"}:
        return "[SUCCESS]"
    if normalized in {"warn", "warning"}:
        return "[WARN]"
    return "[ERROR]"


def render_status_line(console: Console, level: str, message: str) -> None:
    console.print(f"{status_label(level)} {message}")


def render_key_footer(console: Console, items: Iterable[str]) -> None:
    entries = [item.strip() for item in items if item and item.strip()]
    if not entries:
        return
    console.print("")
    console.print(" | ".join(entries))


def api_footer_items(*, include_debug: bool = False) -> list[str]:
    items = ["I Inspect API", "J Raw JSON", "F Toggle full IDs", "R Refresh"]
    if include_debug:
        items.append("D Debug details")
    items.extend(["B Back", "Q Quit"])
    return items


def render_api_footer(
    console: Console,
    *,
    method: str | None = None,
    route: str | None = None,
    status_code: int | None = None,
    elapsed_ms: int | None = None,
    include_debug: bool = False,
) -> None:
    if method and route:
        status = str(status_code) if status_code is not None else "unknown"
        time = f"{elapsed_ms} ms" if elapsed_ms is not None else "unknown"
        console.print("")
        console.print(f"Route: {method} {route}    Status: {status}    Time: {time}")
    render_key_footer(console, api_footer_items(include_debug=include_debug))


def truncate_id(value: str, *, prefix: int = 8, suffix: int = 12) -> str:
    text = str(value or "")
    if len(text) <= prefix + suffix + 3:
        return text
    return f"{text[:prefix]}...{text[-suffix:]}"
