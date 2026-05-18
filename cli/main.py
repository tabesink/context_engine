"""Legacy module kept for internal compatibility only."""

from __future__ import annotations

from cli.launcher import main as run_tui_only


def app() -> None:
    """Legacy callable that now delegates to the TUI launcher."""
    run_tui_only()
