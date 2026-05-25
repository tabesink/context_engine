"""Authentication and session route wrappers."""

from __future__ import annotations

from typing import Any

from cli.api_client import ApiClient


class AuthService:
    def __init__(self, client: ApiClient):
        self._client = client

    def login(self, username: str, password: str) -> dict[str, Any]:
        return self._client.post("/auth/login", {"username": username, "password": password})

    def current_user(self) -> dict[str, Any]:
        payload = self._client.get("/auth/me")
        return payload if isinstance(payload, dict) else {"username": "unknown"}
