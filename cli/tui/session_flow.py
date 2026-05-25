"""Startup session selection for the TUI."""

from __future__ import annotations

from cli.api_client import ApiClientError
from cli.tui.screen import TuiScreen
from cli.tui.screens.login import LoginScreen
from cli.tui.state import TuiState


def choose_start_screen(state: TuiState) -> TuiScreen:
    from cli.tui.screens.main_menu import MainMenuScreen

    creds = state.credential_store.load()
    if creds is None:
        state.reset_anonymous_client()
        return LoginScreen()

    state.api_base_url = creds.base_url.rstrip("/")
    state.client = state.client_factory(state.api_base_url, creds.access_token)
    try:
        user = state.auth_service().current_user()
    except ApiClientError:
        state.credential_store.clear()
        state.reset_anonymous_client()
        return LoginScreen(message="Previous session expired. Please log in again.")

    if isinstance(user, dict):
        state.username = str(user.get("username") or user.get("email", "saved session"))
        role = user.get("role")
        state.user_role = str(role).lower() if role else None
    else:
        state.username = "saved session"
        state.user_role = None
    return MainMenuScreen()
