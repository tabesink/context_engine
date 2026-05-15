"""ASCII table rendering helpers."""

from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Console
from rich.table import Table

from cli.tui.styles import truncate_id


def render_ascii_table(
    title: str,
    rows: list[dict[str, Any]],
    columns: list[str],
    *,
    console: Console,
) -> None:
    """Render a portable ASCII table for terminals and tests."""
    if title:
        console.print(f"{title}:")
    table = Table(box=box.ASCII)
    for column in columns:
        table.add_column(_humanize_column(column))
    if rows:
        for row in rows:
            table.add_row(*(display_table_value(column, row.get(column, "")) for column in columns))
    else:
        table.add_row(*("No data" if index == 0 else "" for index, _ in enumerate(columns)))
    console.print(table)


def _humanize_column(column: str) -> str:
    overrides = {
        "id": "ID",
        "document_id": "Document ID",
        "job_id": "Job ID",
        "created_at": "Created",
        "updated_at": "Updated",
        "latency_ms": "Latency ms",
        "top_k": "Top K",
    }
    if column in overrides:
        return overrides[column]
    return column.replace("_", " ").title()


def _display_value(value: Any) -> str:
    if value is None or value == "":
        return "--"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value) if value else "none"
    return str(value)


def display_table_value(column: str, value: Any) -> str:
    """Display-safe value for tables with ID truncation policy."""
    rendered = _display_value(value)
    if "id" in column:
        return truncate_id(rendered)
    return rendered
