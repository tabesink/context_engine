"""Small screen/result models for command and TUI renderers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScreenAction:
    label: str
    command: str
    disabled: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class ScreenSection:
    title: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    text: str | None = None
    columns: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScreenResult:
    title: str
    api_group: str
    summary: dict[str, Any] = field(default_factory=dict)
    sections: list[ScreenSection] = field(default_factory=list)
    actions: list[ScreenAction] = field(default_factory=list)
    raw: Any = None
