import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from cli.main import app


runner = CliRunner()


class FakeApiClient:
    calls: list[tuple[str, str, Any, str | None]] = []

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url
        self.token = token

    @classmethod
    def reset(cls) -> None:
        cls.calls = []

    def get(self, path: str) -> Any:
        self.calls.append(("GET", path, None, self.token))
        if path == "/auth/me":
            return {"email": "admin@example.com", "role": "admin"}
        if path == "/documents":
            return [{"id": "doc-1", "filename": "manual.txt", "status": "ready"}]
        if path == "/documents/doc-1":
            return {"id": "doc-1", "filename": "manual.txt", "status": "ready"}
        if path == "/documents/doc-1/structure":
            return {"document_id": "doc-1", "tree": {"title": "Manual"}}
        if path == "/documents/doc-1/pages/1":
            return {"document_id": "doc-1", "page_number": 1, "text": "hello"}
        if path == "/admin/documents":
            return [{"id": "doc-1", "filename": "manual.txt", "status": "ready"}]
        if path == "/admin/audit-logs":
            return [{"id": "audit-1", "event": "document.uploaded", "target_id": "doc-1"}]
        if path == "/admin/query-logs":
            return [{"id": "query-1", "query": "install steps", "mode": "auto", "latency_ms": 12}]
        if path == "/jobs":
            return [{"id": "job-1", "kind": "index_document", "status": "queued"}]
        if path == "/jobs/job-1":
            return {"id": "job-1", "kind": "index_document", "status": "queued"}
        if path == "/graph/label/list":
            return ["manual", "installation"]
        if path == "/graphs?label=manual&max_depth=3&max_nodes=1000":
            return {"label": "manual", "nodes": [], "edges": []}
        if path == "/graphs?label=manual&max_depth=2&max_nodes=100":
            return {"label": "manual", "nodes": [], "edges": []}
        if path == "/graph/label/popular?limit=2":
            return [{"label": "manual", "count": 4}, {"label": "installation", "count": 2}]
        if path == "/graph/label/search?q=install&limit=3":
            return ["installation", "install steps"]
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append(("POST", path, payload, self.token))
        if path == "/auth/login":
            return {"access_token": "secret-token", "token_type": "bearer"}
        if path == "/query/retrieve":
            return {
                "query": payload["query"],
                "mode": payload["mode"],
                "evidence": [
                    {
                        "document_id": "doc-1",
                        "source_engine": payload["mode"],
                        "score": 0.8,
                        "page_start": 1,
                        "page_end": 1,
                        "text": "install steps evidence",
                    }
                ],
                "debug": {"selected_engine": payload["mode"]},
            }
        if path == "/query/answer" or path == "/query":
            return {
                "query": payload["query"],
                "mode": payload["mode"],
                "evidence": [{"document_id": "doc-1", "text": "install steps evidence"}],
                "answer": "ok",
            }
        if path == "/admin/documents/doc-1/index":
            return {"job_id": "job-1"}
        if path == "/admin/documents/doc-1/reindex":
            return {"job_id": "job-2"}
        if path == "/jobs/job-1/retry":
            return {"id": "job-1", "kind": "index_document", "status": "running"}
        raise AssertionError(f"unexpected POST {path}")

    def delete(self, path: str) -> Any:
        self.calls.append(("DELETE", path, None, self.token))
        if path == "/admin/documents/doc-1":
            return {"id": "doc-1", "filename": "manual.txt", "status": "deleted"}
        raise AssertionError(f"unexpected DELETE {path}")

    def post_file(self, path: str, field_name: str, filename: str, content: bytes) -> Any:
        self.calls.append(("FILE", path, {"field": field_name, "filename": filename, "content": content}, self.token))
        if path == "/admin/documents/upload":
            return {"document": {"id": "doc-1", "filename": filename}, "job_id": "job-1"}
        raise AssertionError(f"unexpected FILE {path}")


def base_args(config_dir: Path) -> list[str]:
    return ["--config-dir", str(config_dir), "--no-keyring"]


def login(config_dir: Path) -> None:
    result = runner.invoke(
        app,
        base_args(config_dir)
        + ["login", "--email", "admin@example.com", "--password", "secret", "--output", "json"],
    )
    assert result.exit_code == 0, result.output


def test_login_stores_token_without_printing_it(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()

    result = runner.invoke(
        app,
        base_args(tmp_path)
        + ["login", "--email", "admin@example.com", "--password", "secret", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    assert "secret-token" not in result.output
    assert json.loads(result.output)["email"] == "admin@example.com"
    assert (tmp_path / "credentials.json").exists()
    assert FakeApiClient.calls == [
        ("POST", "/auth/login", {"email": "admin@example.com", "password": "secret"}, None)
    ]


def test_logout_clears_credentials(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(app, base_args(tmp_path) + ["logout", "--output", "json"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"message": "Logged out"}
    assert not (tmp_path / "credentials.json").exists()


def test_protected_command_requires_login(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)

    result = runner.invoke(app, base_args(tmp_path) + ["documents", "list", "--output", "json"])

    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["code"] == "auth_required"


def test_documents_and_query_commands_use_current_backend_routes(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    commands = [
        ["documents", "list", "--output", "json"],
        ["documents", "show", "--document-id", "doc-1", "--output", "json"],
        ["documents", "structure", "--document-id", "doc-1", "--output", "json"],
        ["documents", "page", "--document-id", "doc-1", "--page-number", "1", "--output", "json"],
        ["documents", "retrieve", "--query", "install steps", "--mode", "hybrid", "--top-k", "3", "--output", "json"],
        ["documents", "answer", "--query", "install steps", "--output", "json"],
        ["query", "--query", "install steps", "--output", "json"],
    ]

    for command in commands:
        result = runner.invoke(app, base_args(tmp_path) + command)
        assert result.exit_code == 0, result.output

    assert ("GET", "/documents", None, "secret-token") in FakeApiClient.calls
    assert ("GET", "/documents/doc-1", None, "secret-token") in FakeApiClient.calls
    assert ("GET", "/documents/doc-1/structure", None, "secret-token") in FakeApiClient.calls
    assert ("GET", "/documents/doc-1/pages/1", None, "secret-token") in FakeApiClient.calls
    assert ("POST", "/query/retrieve", {"query": "install steps", "mode": "hybrid", "top_k": 3, "include_debug": False, "allow_general_fallback": False}, "secret-token") in FakeApiClient.calls


def test_documents_retrieve_can_filter_by_document_ids(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path)
        + [
            "documents",
            "retrieve",
            "--query",
            "install steps",
            "--document-id",
            "doc-1",
            "--document-id",
            "doc-2",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        "POST",
        "/query/retrieve",
        {
            "query": "install steps",
            "mode": "auto",
            "top_k": 8,
            "include_debug": False,
            "allow_general_fallback": False,
            "document_ids": ["doc-1", "doc-2"],
        },
        "secret-token",
    ) in FakeApiClient.calls


def test_documents_answer_can_filter_by_document_ids(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path)
        + [
            "documents",
            "answer",
            "--query",
            "install steps",
            "--document-id",
            "doc-1",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        "POST",
        "/query/answer",
        {
            "query": "install steps",
            "mode": "auto",
            "top_k": 8,
            "include_debug": False,
            "allow_general_fallback": False,
            "document_ids": ["doc-1"],
        },
        "secret-token",
    ) in FakeApiClient.calls


def test_query_command_can_filter_by_document_ids(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path)
        + [
            "query",
            "--query",
            "install steps",
            "--document-id",
            "doc-1",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (
        "POST",
        "/query",
        {
            "query": "install steps",
            "mode": "auto",
            "top_k": 8,
            "include_debug": False,
            "allow_general_fallback": False,
            "document_ids": ["doc-1"],
        },
        "secret-token",
    ) in FakeApiClient.calls


def test_admin_documents_and_jobs_use_current_backend_routes(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)
    upload_file = tmp_path / "manual.txt"
    upload_file.write_text("manual", encoding="utf-8")

    commands = [
        ["admin", "documents", "upload", "--file", str(upload_file), "--output", "json"],
        ["admin", "documents", "list", "--output", "json"],
        ["admin", "documents", "index", "--document-id", "doc-1", "--output", "json"],
        ["admin", "documents", "reindex", "--document-id", "doc-1", "--output", "json"],
        ["admin", "documents", "delete", "--document-id", "doc-1", "--output", "json"],
        ["jobs", "list", "--output", "json"],
        ["jobs", "status", "--job-id", "job-1", "--output", "json"],
        ["jobs", "retry", "--job-id", "job-1", "--output", "json"],
    ]

    for command in commands:
        result = runner.invoke(app, base_args(tmp_path) + command)
        assert result.exit_code == 0, result.output

    assert ("FILE", "/admin/documents/upload", {"field": "file", "filename": "manual.txt", "content": b"manual"}, "secret-token") in FakeApiClient.calls
    assert ("POST", "/admin/documents/doc-1/index", None, "secret-token") in FakeApiClient.calls
    assert ("POST", "/admin/documents/doc-1/reindex", None, "secret-token") in FakeApiClient.calls
    assert ("DELETE", "/admin/documents/doc-1", None, "secret-token") in FakeApiClient.calls
    assert ("GET", "/jobs/job-1", None, "secret-token") in FakeApiClient.calls


def test_admin_audit_logs_list_uses_current_backend_route(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path) + ["admin", "audit-logs", "list", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "audit_logs": [{"id": "audit-1", "event": "document.uploaded", "target_id": "doc-1"}]
    }
    assert ("GET", "/admin/audit-logs", None, "secret-token") in FakeApiClient.calls


def test_admin_query_logs_list_uses_current_backend_route(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path) + ["admin", "query-logs", "list", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "query_logs": [{"id": "query-1", "query": "install steps", "mode": "auto", "latency_ms": 12}]
    }
    assert ("GET", "/admin/query-logs", None, "secret-token") in FakeApiClient.calls


def test_lightrag_labels_list_uses_current_backend_route(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path) + ["lightrag", "labels", "list", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"labels": ["manual", "installation"]}
    assert ("GET", "/graph/label/list", None, "secret-token") in FakeApiClient.calls


def test_lightrag_graph_show_uses_current_backend_route(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path) + ["lightrag", "graphs", "show", "--label", "manual", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"graph": {"label": "manual", "nodes": [], "edges": []}}
    assert ("GET", "/graphs?label=manual&max_depth=3&max_nodes=1000", None, "secret-token") in FakeApiClient.calls


def test_lightrag_graph_show_can_set_depth_and_node_limit(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path)
        + [
            "lightrag",
            "graphs",
            "show",
            "--label",
            "manual",
            "--max-depth",
            "2",
            "--max-nodes",
            "100",
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0, result.output
    assert ("GET", "/graphs?label=manual&max_depth=2&max_nodes=100", None, "secret-token") in FakeApiClient.calls


def test_query_commands_accept_include_debug_alias(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path)
        + ["documents", "retrieve", "--query", "install steps", "--include-debug", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    assert (
        "POST",
        "/query/retrieve",
        {
            "query": "install steps",
            "mode": "auto",
            "top_k": 8,
            "include_debug": True,
            "allow_general_fallback": False,
        },
        "secret-token",
    ) in FakeApiClient.calls


def test_lightrag_labels_popular_uses_current_backend_route(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path) + ["lightrag", "labels", "popular", "--limit", "2", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {
        "labels": [{"label": "manual", "count": 4}, {"label": "installation", "count": 2}]
    }
    assert ("GET", "/graph/label/popular?limit=2", None, "secret-token") in FakeApiClient.calls


def test_lightrag_labels_search_uses_current_backend_route(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path)
        + ["lightrag", "labels", "search", "--query", "install", "--limit", "3", "--output", "json"],
    )

    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == {"labels": ["installation", "install steps"]}
    assert ("GET", "/graph/label/search?q=install&limit=3", None, "secret-token") in FakeApiClient.calls


def test_planned_command_returns_structured_backend_gap(tmp_path: Path) -> None:
    result = runner.invoke(app, base_args(tmp_path) + ["agents", "list", "--output", "json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["error"]["code"] == "not_supported_by_backend"
    assert "docs/cli_docs/api-contract.md" in payload["error"]["message"]


def test_documents_list_human_output_is_screen_like_ascii_table(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(app, base_args(tmp_path) + ["documents", "list"])

    assert result.exit_code == 0, result.output
    assert "DOCUMENTS" in result.output
    assert "doc-1" in result.output
    assert "manual.txt" in result.output
    assert "+" in result.output
    assert "|" in result.output
    assert "secret-token" not in result.output
    assert "┌" not in result.output
    assert "│" not in result.output


def test_documents_retrieve_human_output_shows_evidence_and_debug(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path)
        + ["documents", "retrieve", "--query", "install steps", "--include-debug"],
    )

    assert result.exit_code == 0, result.output
    assert "install steps" in result.output
    assert "install steps evidence" in result.output
    assert "doc-1" in result.output
    assert "Debug" in result.output


def test_query_human_output_shows_answer_and_sources(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(app, base_args(tmp_path) + ["query", "--query", "install steps"])

    assert result.exit_code == 0, result.output
    assert "ANSWER" in result.output
    assert "ok" in result.output
    assert "doc-1" in result.output


def test_lightrag_graph_show_human_output_summarizes_nodes_edges(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path) + ["lightrag", "graphs", "show", "--label", "manual"],
    )

    assert result.exit_code == 0, result.output
    assert "GRAPH" in result.output
    assert "manual" in result.output
    assert "nodes" in result.output
    assert "--output json" in result.output


def test_ui_command_is_registered() -> None:
    result = runner.invoke(app, ["ui", "--help"])

    assert result.exit_code == 0, result.output
    assert "interactive" in result.output.lower() or "tui" in result.output.lower()


def test_retrieval_compare_calls_all_supported_modes(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(
        app,
        base_args(tmp_path) + ["retrieval", "compare", "--query", "install steps", "--top-k", "5"],
    )

    assert result.exit_code == 0, result.output
    assert "RETRIEVAL MODE COMPARISON" in result.output
    assert "auto" in result.output
    assert "semantic" in result.output
    assert "navigation" in result.output
    assert "hybrid" in result.output
    called_modes = [
        call[2]["mode"]
        for call in FakeApiClient.calls
        if call[0] == "POST" and call[1] == "/query/retrieve"
    ]
    assert called_modes == ["auto", "semantic", "navigation", "hybrid"]


def test_admin_upload_flow_success_with_job_suggests_job_status(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)
    upload_file = tmp_path / "manual.txt"
    upload_file.write_text("manual", encoding="utf-8")

    result = runner.invoke(
        app,
        base_args(tmp_path) + ["admin", "documents", "upload-flow", "--file", str(upload_file)],
    )

    assert result.exit_code == 0, result.output
    assert "ADMIN DOCUMENT UPLOAD" in result.output
    assert "job-1" in result.output
    assert "ragcli jobs status --job-id job-1" in result.output
    assert ("GET", "/jobs/job-1", None, "secret-token") in FakeApiClient.calls


def test_admin_dashboard_calls_documents_jobs_and_query_logs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(app, base_args(tmp_path) + ["admin", "dashboard"])

    assert result.exit_code == 0, result.output
    assert "ADMIN DASHBOARD" in result.output
    assert ("GET", "/admin/documents", None, "secret-token") in FakeApiClient.calls
    assert ("GET", "/jobs", None, "secret-token") in FakeApiClient.calls
    assert ("GET", "/admin/query-logs", None, "secret-token") in FakeApiClient.calls


def test_screen_documents_renders_document_library(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", FakeApiClient)
    FakeApiClient.reset()
    login(tmp_path)

    result = runner.invoke(app, base_args(tmp_path) + ["screen", "documents"])

    assert result.exit_code == 0, result.output
    assert "DOCUMENTS" in result.output
    assert "doc-1" in result.output

