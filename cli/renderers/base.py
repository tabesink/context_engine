"""Generic human renderer for screen results."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from cli.renderers.tables import render_ascii_table
from cli.screens.models import ScreenResult


SECRET_KEYS = {"access_token", "authorization", "bearer", "password", "token"}


def is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(secret in normalized for secret in SECRET_KEYS)


def safe_value(key: str, value: Any) -> str:
    if is_secret_key(key):
        return "redacted"
    if value is None or value == "":
        return "--"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) if value else "none"
    return str(value)


def render_screen_result(screen: ScreenResult, *, console: Console, show_title: bool = True) -> None:
    if show_title:
        console.print(screen.title.upper())
    if screen.summary:
        console.print("")
        for key, value in screen.summary.items():
            render_key_value(_humanize_label(key), safe_value(key, value), console=console)

    for section in screen.sections:
        console.print("")
        if section.rows:
            columns = section.columns or list(section.rows[0].keys())
            render_ascii_table(section.title, section.rows, columns, console=console)
        else:
            suffix = ":" if section.text else ""
            console.print(f"{section.title}{suffix}")
        if section.text:
            render_text_block(section.text, console=console)

    if screen.actions:
        console.print("")
        console.print("Next:")
        for action in screen.actions:
            if action.disabled:
                reason = f" ({action.reason})" if action.reason else ""
                console.print(f"  {action.command}: disabled{reason}")
            else:
                console.print(f"  {action.command}")


def render_key_value(label: str, value: Any, *, console: Console) -> None:
    console.print(f"{label}:")
    render_text_block(str(value), console=console)


def render_text_block(text: str, *, console: Console) -> None:
    for line in str(text).splitlines() or [""]:
        console.print(f"  {line}")


def _humanize_label(key: str) -> str:
    overrides = {
        "base_url": "Backend",
        "backend": "Backend",
        "document_id": "Document ID",
        "job_id": "Job ID",
        "created_at": "Created",
        "updated_at": "Updated",
        "page_number": "Page",
        "selected_engine": "Selected engine",
        "top_k": "Top K",
    }
    if key in overrides:
        return overrides[key]
    return key.replace("_", " ").capitalize()
