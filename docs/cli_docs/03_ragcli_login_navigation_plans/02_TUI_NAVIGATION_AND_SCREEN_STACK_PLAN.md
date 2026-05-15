# TUI Navigation and Screen Stack Plan

## Goal

Users must be able to navigate the TUI with arrows, select options with Enter, move between screens, and return with Back. The terminal must not accumulate previous screen output.

## User controls

| Key | Behavior |
| --- | --- |
| Up arrow | Move selection up |
| Down arrow | Move selection down |
| Enter | Select highlighted option |
| B | Go back one screen |
| Esc | Optional: go back one screen |
| Q | Quit from any screen |
| Ctrl+C | Exit cleanly |

## Required behavior

- Starting `ragcli ui` shows login or main menu depending on session state.
- Arrow keys move the selected item.
- Enter opens the selected screen/action.
- The selected screen replaces the previous screen.
- Back returns to the previous screen.
- Quit exits from any screen.
- Nested screens use a stack.
- Loading, error, and backend-gap states replace the current screen; they do not append output.

## Navigation stack

Create a very small navigation stack.

```python
from dataclasses import dataclass, field

@dataclass
class NavigationStack:
    screens: list["TuiScreen"] = field(default_factory=list)

    def push(self, screen: "TuiScreen") -> None:
        self.screens.append(screen)

    def pop(self) -> None:
        if len(self.screens) > 1:
            self.screens.pop()

    def replace(self, screen: "TuiScreen") -> None:
        if self.screens:
            self.screens[-1] = screen
        else:
            self.screens.append(screen)

    def reset(self, screen: "TuiScreen") -> None:
        self.screens = [screen]

    def current(self) -> "TuiScreen":
        return self.screens[-1]
```

## Screen command model

Keep this simple.

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ScreenCommandType(str, Enum):
    NONE = "none"
    PUSH = "push"
    POP = "pop"
    REPLACE = "replace"
    RESET = "reset"
    QUIT = "quit"
    REFRESH = "refresh"

@dataclass
class ScreenCommand:
    type: ScreenCommandType
    screen: Optional["TuiScreen"] = None
```

## TUI screen protocol

```python
from typing import Protocol, Any

class TuiScreen(Protocol):
    title: str

    def render(self, state: "TuiState") -> Any:
        ...

    def handle_key(self, key: str, state: "TuiState") -> ScreenCommand:
        ...
```

## TUI state

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class TuiState:
    api_base_url: str
    user_email: Optional[str] = None
    should_quit: bool = False
    last_error: Optional[str] = None
```

## Selection helper

Keep selection movement testable and boring.

```python
def move_selection_up(index: int, item_count: int) -> int:
    if item_count <= 0:
        return 0
    return (index - 1) % item_count

def move_selection_down(index: int, item_count: int) -> int:
    if item_count <= 0:
        return 0
    return (index + 1) % item_count
```

## Screen replacement rule

The TUI loop must call `console.clear()` before every render.

Do not render screens using normal `print()`.

Do not let screen content accumulate in the terminal.

## Main menu screen

Main menu options:

```text
Documents
Retrieval
LightRAG Graphs
Admin Documents
Jobs
Observability
Backend Gaps
Logout
Quit
```

Behavior:

- Up/down changes highlighted row.
- Enter on an option pushes or replaces with the selected screen.
- Enter on Logout clears session and resets to login/logged-out screen.
- Enter on Quit exits.
- Q exits.

## Back behavior

- From any child screen, `B` pops back one screen.
- From root main menu, `B` does nothing or shows a quit confirmation.
- From login screen, `B` does nothing.
- From logged-out screen, `B` returns to login or does nothing.

## Acceptance criteria

- User can navigate main menu options with arrow keys.
- User can open selected screen with Enter.
- User can go back with B.
- Terminal content is replaced, not appended.
- Quit works from every screen.
- Screen stack behavior is covered by behavior tests.
