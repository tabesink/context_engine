"""Small HTTP client used by ragcli."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class ApiClientError(Exception):
    """Typed API error surfaced to CLI commands."""

    code: str
    message: str
    status_code: int


class ApiClient:
    """Minimal JSON and multipart client for the FastAPI backend."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def get(self, path: str) -> Any:
        return self._request_json("GET", path, None)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self._request_json("POST", path, payload or {})

    def delete(self, path: str) -> Any:
        return self._request_json("DELETE", path, None)

    def post_file(self, path: str, field_name: str, filename: str, content: bytes) -> Any:
        boundary = f"----ragcli-{uuid.uuid4().hex}"
        prelude = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
        ending = f"\r\n--{boundary}--\r\n".encode("utf-8")
        return self._request_raw(
            "POST",
            path,
            body=prelude + content + ending,
            headers={
                "Accept": "application/json",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None) -> Any:
        body: bytes | None = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        return self._request_raw(method, path, body=body, headers=headers)

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None,
        headers: dict[str, str],
    ) -> Any:
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
            raise self._api_error_from_http(exc) from exc
        except error.URLError as exc:
            reason = str(exc.reason)
            raise ApiClientError(
                code="connection_failed",
                message=f"cannot reach backend at {self.base_url} ({reason})",
                status_code=0,
            ) from exc

    def _api_error_from_http(self, exc: error.HTTPError) -> ApiClientError:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        code = "request_failed"
        message = f"http {exc.code}"
        if raw:
            try:
                decoded = json.loads(raw)
            except json.JSONDecodeError:
                message = raw
            else:
                if isinstance(decoded, dict) and isinstance(decoded.get("error"), dict):
                    payload = decoded["error"]
                    code = str(payload.get("code", code))
                    message = str(payload.get("message", message))
                elif isinstance(decoded, dict) and decoded.get("detail"):
                    detail = decoded["detail"]
                    message = detail if isinstance(detail, str) else json.dumps(detail)
        return ApiClientError(code=code, message=message, status_code=exc.code)

