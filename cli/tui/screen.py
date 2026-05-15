"""Small command model shared by TUI screens."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Protocol

from rich.console import Console

if TYPE_CHECKING:
    from cli.tui.state import TuiState


class ScreenCommandType(str, Enum):
    NONE = "none"
    PUSH = "push"
    POP = "pop"
    REPLACE = "replace"
    RESET = "reset"
    QUIT = "quit"


@dataclass(frozen=True)
class ScreenCommand:
    type: ScreenCommandType
    screen: TuiScreen | None = None

    @classmethod
    def none(cls) -> ScreenCommand:
        return cls(ScreenCommandType.NONE)

    @classmethod
    def push(cls, screen: TuiScreen) -> ScreenCommand:
        return cls(ScreenCommandType.PUSH, screen)

    @classmethod
    def pop(cls) -> ScreenCommand:
        return cls(ScreenCommandType.POP)

    @classmethod
    def replace(cls, screen: TuiScreen) -> ScreenCommand:
        return cls(ScreenCommandType.REPLACE, screen)

    @classmethod
    def reset(cls, screen: TuiScreen) -> ScreenCommand:
        return cls(ScreenCommandType.RESET, screen)

    @classmethod
    def quit(cls) -> ScreenCommand:
        return cls(ScreenCommandType.QUIT)


class TuiScreen(Protocol):
    title: str

    def render(self, console: Console, state: TuiState) -> None:
        ...

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        ...
