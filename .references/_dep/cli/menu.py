"""Interactive selector menu for common CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import questionary
import typer
from rich.console import Console


@dataclass(frozen=True)
class MenuOption:
    """Selectable menu option bound to an action callback."""

    label: str
    action: Callable[[], None]


def _fallback_selection(labels: list[str], quit_label: str, console: Console) -> str:
    """Fallback selector when arrow-key UI is unavailable."""
    all_labels = [*labels, quit_label]
    while True:
        console.print("\n[bold]Menu options:[/bold]")
        for idx, label in enumerate(all_labels, start=1):
            console.print(f"  {idx}) {label}")
        raw_choice = typer.prompt("Select option number", default=str(len(all_labels)))
        try:
            selected_idx = int(raw_choice)
        except ValueError:
            console.print("[yellow]Please enter a valid number.[/yellow]")
            continue
        if 1 <= selected_idx <= len(all_labels):
            return all_labels[selected_idx - 1]
        console.print("[yellow]Please choose a listed option number.[/yellow]")


def run_menu_loop(
    options: list[MenuOption],
    title: str = "my-bot menu",
    quit_label: str = "Quit",
) -> None:
    """Render an arrow-key selector and run selected actions until quit."""
    if not options:
        raise ValueError("menu options cannot be empty")

    console = Console()
    labels = [option.label for option in options]
    options_by_label = {option.label: option for option in options}
    using_fallback = False

    while True:
        if using_fallback:
            selection = _fallback_selection(labels=labels, quit_label=quit_label, console=console)
        else:
            try:
                selection = questionary.select(
                    f"{title}: choose an action",
                    choices=[*labels, quit_label],
                    use_indicator=True,
                ).ask()
            except Exception:
                using_fallback = True
                console.print(
                    "[yellow]Arrow-key selector unavailable in this terminal; using numbered menu.[/yellow]"
                )
                selection = _fallback_selection(labels=labels, quit_label=quit_label, console=console)

        if selection is None or selection == quit_label:
            console.print("[cyan]Exiting menu.[/cyan]")
            return

        selected = options_by_label[selection]
        try:
            selected.action()
        except typer.Exit as exc:
            if exc.exit_code not in (None, 0):
                console.print(f"[yellow]Action exited with code {exc.exit_code}.[/yellow]")
        except Exception as exc:  # pragma: no cover - defensive guard
            console.print(f"[red]Action failed:[/red] {exc}")
