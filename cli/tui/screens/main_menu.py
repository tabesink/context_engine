"""Authenticated main menu screen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rich.console import Console

from cli.tui.keys import KEY_BACK, KEY_DOWN, KEY_ENTER, KEY_QUIT, KEY_UP
from cli.tui.navigation import move_selection_down, move_selection_up
from cli.tui.screen import ScreenCommand, TuiScreen
from cli.tui.screens.content import (
    DocumentsScreen,
    HealthScreen,
    ObservabilityScreen,
    RetrievalPromptScreen,
    jobs_screen,
    lightrag_domains_screen,
    lightrag_screen,
)
from cli.tui.screens.login import LoggedOutScreen
from cli.tui.state import TuiState
from cli.tui.styles import render_breadcrumb, render_key_footer


@dataclass(frozen=True)
class MenuItem:
    label: str
    action: Callable[[TuiState], ScreenCommand]


def _push(screen_factory: Callable[[], TuiScreen]) -> Callable[[TuiState], ScreenCommand]:
    def _action(state: TuiState) -> ScreenCommand:
        return ScreenCommand.push(screen_factory())

    return _action


def _logout(state: TuiState) -> ScreenCommand:
    state.credential_store.clear()
    state.username = None
    state.user_role = None
    state.reset_anonymous_client()
    return ScreenCommand.reset(LoggedOutScreen())


def _quit(state: TuiState) -> ScreenCommand:
    return ScreenCommand.quit()


BASE_MENU_ITEMS = [
    MenuItem("Documents", _push(DocumentsScreen)),
    MenuItem("Retrieval", _push(RetrievalPromptScreen)),
    MenuItem("Graphs", lambda state: ScreenCommand.push(lightrag_screen())),
]

ADMIN_MENU_ITEMS = [
    MenuItem("LightRAG Domains", lambda state: ScreenCommand.push(lightrag_domains_screen())),
    MenuItem("Jobs", lambda state: ScreenCommand.push(jobs_screen())),
    MenuItem("Observability", _push(ObservabilityScreen)),
]

TAIL_MENU_ITEMS = [
    MenuItem("Health / Readiness", _push(HealthScreen)),
    MenuItem("Logout", _logout),
    MenuItem("Quit", _quit),
]


def _menu_items_for_state(state: TuiState) -> list[MenuItem]:
    items = list(BASE_MENU_ITEMS)
    if (state.user_role or "").lower() == "admin":
        items.extend(ADMIN_MENU_ITEMS)
    items.extend(TAIL_MENU_ITEMS)
    return items


@dataclass
class MainMenuScreen:
    title: str = "Context Engine"
    selected_index: int = 0

    def render(self, console: Console, state: TuiState) -> None:
        menu_items = _menu_items_for_state(state)
        if self.selected_index >= len(menu_items):
            self.selected_index = max(0, len(menu_items) - 1)
        render_breadcrumb(console, "Context Engine")
        console.print(f"Backend: {state.api_base_url}")
        console.print(f"Session: {state.username or 'saved'}")
        console.print("")
        for index, item in enumerate(menu_items):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {item.label}")
        render_key_footer(console, ["Up/Down Move", "Enter Select", "B Stay", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        menu_items = _menu_items_for_state(state)
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.none()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, len(menu_items))
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, len(menu_items))
            return ScreenCommand.none()
        if key == KEY_ENTER:
            return menu_items[self.selected_index].action(state)
        legacy_shortcuts = {"1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6, "8": 7, "9": 8}
        if key in legacy_shortcuts:
            self.selected_index = legacy_shortcuts[key]
            if self.selected_index < len(menu_items):
                return menu_items[self.selected_index].action(state)
            return ScreenCommand.none()
        return ScreenCommand.none()
