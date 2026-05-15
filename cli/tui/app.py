"""A small Rich-only terminal UI over ragcli screen builders."""

from __future__ import annotations

from io import StringIO
from typing import Any, Callable

from rich.console import Console
from rich.live import Live
from rich.text import Text

from cli.credentials import CredentialStore
from cli.tui.keys import normalize_key, read_tui_key
from cli.tui.navigation import NavigationStack
from cli.tui.session_flow import choose_start_screen
from cli.tui.state import TuiState

InputFunc = Callable[[str], str]
ClientFactory = Callable[[str, str | None], Any]
CursorControlFunc = Callable[[bool], None]


def _render_frame(screen: Any, state: TuiState, *, width: int) -> Text:
    stream = StringIO()
    frame_console = Console(file=stream, force_terminal=False, width=width)
    screen.render(frame_console, state)
    return Text.from_ansi(stream.getvalue())


def _default_cursor_control(console: Console) -> CursorControlFunc:
    def _set_cursor_visible(visible: bool) -> None:
        # ANSI cursor visibility control for responsive TUIs.
        control = "\x1b[?25h" if visible else "\x1b[?25l"
        console.file.write(control)
        if hasattr(console.file, "flush"):
            console.file.flush()

    return _set_cursor_visible


def _clear_for_next_frame(console: Console) -> None:
    stream = console.file
    if hasattr(stream, "truncate") and hasattr(stream, "seek"):
        stream.truncate(0)
        stream.seek(0)


def run_tui(
    *,
    api_base_url: str,
    credential_store: CredentialStore,
    client_factory: ClientFactory,
    console: Console,
    input_func: InputFunc = read_tui_key,
    cursor_control: CursorControlFunc | None = None,
) -> None:
    state = TuiState(
        api_base_url=api_base_url.rstrip("/"),
        credential_store=credential_store,
        client_factory=client_factory,
    )
    navigation = NavigationStack([choose_start_screen(state)])
    cursor_visibility = cursor_control or _default_cursor_control(console)

    cursor_visibility(False)
    try:
        if not getattr(console, "is_terminal", False):
            while True:
                active_screen = navigation.current()
                _clear_for_next_frame(console)
                active_screen.render(console, state)
                try:
                    raw_key = input_func("")
                except (EOFError, KeyboardInterrupt, StopIteration):
                    return
                command = active_screen.handle_key(normalize_key(raw_key), state)
                if navigation.apply(command):
                    return
            return

        initial_screen = navigation.current()
        with Live(
            _render_frame(initial_screen, state, width=console.width),
            console=console,
            auto_refresh=False,
            refresh_per_second=30,
            transient=False,
        ) as live:
            while True:
                try:
                    raw_key = input_func("")
                except (EOFError, KeyboardInterrupt, StopIteration):
                    return
                command = navigation.current().handle_key(normalize_key(raw_key), state)
                if navigation.apply(command):
                    return
                active_screen = navigation.current()
                live.update(_render_frame(active_screen, state, width=console.width), refresh=True)
    finally:
        cursor_visibility(True)
