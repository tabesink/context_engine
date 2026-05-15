"""Navigation stack for the lightweight TUI."""

from __future__ import annotations

from dataclasses import dataclass, field

from cli.tui.screen import ScreenCommand, ScreenCommandType, TuiScreen


@dataclass
class NavigationStack:
    screens: list[TuiScreen] = field(default_factory=list)

    def push(self, screen: TuiScreen) -> None:
        self.screens.append(screen)

    def pop(self) -> None:
        if len(self.screens) > 1:
            self.screens.pop()

    def replace(self, screen: TuiScreen) -> None:
        if self.screens:
            self.screens[-1] = screen
        else:
            self.screens.append(screen)

    def reset(self, screen: TuiScreen) -> None:
        self.screens = [screen]

    def current(self) -> TuiScreen:
        return self.screens[-1]

    def apply(self, command: ScreenCommand) -> bool:
        if command.type == ScreenCommandType.NONE:
            return False
        if command.type == ScreenCommandType.QUIT:
            return True
        if command.type == ScreenCommandType.POP:
            self.pop()
        elif command.type == ScreenCommandType.PUSH and command.screen is not None:
            self.push(command.screen)
        elif command.type == ScreenCommandType.REPLACE and command.screen is not None:
            self.replace(command.screen)
        elif command.type == ScreenCommandType.RESET and command.screen is not None:
            self.reset(command.screen)
        return False


def move_selection_up(index: int, item_count: int) -> int:
    if item_count <= 0:
        return 0
    return (index - 1) % item_count


def move_selection_down(index: int, item_count: int) -> int:
    if item_count <= 0:
        return 0
    return (index + 1) % item_count
