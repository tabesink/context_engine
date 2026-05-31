"""Minimal backend API client for CLI."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Generator
from urllib import error, request


@dataclass
class ApiClientError(Exception):
    """Typed API error surfaced to CLI."""

    code: str
    message: str
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


class ApiClient:
    """Small JSON REST client."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def with_token(self, token: str | None) -> "ApiClient":
        return ApiClient(base_url=self.base_url, token=token)

    def get(self, path: str) -> dict[str, Any]:
        return self._request_json("GET", path, None)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request_json("POST", path, payload or {})

    def post_file(self, path: str, field_name: str, filename: str, content: bytes) -> dict[str, Any]:
        boundary = f"----clawagent-{uuid.uuid4().hex}"
        prelude = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
        ending = f"\r\n--{boundary}--\r\n".encode("utf-8")
        body = prelude + content + ending
        headers = {
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        return self._request_raw("POST", path, body=body, headers=headers)

    def stream(self, path: str) -> Generator[dict[str, Any], None, None]:
        request_headers: dict[str, str] = {"Accept": "text/event-stream"}
        if self.token:
            request_headers["Authorization"] = f"Bearer {self.token}"
        req = request.Request(
            url=f"{self.base_url}{path}",
            headers=request_headers,
            method="GET",
        )
        try:
            with request.urlopen(req, timeout=60) as resp:
                current_event = "message"
                current_data_lines: list[str] = []
                while True:
                    raw_line = resp.readline()
                    if raw_line == b"":
                        break
                    line = raw_line.decode("utf-8").rstrip("\r\n")
                    if not line:
                        if current_data_lines:
                            data_raw = "\n".join(current_data_lines)
                            payload: dict[str, Any]
                            try:
                                decoded = json.loads(data_raw)
                                payload = decoded if isinstance(decoded, dict) else {"value": decoded}
                            except json.JSONDecodeError:
                                payload = {"raw": data_raw}
                            payload.setdefault("event", current_event)
                            yield payload
                        current_event = "message"
                        current_data_lines = []
                        continue
                    if line.startswith(":"):
                        continue
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip() or "message"
                    elif line.startswith("data:"):
                        current_data_lines.append(line.split(":", 1)[1].lstrip())
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp else ""
            code = "request_failed"
            message = f"http {exc.code}"
            if raw:
                try:
                    decoded = json.loads(raw)
                    if isinstance(decoded, dict) and isinstance(decoded.get("error"), dict):
                        err = decoded["error"]
                        code = str(err.get("code", code))
                        message = str(err.get("message", message))
                except json.JSONDecodeError:
                    message = raw
            raise ApiClientError(code=code, message=message, status_code=exc.code) from exc
        except error.URLError as exc:
            reason = str(exc.reason)
            message = f"cannot reach backend at {self.base_url} ({reason})"
            raise ApiClientError(code="connection_failed", message=message, status_code=0) from exc

    def _request_json(
        self, method: str, path: str, payload: dict[str, Any] | None
    ) -> dict[str, Any]:
        body: bytes | None = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        return self._request_raw(method, path, body=body, headers=headers)

    def _request_raw(
        self, method: str, path: str, body: bytes | None, headers: dict[str, str]
    ) -> dict[str, Any]:
        request_headers = dict(headers)
        if self.token:
            request_headers["Authorization"] = f"Bearer {self.token}"
        req = request.Request(
            url=f"{self.base_url}{path}",
            data=body,
            headers=request_headers,
            method=method,
        )
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp else ""
            code = "request_failed"
            message = f"http {exc.code}"
            if raw:
                try:
                    decoded = json.loads(raw)
                    if isinstance(decoded, dict) and isinstance(decoded.get("error"), dict):
                        err = decoded["error"]
                        code = str(err.get("code", code))
                        message = str(err.get("message", message))
                except json.JSONDecodeError:
                    message = raw
            raise ApiClientError(code=code, message=message, status_code=exc.code) from exc
        except error.URLError as exc:
            reason = str(exc.reason)
            message = f"cannot reach backend at {self.base_url} ({reason})"
            raise ApiClientError(code="connection_failed", message=message, status_code=0) from exc
