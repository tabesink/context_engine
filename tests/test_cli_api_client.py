import json

from cli.api_client import ApiClient


class FakeResponse:
    status = 200

    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_api_client_records_sanitized_json_request_metadata(monkeypatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        assert timeout == 20
        return FakeResponse({"status": "ok", "access_token": "secret-token"})

    monkeypatch.setattr("cli.api_client.request.urlopen", fake_urlopen)
    client = ApiClient("http://api.example", token="client-token")

    response = client.post("/auth/login", {"username": "admin@example.com", "password": "secret"})

    assert response["status"] == "ok"
    assert client.last_request is not None
    assert client.last_request.method == "POST"
    assert client.last_request.route == "/auth/login"
    assert client.last_request.status_code == 200
    assert client.last_request.elapsed_ms >= 0
    assert client.last_request.request_summary["password"] == "redacted"
    assert client.last_request.response_summary["access_token"] == "redacted"


def test_api_client_records_multipart_metadata_without_file_bytes(monkeypatch) -> None:
    def fake_urlopen(req, timeout):  # noqa: ANN001
        body = req.data
        assert b"pdf-bytes" in body
        return FakeResponse({"document": {"id": "doc-1"}, "job_id": None})

    monkeypatch.setattr("cli.api_client.request.urlopen", fake_urlopen)
    client = ApiClient("http://api.example")

    client.post_file("/admin/documents/upload", "file", "manual.pdf", b"pdf-bytes")

    assert client.last_request is not None
    assert client.last_request.method == "POST"
    assert client.last_request.route == "/admin/documents/upload"
    assert client.last_request.request_summary == {
        "multipart": True,
        "field_name": "file",
        "filename": "manual.pdf",
        "content_size": 9,
        "fields": {},
    }
    assert "pdf-bytes" not in str(client.last_request.request_summary)
