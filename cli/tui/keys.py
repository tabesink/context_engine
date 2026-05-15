"""Key handling for the lightweight TUI."""

from __future__ import annotations

import os
import sys

KEY_UP = "up"
KEY_DOWN = "down"
KEY_ENTER = "enter"
KEY_TAB = "tab"
KEY_BACK = "back"
KEY_QUIT = "quit"
KEY_BACKSPACE = "backspace"
KEY_REFRESH = "refresh"
KEY_UPLOAD = "upload"


def read_tui_key(_prompt: str = "") -> str:
    """Read one keypress from a real terminal without waiting for Enter."""
    if os.name == "nt":
        return _read_windows_key()
    return _read_posix_key()


def normalize_key(raw: str) -> str:
    if raw in {KEY_UP, KEY_DOWN, KEY_ENTER, KEY_TAB, KEY_BACK, KEY_QUIT, KEY_BACKSPACE, KEY_REFRESH, KEY_UPLOAD}:
        return raw
    if raw in {"\x00H", "\xe0H"}:
        return KEY_UP
    if raw in {"\x00P", "\xe0P"}:
        return KEY_DOWN
    # Keep literal character input (especially spaces) intact for text fields.
    lowered = raw.strip().lower()
    if lowered in {"q", "quit"}:
        return KEY_QUIT
    if lowered == "upload":
        return KEY_UPLOAD
    if lowered == "refresh" or raw == "\x12":
        return KEY_REFRESH
    if lowered in {"b", "back", "\x1b"}:
        return KEY_BACK
    if lowered in {"up", "arrowup"} or raw == "\x1b[A":
        return KEY_UP
    if lowered in {"down", "arrowdown"} or raw == "\x1b[B":
        return KEY_DOWN
    if lowered == "tab" or raw == "\t":
        return KEY_TAB
    if lowered in {"enter", "return"} or raw in {"\r", "\n", ""}:
        return KEY_ENTER
    if lowered == "backspace" or raw in {"\x08", "\x7f"}:
        return KEY_BACKSPACE
    return raw


def _read_windows_key() -> str:
    import msvcrt

    char = msvcrt.getwch()
    if char in {"\x00", "\xe0"}:
        code = msvcrt.getwch()
        if code == "H":
            return KEY_UP
        if code == "P":
            return KEY_DOWN
        return ""
    if char == "\r":
        return KEY_ENTER
    if char == "\t":
        return KEY_TAB
    if char in {"\x08", "\x7f"}:
        return KEY_BACKSPACE
    return char


def _read_posix_key() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        char = sys.stdin.read(1)
        if char == "\x1b":
            sequence = char + sys.stdin.read(2)
            if sequence == "\x1b[A":
                return KEY_UP
            if sequence == "\x1b[B":
                return KEY_DOWN
            return KEY_BACK
        if char in {"\r", "\n"}:
            return KEY_ENTER
        if char == "\t":
            return KEY_TAB
        if char in {"\x08", "\x7f"}:
            return KEY_BACKSPACE
        return char
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
