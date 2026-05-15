"""Login and session lifecycle screens."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console

from cli.api_client import ApiClientError
from cli.credentials import StoredCredentials
from cli.tui.keys import KEY_BACKSPACE, KEY_DOWN, KEY_ENTER, KEY_QUIT, KEY_TAB, KEY_UP
from cli.tui.navigation import move_selection_down, move_selection_up
from cli.tui.screen import ScreenCommand
from cli.tui.state import TuiState
from cli.tui.styles import render_breadcrumb, render_key_footer, render_status_line


@dataclass
class LoginScreen:
    message: str | None = None
    title: str = "Context Engine Login"
    email: str = ""
    password: str = ""
    active_field: str = "email"

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Session", "Login")
        if self.message:
            render_status_line(console, "warn", self.message)
        console.print(f"Backend: {state.api_base_url}")
        console.print("")
        email_marker = ">" if self.active_field == "email" else " "
        password_marker = ">" if self.active_field == "password" else " "
        console.print(f"{email_marker} Email:    [{self.email}]")
        console.print(f"{password_marker} Password: [{'*' * len(self.password)}]")
        render_key_footer(console, ["Tab/Up/Down Next field", "Enter Submit", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key in {KEY_TAB, KEY_UP, KEY_DOWN}:
            self.active_field = "password" if self.active_field == "email" else "email"
            return ScreenCommand.none()
        if key == KEY_ENTER:
            if self.active_field == "email" and self.email and not self.password:
                self.active_field = "password"
                return ScreenCommand.none()
            if not self.email or not self.password:
                self.message = "Email and password are required."
                return ScreenCommand.none()
            return self._submit(state)
        if key == KEY_BACKSPACE:
            if self.active_field == "email":
                self.email = self.email[:-1]
            else:
                self.password = self.password[:-1]
            return ScreenCommand.none()
        if self.active_field == "email":
            self.email += key
        else:
            self.password += key
        return ScreenCommand.none()

    def _submit(self, state: TuiState) -> ScreenCommand:
        from cli.tui.screens.main_menu import MainMenuScreen

        client = state.client_factory(state.api_base_url, None)
        try:
            result = client.post("/auth/login", {"email": self.email, "password": self.password})
        except ApiClientError as exc:
            return ScreenCommand.reset(LoginFailedScreen(f"{exc.code}: {exc.message}"))

        token = str(result["access_token"])
        state.credential_store.save(StoredCredentials(base_url=state.api_base_url, access_token=token))
        state.client = state.client_factory(state.api_base_url, token)
        state.user_email = self.email
        state.last_error = None
        return ScreenCommand.reset(MainMenuScreen())


@dataclass
class LoginFailedScreen:
    message: str
    title: str = "Login Failed"
    selected_index: int = 0

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Session", "Login Failed")
        render_status_line(console, "error", self.message)
        console.print("")
        for index, label in enumerate(["Retry", "Quit"]):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {label}")
        render_key_footer(console, ["Up/Down Select", "Enter Choose", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, 2)
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, 2)
            return ScreenCommand.none()
        if key == KEY_ENTER:
            if self.selected_index == 0:
                state.reset_anonymous_client()
                return ScreenCommand.reset(LoginScreen())
            return ScreenCommand.quit()
        return ScreenCommand.none()


@dataclass
class LoggedOutScreen:
    title: str = "Logged Out"
    selected_index: int = 0

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Session", "Logged Out")
        render_status_line(console, "success", "Your local CLI session has been cleared.")
        console.print("")
        for index, label in enumerate(["Login again", "Quit"]):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {label}")
        render_key_footer(console, ["Up/Down Select", "Enter Choose", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, 2)
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, 2)
            return ScreenCommand.none()
        if key == KEY_ENTER:
            if self.selected_index == 0:
                state.reset_anonymous_client()
                return ScreenCommand.reset(LoginScreen())
            return ScreenCommand.quit()
        return ScreenCommand.none()
