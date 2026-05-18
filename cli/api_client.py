"""Small HTTP client used by the terminal app."""

from __future__ import annotations

import json
import time
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


@dataclass(frozen=True)
class ApiRequestMetadata:
    method: str
    route: str
    status_code: int
    elapsed_ms: int
    request_summary: Any
    response_summary: Any


class ApiClient:
    """Minimal JSON and multipart client for the FastAPI backend."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.last_request: ApiRequestMetadata | None = None

    def get(self, path: str) -> Any:
        return self._request_json("GET", path, None)

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        return self._request_json("POST", path, payload or {})

    def delete(self, path: str) -> Any:
        return self._request_json("DELETE", path, None)

    def post_file(
        self,
        path: str,
        field_name: str,
        filename: str,
        content: bytes,
        fields: dict[str, str] | None = None,
    ) -> Any:
        boundary = f"----context-engine-{uuid.uuid4().hex}"
        parts: list[bytes] = []
        for key, value in (fields or {}).items():
            parts.append(
                (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                    f"{value}\r\n"
                ).encode("utf-8")
            )
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                "Content-Type: application/octet-stream\r\n\r\n"
            ).encode("utf-8")
        )
        ending = f"\r\n--{boundary}--\r\n".encode("utf-8")
        body = b"".join(parts) + content + ending
        return self._request_raw(
            "POST",
            path,
            body=body,
            headers={
                "Accept": "application/json",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            request_summary={
                "multipart": True,
                "field_name": field_name,
                "filename": filename,
                "content_size": len(content),
                "fields": fields or {},
            },
        )

    def _request_json(self, method: str, path: str, payload: dict[str, Any] | None) -> Any:
        body: bytes | None = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        return self._request_raw(method, path, body=body, headers=headers, request_summary=payload)

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None,
        headers: dict[str, str],
        request_summary: Any = None,
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
        started = time.perf_counter()
        try:
            with request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
                decoded = json.loads(raw) if raw else {}
                self._record_request(
                    method=method,
                    path=path,
                    status_code=int(getattr(resp, "status", 200)),
                    started=started,
                    request_summary=request_summary,
                    response_summary=decoded,
                )
                return decoded
        except error.HTTPError as exc:
            api_error = self._api_error_from_http(exc)
            self._record_request(
                method=method,
                path=path,
                status_code=exc.code,
                started=started,
                request_summary=request_summary,
                response_summary={"code": api_error.code, "message": api_error.message},
            )
            raise api_error from exc
        except error.URLError as exc:
            reason = str(exc.reason)
            message = f"cannot reach backend at {self.base_url} ({reason})"
            self._record_request(
                method=method,
                path=path,
                status_code=0,
                started=started,
                request_summary=request_summary,
                response_summary={"code": "connection_failed", "message": message},
            )
            raise ApiClientError(
                code="connection_failed",
                message=message,
                status_code=0,
            ) from exc

    def _record_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        started: float,
        request_summary: Any,
        response_summary: Any,
    ) -> None:
        self.last_request = ApiRequestMetadata(
            method=method,
            route=path,
            status_code=status_code,
            elapsed_ms=max(0, round((time.perf_counter() - started) * 1000)),
            request_summary=_sanitize_for_display(request_summary),
            response_summary=_sanitize_for_display(response_summary),
        )

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


SENSITIVE_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "password",
    "secret",
    "token",
}


def _sanitize_for_display(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in SENSITIVE_KEYS or any(part in normalized for part in ("token", "password", "api_key", "authorization")):
                cleaned[str(key)] = "redacted"
            else:
                cleaned[str(key)] = _sanitize_for_display(item)
        return cleaned
    if isinstance(value, list):
        return [_sanitize_for_display(item) for item in value]
    if isinstance(value, bytes):
        return f"<{len(value)} bytes>"
    if isinstance(value, str) and len(value) > 500:
        return f"{value[:500]}...<truncated>"
    return value

