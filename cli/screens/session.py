"""Session screen builders."""

from __future__ import annotations

from typing import Any

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


def build_login_screen(*, username: str, base_url: str) -> ScreenResult:
    return ScreenResult(
        title="Login",
        api_group="auth",
        summary={"backend": base_url, "username": username, "status": "success"},
        sections=[
            ScreenSection(
                title="Saved session",
                rows=[
                    {"field": "API base URL", "value": base_url},
                    {"field": "Token stored", "value": "yes"},
                    {"field": "Password saved", "value": "no"},
                ],
                columns=["field", "value"],
            )
        ],
        actions=[
            ScreenAction("Current session", "context-engine auth me"),
            ScreenAction("Documents", "context-engine documents list"),
        ],
        raw={"username": username, "base_url": base_url},
    )


def build_logout_screen() -> ScreenResult:
    return ScreenResult(
        title="Logout",
        api_group="auth",
        summary={"status": "local session cleared"},
        sections=[
            ScreenSection(
                title="Cleared",
                rows=[
                    {"item": "API base URL", "state": "yes"},
                    {"item": "Access token", "state": "yes"},
                    {"item": "Password", "state": "n/a"},
                ],
                columns=["item", "state"],
            )
        ],
        actions=[ScreenAction("Login", "context-engine login --username admin")],
    )


def build_session_screen(user: dict[str, Any] | None, *, base_url: str) -> ScreenResult:
    summary = {"backend": base_url}
    if user:
        summary["username"] = user.get("username") or user.get("email", "")
        summary["role"] = user.get("role", "")
    else:
        summary["session"] = "not logged in"
    return ScreenResult(
        title="Current Session",
        api_group="auth",
        summary={"backend": base_url},
        sections=[
            ScreenSection(
                title="User",
                rows=[
                    {"field": "Username", "value": summary.get("username", "")},
                    {"field": "Role", "value": summary.get("role", "")},
                    {"field": "Authenticated", "value": bool(user)},
                ],
                columns=["field", "value"],
            )
        ],
        actions=[
            ScreenAction("Documents", "context-engine documents list"),
            ScreenAction("Admin documents", "context-engine admin documents list"),
        ],
        raw=user,
    )
