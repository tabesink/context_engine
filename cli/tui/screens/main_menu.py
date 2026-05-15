"""Authenticated main menu screen."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from rich.console import Console

from cli.tui.keys import KEY_BACK, KEY_DOWN, KEY_ENTER, KEY_QUIT, KEY_UP
from cli.tui.navigation import move_selection_down, move_selection_up
from cli.tui.screen import ScreenCommand, TuiScreen
from cli.tui.screens.content import (
    BackendGapsScreen,
    DocumentsScreen,
    ObservabilityScreen,
    RetrievalPromptScreen,
    admin_documents_screen,
    jobs_screen,
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
    state.user_email = None
    state.reset_anonymous_client()
    return ScreenCommand.reset(LoggedOutScreen())


def _quit(state: TuiState) -> ScreenCommand:
    return ScreenCommand.quit()


MENU_ITEMS = [
    MenuItem("Documents", _push(DocumentsScreen)),
    MenuItem("Retrieval", _push(RetrievalPromptScreen)),
    MenuItem("LightRAG Graphs", lambda state: ScreenCommand.push(lightrag_screen())),
    MenuItem("Admin Documents", lambda state: ScreenCommand.push(admin_documents_screen())),
    MenuItem("Jobs", lambda state: ScreenCommand.push(jobs_screen())),
    MenuItem("Observability", _push(ObservabilityScreen)),
    MenuItem("Backend Gaps", _push(BackendGapsScreen)),
    MenuItem("Logout", _logout),
    MenuItem("Quit", _quit),
]


@dataclass
class MainMenuScreen:
    title: str = "Context Engine"
    selected_index: int = 0

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Context Engine")
        console.print(f"Backend: {state.api_base_url}")
        console.print(f"Session: {state.user_email or 'saved'}")
        console.print("")
        for index, item in enumerate(MENU_ITEMS):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {item.label}")
        render_key_footer(console, ["Up/Down Move", "Enter Select", "B Stay", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.none()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, len(MENU_ITEMS))
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, len(MENU_ITEMS))
            return ScreenCommand.none()
        if key == KEY_ENTER:
            return MENU_ITEMS[self.selected_index].action(state)
        legacy_shortcuts = {
            "1": 0,
            "2": 0,
            "3": 1,
            "4": 2,
            "5": 3,
            "6": 4,
            "7": 5,
            "8": 6,
        }
        if key in legacy_shortcuts:
            self.selected_index = legacy_shortcuts[key]
            return MENU_ITEMS[self.selected_index].action(state)
        return ScreenCommand.none()
