from io import StringIO
from pathlib import Path
from typing import Any, Callable

from rich.console import Console

from cli.api_client import ApiClientError, ApiRequestMetadata
from cli.credentials import CredentialStore, StoredCredentials
from cli.tui.app import run_tui
from cli.tui.keys import (
    KEY_BACKSPACE,
    KEY_DEBUG,
    KEY_DOWN,
    KEY_ENTER,
    KEY_INSPECT,
    KEY_QUIT,
    KEY_RAW_JSON,
    KEY_REFRESH,
    KEY_TOGGLE_FULL_IDS,
    KEY_UP,
    KEY_UPLOAD,
    normalize_key,
)


class FakeTuiClient:
    calls: list[tuple[str, str, Any, str | None]] = []
    fail_login = False
    fail_me = False
    fail_admin = False
    fail_upload_forbidden = False
    fail_upload_connection = False
    fail_graphs = False
    fail_domains = False
    current_username = "admin"
    current_user_role = "admin"
    documents: list[dict[str, Any]] = [{"id": "doc-1", "filename": "manual.txt", "status": "ready"}]
    upload_response: dict[str, Any] = {
        "document": {"id": "doc-2", "filename": "manual.pdf", "status": "uploaded"},
        "job_id": "job-456",
    }

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url
        self.token = token
        self.last_request: ApiRequestMetadata | None = None

    def _record(self, method: str, path: str, payload: Any, response: Any, status_code: int = 200) -> Any:
        self.last_request = ApiRequestMetadata(
            method=method,
            route=path,
            status_code=status_code,
            elapsed_ms=1,
            request_summary=payload,
            response_summary=response,
        )
        return response

    @classmethod
    def reset(cls) -> None:
        cls.calls = []
        cls.fail_login = False
        cls.fail_me = False
        cls.fail_admin = False
        cls.fail_upload_forbidden = False
        cls.fail_upload_connection = False
        cls.fail_graphs = False
        cls.fail_domains = False
        cls.current_username = "admin"
        cls.current_user_role = "admin"
        cls.documents = [{"id": "doc-1", "filename": "manual.txt", "status": "ready"}]
        cls.upload_response = {
            "document": {"id": "doc-2", "filename": "manual.pdf", "status": "uploaded"},
            "job_id": "job-456",
        }

    def get(self, path: str) -> Any:
        self.calls.append(("GET", path, None, self.token))
        if path == "/auth/me":
            if self.fail_me:
                raise ApiClientError("auth_expired", "session expired", 401)
            return self._record("GET", path, None, {"username": self.current_username, "role": self.current_user_role})
        if path == "/documents":
            return self._record("GET", path, None, self.documents)
        if path == "/documents/doc-1":
            return self._record("GET", path, None, {"id": "doc-1", "filename": "manual.txt", "status": "ready"})
        if path == "/documents/doc-1/structure?include_blocks=true&include_assets=true":
            return self._record("GET", path, None, {
                "document_id": "doc-1",
                "source": "document_structure",
                "tree": [{"title": "Safety", "level": 1, "page_start": 1, "page_end": 2}],
                "sections": [{"section_id": "doc-1-sec-1"}],
                "source_chunks": [{"chunk_id": "doc-1-source-chunk-1"}],
                "assets": [],
            })
        if path == "/documents/doc-1/structure-quality":
            return self._record("GET", path, None, {
                "document_id": "doc-1",
                "score": 1.0,
                "section_count": 2,
                "block_count": 8,
                "asset_count": 1,
                "should_run_toc_refiner": False,
                "reasons": [],
            })
        if path == "/graph/label/popular?limit=20":
            if self.fail_graphs:
                raise ApiClientError("service_disabled", "LightRAG graph proxy is disabled.", 503)
            return self._record("GET", path, None, [{"label": "manual", "count": 4}])
        if path == "/lightrag/domains":
            return self._record("GET", path, None, {
                "domains": [
                    {"id": "fatigue", "display_name": "Fatigue Manuals", "is_default": True},
                    {"id": "abaqus", "display_name": "Abaqus Manuals", "is_default": False},
                ]
            })
        if path == "/admin/lightrag/domains":
            if self.fail_domains:
                raise ApiClientError("service_disabled", "LightRAG domain deployment is disabled.", 503)
            return self._record("GET", path, None, {
                "domains": [
                    {
                        "id": "fatigue",
                        "display_name": "Fatigue Manuals",
                        "host_port": 9622,
                        "status": "configured",
                        "is_default": True,
                    }
                ]
            })
        if path == "/admin/lightrag/domains/fatigue":
            return self._record("GET", path, None, {
                "id": "fatigue",
                "display_name": "Fatigue Manuals",
                "host_port": 9622,
                "status": "running",
                "is_default": True,
            })
        if path == "/admin/documents":
            if self.fail_admin:
                raise ApiClientError("forbidden", "admin role required", 403)
            return self._record("GET", path, None, [{"id": "doc-1", "filename": "manual.txt", "status": "ready"}])
        if path == "/jobs":
            return self._record("GET", path, None, [{"id": "job-1", "kind": "document_ingest", "status": "queued"}])
        if path == "/jobs/job-456":
            return self._record(
                "GET",
                path,
                None,
                {"id": "job-456", "kind": "document_ingest", "status": "queued", "document_id": "doc-2"},
            )
        if path == "/admin/query-logs":
            return self._record("GET", path, None, [{"id": "query-1", "query": "install steps", "mode": "auto"}])
        if path == "/admin/audit-logs":
            return self._record("GET", path, None, [{"id": "audit-1", "event": "document.uploaded", "target_id": "doc-1"}])
        if path == "/health":
            return self._record("GET", path, None, {"status": "ok"})
        if path == "/health/readiness":
            return self._record("GET", path, None, {"status": "ready"})
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append(("POST", path, payload, self.token))
        if path == "/auth/login":
            if self.fail_login:
                raise ApiClientError("auth_failed", "Invalid username or password.", 401)
            return self._record("POST", path, payload, {"access_token": "secret-token", "token_type": "bearer"})
        if path == "/admin/lightrag/domains":
            return self._record("POST", path, payload, {
                "id": payload["domain_id"],
                "display_name": payload.get("display_name") or payload["domain_id"],
                "host_port": payload.get("host_port"),
                "status": "configured",
                "is_default": bool(payload.get("make_default")),
            })
        if path.startswith("/admin/lightrag/domains/"):
            domain_id = path.split("/")[4]
            operation = path.rsplit("/", 1)[-1]
            return self._record("POST", path, payload, {
                "id": domain_id,
                "operation": operation,
                "status": "succeeded",
                "service_name": f"lightrag-{domain_id}",
                "message": None,
            })
        if path == "/retrieve":
            return self._record("POST", path, payload, {
                "query": payload["query"],
                "mode": payload["mode"],
                "evidence": [{"document_id": "doc-1", "text": "reset procedure evidence"}],
            })
        raise AssertionError(f"unexpected POST {path}")

    def delete(self, path: str) -> Any:
        self.calls.append(("DELETE", path, None, self.token))
        if path.startswith("/admin/lightrag/domains/"):
            domain_id = path.split("/")[4].split("?")[0]
            return self._record("DELETE", path, None, {
                "id": domain_id,
                "archived": "permanent=true" not in path,
                "archive_path": f".data/lightrag/deleted/{domain_id}",
                "permanent": "permanent=true" in path,
            })
        raise AssertionError(f"unexpected DELETE {path}")

    def post_file(self, path: str, field_name: str, filename: str, content: bytes) -> Any:
        self.calls.append(
            (
                "POST_FILE",
                path,
                {"field_name": field_name, "filename": filename, "content_size": len(content)},
                self.token,
            )
        )
        if self.fail_upload_forbidden:
            raise ApiClientError("forbidden", "Admin permission required.", 403)
        if self.fail_upload_connection:
            raise ApiClientError("service_unavailable", "Backend unavailable.", 503)
        return self._record(
            "POST",
            path,
            {"field_name": field_name, "filename": filename, "content_size": len(content)},
            self.upload_response,
        )


def input_sequence(values: list[str]):
    iterator = iter(values)

    def _input(_prompt: str) -> str:
        return next(iterator)

    return _input


def run_with_inputs(
    tmp_path: Path,
    values: list[str],
    store: CredentialStore | None = None,
    *,
    client_setup: Callable[[], None] | None = None,
) -> str:
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)
    FakeTuiClient.reset()
    if client_setup:
        client_setup()
    run_tui(
        api_base_url="http://127.0.0.1:8000",
        credential_store=store or CredentialStore(tmp_path, keyring_enabled=False),
        client_factory=FakeTuiClient,
        console=console,
        input_func=input_sequence(values),
    )
    return stream.getvalue()


def run_with_cursor_events(tmp_path: Path, values: list[str]) -> list[bool]:
    cursor_events: list[bool] = []
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)
    FakeTuiClient.reset()
    run_tui(
        api_base_url="http://127.0.0.1:8000",
        credential_store=CredentialStore(tmp_path, keyring_enabled=False),
        client_factory=FakeTuiClient,
        console=console,
        input_func=input_sequence(values),
        cursor_control=cursor_events.append,
    )
    return cursor_events


def authenticated_store(tmp_path: Path) -> CredentialStore:
    store = CredentialStore(tmp_path, keyring_enabled=False)
    store.save(StoredCredentials(base_url="http://127.0.0.1:8000", access_token="secret-token"))
    return store


def test_tui_normalizes_real_terminal_navigation_keys() -> None:
    assert normalize_key("\xe0P") == KEY_DOWN
    assert normalize_key("\x00P") == KEY_DOWN
    assert normalize_key("\x1b[B") == KEY_DOWN
    assert normalize_key("\xe0H") == KEY_UP
    assert normalize_key("\x00H") == KEY_UP
    assert normalize_key("\x1b[A") == KEY_UP
    assert normalize_key("\r") == KEY_ENTER
    assert normalize_key("\x08") == KEY_BACKSPACE
    assert normalize_key("\x12") == KEY_REFRESH
    assert normalize_key("r") == KEY_REFRESH
    assert normalize_key("refresh") == KEY_REFRESH
    assert normalize_key("upload") == KEY_UPLOAD
    assert normalize_key("i") == KEY_INSPECT
    assert normalize_key("j") == KEY_RAW_JSON
    assert normalize_key("f") == KEY_TOGGLE_FULL_IDS
    assert normalize_key("d") == KEY_DEBUG
    assert normalize_key("q") == KEY_QUIT


def test_tui_starts_at_login_when_no_session_exists(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["q"])

    assert "SESSION / LOGIN" in output
    assert "Username" in output
    assert "Password" in output
    assert "Admin Documents" not in output


def test_tui_replaces_previous_frame_in_non_terminal_mode(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["admin", "tab", "password123", "enter", "q"])

    assert "CONTEXT ENGINE" in output
    assert "CONTEXT ENGINE LOGIN" not in output


def test_tui_balances_cursor_visibility_on_exit(tmp_path: Path) -> None:
    assert run_with_cursor_events(tmp_path, ["q"]) == [False, True]


def test_user_can_login_from_tui_and_reaches_main_menu(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["admin", "tab", "password123", "enter", "q"])

    assert ("POST", "/auth/login", {"username": "admin", "password": "password123"}, None) in FakeTuiClient.calls
    assert (tmp_path / "credentials.json").exists()
    assert "CONTEXT ENGINE" in output
    assert "Documents" in output
    assert "secret-token" not in output
    assert "password123" not in output


def test_user_can_navigate_login_fields_with_down_and_up_keys(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["admin", "down", "password123", "up", "down", "enter", "q"],
    )

    assert ("POST", "/auth/login", {"username": "admin", "password": "password123"}, None) in FakeTuiClient.calls
    assert "CONTEXT ENGINE" in output
    assert "down" not in FakeTuiClient.calls[0][2]["username"]
    assert "up" not in FakeTuiClient.calls[0][2]["password"]


def test_failed_tui_login_shows_retry_without_leaking_password(tmp_path: Path) -> None:
    FakeTuiClient.reset()
    FakeTuiClient.fail_login = True

    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)
    run_tui(
        api_base_url="http://127.0.0.1:8000",
        credential_store=CredentialStore(tmp_path, keyring_enabled=False),
        client_factory=FakeTuiClient,
        console=console,
        input_func=input_sequence(["admin", "tab", "bad-password", "enter", "q"]),
    )
    output = stream.getvalue()

    assert "SESSION / LOGIN FAILED" in output
    assert "[ERROR]" in output
    assert "Invalid username or password" in output
    assert "bad-password" not in output
    assert "secret-token" not in output


def test_existing_valid_session_opens_main_menu(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["q"], authenticated_store(tmp_path))

    assert ("GET", "/auth/me", None, "secret-token") in FakeTuiClient.calls
    assert "Session: admin" in output
    assert "Graphs" in output
    assert output.count("LightRAG Domains") == 1
    assert "LightRAG Graphs" not in output
    assert "Admin Documents" not in output
    assert "Create LightRAG Domain" not in output
    assert "Start LightRAG Domain" not in output
    assert "Stop LightRAG Domain" not in output
    assert "Recreate LightRAG Domain" not in output
    assert "Remove LightRAG Domain" not in output
    assert "Backend Gaps" not in output


def test_non_admin_session_hides_admin_only_root_menu_items(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["q"],
        authenticated_store(tmp_path),
        client_setup=lambda: (
            setattr(FakeTuiClient, "current_username", "user"),
            setattr(FakeTuiClient, "current_user_role", "user"),
        ),
    )

    assert "Session: user" in output
    assert "LightRAG Domains" not in output
    assert "Jobs" not in output
    assert "Observability" not in output
    assert "Backend Gaps" not in output


def test_documents_screen_hides_admin_actions_for_non_admin_users(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "current_user_role", "user"),
    )

    assert "DOCUMENTS / LIBRARY" in output
    assert "Admin Actions" not in output


def test_expired_session_is_cleared_and_login_screen_is_shown(tmp_path: Path) -> None:
    store = authenticated_store(tmp_path)
    FakeTuiClient.reset()
    FakeTuiClient.fail_me = True
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)

    run_tui(
        api_base_url="http://127.0.0.1:8000",
        credential_store=store,
        client_factory=FakeTuiClient,
        console=console,
        input_func=input_sequence(["q"]),
    )
    output = stream.getvalue()

    assert "Previous session expired. Please log in again." in output
    assert "SESSION / LOGIN" in output
    assert not (tmp_path / "credentials.json").exists()


def test_user_can_move_selection_with_arrow_keys(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["down", "down", "up", "q"], authenticated_store(tmp_path))

    assert "> Retrieval" in output
    assert "> LightRAG Graphs" not in output


def test_tui_documents_screen_renders_document_library(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["enter", "q"], authenticated_store(tmp_path))

    assert "doc-1" in output
    assert "manual.txt" in output
    assert "+" in output
    assert "│" not in output
    assert ("GET", "/documents", None, "secret-token") in FakeTuiClient.calls


def test_empty_documents_screen_shows_upload_refresh_back_quit(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "documents", []),
    )

    assert "No documents found." in output
    assert "Admin Actions" in output
    assert "Refresh" in output
    assert "Back" in output
    assert "Quit" in output
    assert "Enter    Open selected document" not in output
    assert output.count("No documents found.") == 1


def test_empty_documents_upload_action_opens_file_path_form(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "documents", []),
    )

    assert "DOCUMENTS / ADMIN ACTIONS / UPLOAD" in output
    assert "File path:" in output
    assert "Enter Submit" in output


def test_upload_form_invalid_file_path_shows_error_without_backend_call(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", "./missing-file.pdf", "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "documents", []),
    )

    assert "DOCUMENTS / ADMIN ACTIONS / UPLOAD / ERROR" in output
    assert "[ERROR] file_not_found" in output
    assert "Edit file path" in output
    upload_calls = [call for call in FakeTuiClient.calls if call[0] == "POST_FILE"]
    assert not upload_calls


def test_upload_form_valid_file_path_calls_admin_upload_route(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "documents", []),
    )

    upload_calls = [call for call in FakeTuiClient.calls if call[0] == "POST_FILE"]
    assert upload_calls
    method, path, payload, token = upload_calls[-1]
    assert method == "POST_FILE"
    assert path == "/admin/documents/upload"
    assert payload["field_name"] == "file"
    assert payload["filename"] == "manual.pdf"
    assert payload["content_size"] == len(b"test-pdf")
    assert token == "secret-token"
    assert "DOCUMENTS / ADMIN ACTIONS / UPLOAD" in output
    assert "[SUCCESS] Upload complete." in output


def test_upload_success_with_job_shows_view_job_status_action(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "documents", []),
    )

    assert "Document ID" in output
    assert "doc-2" in output
    assert "Job ID" in output
    assert "job-456" in output
    assert "View job status" in output
    assert "Show full IDs" in output


def test_upload_success_without_job_handles_lightrag_forwarding(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    def setup() -> None:
        FakeTuiClient.documents = []
        FakeTuiClient.upload_response = {
            "document": {
                "id": "doc-3",
                "filename": "manual.pdf",
                "status": "forwarded_to_lightrag",
                "metadata": {"lightrag": {"status": "accepted"}},
            },
            "job_id": None,
        }

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=setup,
    )

    assert "[SUCCESS] Upload complete." in output
    assert "Local job ID" in output
    assert "none" in output
    assert "View LightRAG labels" in output
    assert "View job status" not in output
    assert "Show full IDs" in output


def test_upload_backend_403_renders_forbidden_screen(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    def setup() -> None:
        FakeTuiClient.documents = []
        FakeTuiClient.fail_upload_forbidden = True

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=setup,
    )

    assert "DOCUMENTS / ADMIN ACTIONS / UPLOAD / FORBIDDEN" in output
    assert "[ERROR]" in output
    assert "Admin permission required" in output
    upload_calls = [call for call in FakeTuiClient.calls if call[0] == "POST_FILE"]
    assert upload_calls


def test_documents_screen_with_documents_includes_upload_shortcut(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["enter", "q"], authenticated_store(tmp_path))

    assert "A Admin actions" in output
    assert "Enter Open" in output


def test_upload_flow_replaces_previous_screen_instead_of_appending_output(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "documents", []),
    )

    assert "DOCUMENTS / ADMIN ACTIONS / UPLOAD" in output
    legacy_name = "rag" + "cli"
    assert legacy_name not in output
    assert output.count("No documents found.") <= 1


def test_tui_documents_screen_refresh_reloads_documents(tmp_path: Path) -> None:
    run_with_inputs(tmp_path, ["enter", "\x12", "q"], authenticated_store(tmp_path))

    document_calls = [call for call in FakeTuiClient.calls if call[0] == "GET" and call[1] == "/documents"]
    assert len(document_calls) == 2


def test_back_from_document_detail_returns_to_documents_screen(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["enter", "enter", "q"], authenticated_store(tmp_path))

    assert "DOCUMENTS / DETAIL" in output
    assert ("GET", "/documents/doc-1", None, "secret-token") in FakeTuiClient.calls


def test_document_detail_shows_structure_quality(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["enter", "enter", "q"], authenticated_store(tmp_path))

    assert "Structure Quality" in output
    assert "TOC Refiner" in output  # quality signal only; no TOC report endpoint is used
    assert ("GET", "/documents/doc-1/structure-quality", None, "secret-token") in FakeTuiClient.calls


def test_document_detail_does_not_request_toc_refinement_report(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["enter", "enter", "q"], authenticated_store(tmp_path))

    assert "TOC Refinement" not in output
    assert ("GET", "/documents/doc-1/toc-refinement-report", None, "secret-token") not in FakeTuiClient.calls


def test_enter_from_document_detail_opens_structure_screen(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["enter", "enter", "enter", "q"], authenticated_store(tmp_path))

    assert "DOCUMENTS / DETAIL / STRUCTURE" in output
    assert "document_structure" in output
    assert "Safety" in output
    assert (
        "GET",
        "/documents/doc-1/structure?include_blocks=true&include_assets=true",
        None,
        "secret-token",
    ) in FakeTuiClient.calls


def test_upload_result_truncates_long_document_and_job_ids(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    long_doc = "54d1d5577f8a9012abcdef1234567890b7308d2905"
    long_job = "a11223344556677889900abcdeffedcba00998877665544332211"

    def setup() -> None:
        FakeTuiClient.documents = []
        FakeTuiClient.upload_response = {
            "document": {"id": long_doc, "filename": "manual.pdf", "status": "uploaded"},
            "job_id": long_job,
        }

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=setup,
    )

    assert "54d1d557...90b7308d2905" in output
    assert "a1122334...665544332211" in output
    assert long_doc not in output
    assert long_job not in output


def test_upload_result_show_full_ids_opens_details_screen(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    long_doc = "54d1d5577f8a9012abcdef1234567890b7308d2905"
    long_job = "a11223344556677889900abcdeffedcba00998877665544332211"

    def setup() -> None:
        FakeTuiClient.documents = []
        FakeTuiClient.upload_response = {
            "document": {"id": long_doc, "filename": "manual.pdf", "status": "uploaded"},
            "job_id": long_job,
        }

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "down", "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=setup,
    )

    assert "DOCUMENTS / ADMIN ACTIONS / UPLOAD / DETAILS" in output
    assert long_doc in output
    assert long_job in output


def test_upload_success_defaults_to_view_job_status_when_job_exists(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "documents", []),
    )

    assert "JOBS / STATUS" in output
    assert ("GET", "/jobs/job-456", None, "secret-token") in FakeTuiClient.calls


def test_upload_success_without_job_defaults_to_return_documents(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    def setup() -> None:
        FakeTuiClient.documents = []
        FakeTuiClient.upload_response = {
            "document": {"id": "doc-3", "filename": "manual.pdf", "status": "uploaded"},
            "job_id": None,
        }

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=setup,
    )

    assert "DOCUMENTS / LIBRARY" in output


def test_upload_result_uses_compact_footer(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "documents", []),
    )

    assert "Up/Down Select | Enter Choose | I Inspect API | J Raw JSON | F Toggle full IDs | B Back | Q Quit" in output


def test_upload_connection_failure_shows_retry_options(tmp_path: Path) -> None:
    source_file = tmp_path / "manual.pdf"
    source_file.write_bytes(b"test-pdf")

    def setup() -> None:
        FakeTuiClient.documents = []
        FakeTuiClient.fail_upload_connection = True

    output = run_with_inputs(
        tmp_path,
        ["enter", "enter", "enter", str(source_file), "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=setup,
    )

    assert "DOCUMENTS / ADMIN ACTIONS / UPLOAD / ERROR" in output
    assert "service_unavailable: Backend unavailable." in output
    assert "Retry upload" in output
    assert "Edit file path" in output


def test_tui_retrieval_screen_accepts_query_and_shows_evidence(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["down", "enter", "reset procedure", "enter", "q"], authenticated_store(tmp_path))

    assert "reset procedure" in output
    assert "reset procedure evidence" in output
    assert "Compare modes" in output


def test_tui_retrieval_result_inspect_shows_request_payload(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down", "enter", "reset procedure", "enter", "i", "q"],
        authenticated_store(tmp_path),
    )

    assert "RETRIEVAL / CONTEXT / INSPECT API" in output
    assert "Route" in output
    assert "/retrieve" in output
    assert "Request JSON" in output
    assert '"query": "reset procedure"' in output
    assert '"top_k": 8' in output


def test_tui_retrieval_result_raw_json_is_on_demand(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down", "enter", "reset procedure", "enter", "j", "q"],
        authenticated_store(tmp_path),
    )

    assert "RETRIEVAL / CONTEXT / RAW JSON" in output
    assert '"evidence"' in output
    assert '"document_id": "doc-1"' in output


def test_tui_retrieval_prompt_renders_lightrag_domain_selector(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["down", "enter", "q"], authenticated_store(tmp_path))

    assert "LightRAG domain: fatigue" in output
    assert ("GET", "/lightrag/domains", None, "secret-token") in FakeTuiClient.calls


def test_tui_retrieval_prompt_can_select_lightrag_domain(tmp_path: Path) -> None:
    run_with_inputs(
        tmp_path,
        ["down", "enter", "tab", "fatigue limits", "enter", "q"],
        authenticated_store(tmp_path),
    )

    retrieval_calls = [call for call in FakeTuiClient.calls if call[0] == "POST" and call[1] == "/retrieve"]
    assert retrieval_calls[-1][2]["lightrag_domain_id"] == "abaqus"


def test_tui_retrieval_screen_preserves_spaces_when_typing_character_by_character(tmp_path: Path) -> None:
    keys = ["down", "enter", *list("reset procedure"), "enter", "q"]
    output = run_with_inputs(tmp_path, keys, authenticated_store(tmp_path))

    assert "reset procedure" in output
    retrieval_calls = [call for call in FakeTuiClient.calls if call[0] == "POST" and call[1] == "/retrieve"]
    assert retrieval_calls
    assert retrieval_calls[-1][2]["query"] == "reset procedure"


def test_tui_retrieval_result_compare_modes_opens_comparison_screen(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down", "enter", "reset procedure", "enter", "enter", "q"],
        authenticated_store(tmp_path),
    )

    assert "RETRIEVAL / COMPARE MODES" in output
    assert "auto" in output
    assert "semantic" in output
    assert "navigation" in output
    assert "hybrid" in output
    compare_calls = [call for call in FakeTuiClient.calls if call[0] == "POST" and call[1] == "/retrieve"]
    assert len(compare_calls) == 5


def test_tui_health_screen_reads_health_and_readiness(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["down", "down", "down", "down", "down", "down", "enter", "q"], authenticated_store(tmp_path))

    assert "HEALTH" in output
    assert "readiness" in output
    assert "Detail" in output
    assert ("GET", "/health", None, "secret-token") in FakeTuiClient.calls
    assert ("GET", "/health/readiness", None, "secret-token") in FakeTuiClient.calls


def test_logout_clears_session_and_returns_to_logged_out_screen(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down", "down", "down", "down", "down", "down", "down", "enter", "q"],
        authenticated_store(tmp_path),
    )

    assert "SESSION / LOGGED OUT" in output
    assert "[SUCCESS] Your local CLI session has been cleared." in output
    assert not (tmp_path / "credentials.json").exists()


def test_lightrag_tui_screen_uses_backend_graph_proxy(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["down", "down", "enter", "q"], authenticated_store(tmp_path))

    assert "GRAPHS / LABELS" in output
    assert ("GET", "/graph/label/popular?limit=20", None, "secret-token") in FakeTuiClient.calls


def test_graphs_screen_shows_honest_disabled_state_when_backend_unavailable(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down", "down", "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "fail_graphs", True),
    )

    assert "GRAPHS / LABELS" in output
    assert "[ERROR]" in output
    assert "LightRAG graph proxy is disabled" in output


def test_lightrag_domains_tui_screen_uses_backend_admin_api(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["down", "down", "down", "enter", "q"], authenticated_store(tmp_path))

    assert "LIGHTRAG / DOMAINS" in output
    assert "Create Domain" in output
    assert "Show Domain Detail" in output
    assert "Regenerate Domain Files" in output
    assert "Permanent Delete Domain" in output
    assert "fatigue" in output


def test_lightrag_domains_screen_shows_disabled_state_without_hiding_actions(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down", "down", "down", "enter", "q"],
        authenticated_store(tmp_path),
        client_setup=lambda: setattr(FakeTuiClient, "fail_domains", True),
    )

    assert "LIGHTRAG / DOMAINS" in output
    assert "[ERROR]" in output
    assert "LightRAG domain deployment is disabled" in output
    assert "Create Domain" in output
    assert ("GET", "/admin/lightrag/domains", None, "secret-token") in FakeTuiClient.calls


def test_tui_create_lightrag_domain_posts_admin_payload(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        [
            "down",
            "down",
            "down",
            "enter",
            "down",
            "enter",
            *list("fatigue"),
            "tab",
            *list("Fatigue Manuals"),
            "tab",
            *list("9622"),
            "tab",
            "y",
            "enter",
            "q",
        ],
        authenticated_store(tmp_path),
    )

    assert "LIGHTRAG / DOMAINS / CREATE" in output
    assert "[SUCCESS] Domain created." in output
    assert (
        "POST",
        "/admin/lightrag/domains",
        {
            "domain_id": "fatigue",
            "display_name": "Fatigue Manuals",
            "host_port": 9622,
            "make_default": True,
        },
        "secret-token",
    ) in FakeTuiClient.calls


def test_tui_start_lightrag_domain_posts_up_operation(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down"] * 3 + ["enter"] + ["down"] * 3 + ["enter", *list("fatigue"), "enter", "q"],
        authenticated_store(tmp_path),
    )

    assert "LIGHTRAG / DOMAINS / START" in output
    assert "[SUCCESS] start succeeded." in output
    assert ("POST", "/admin/lightrag/domains/fatigue/up", None, "secret-token") in FakeTuiClient.calls


def test_tui_stop_lightrag_domain_posts_down_operation(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down"] * 3 + ["enter"] + ["down"] * 4 + ["enter", *list("fatigue"), "enter", "q"],
        authenticated_store(tmp_path),
    )

    assert "LIGHTRAG / DOMAINS / STOP" in output
    assert "[SUCCESS] stop succeeded." in output
    assert ("POST", "/admin/lightrag/domains/fatigue/down", None, "secret-token") in FakeTuiClient.calls


def test_tui_recreate_lightrag_domain_requires_confirmation(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down"] * 3 + ["enter"] + ["down"] * 5 + ["enter", *list("fatigue"), "tab", *list("RECREATE"), "enter", "q"],
        authenticated_store(tmp_path),
    )

    assert "LIGHTRAG / DOMAINS / RECREATE" in output
    assert "[SUCCESS] recreate succeeded." in output
    assert ("POST", "/admin/lightrag/domains/fatigue/recreate", None, "secret-token") in FakeTuiClient.calls


def test_tui_remove_lightrag_domain_archives_by_default(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        ["down"] * 3 + ["enter"] + ["down"] * 7 + ["enter", *list("fatigue"), "tab", "tab", *list("REMOVE"), "enter", "q"],
        authenticated_store(tmp_path),
    )

    assert "LIGHTRAG / DOMAINS / REMOVE" in output
    assert "[SUCCESS] Domain removed." in output
    assert ("DELETE", "/admin/lightrag/domains/fatigue", None, "secret-token") in FakeTuiClient.calls


def test_tui_remove_lightrag_domain_permanent_delete_requires_confirmation(tmp_path: Path) -> None:
    output = run_with_inputs(
        tmp_path,
        [
            "down",
            "down",
            "down",
            "enter",
            "down",
            "down",
            "down",
            "down",
            "down",
            "down",
            "down",
            "down",
            "enter",
            *list("fatigue"),
            "tab",
            "tab",
            *list("PERMANENT DELETE"),
            "enter",
            "q",
        ],
        authenticated_store(tmp_path),
    )

    assert "LIGHTRAG / DOMAINS / REMOVE" in output
    assert "[SUCCESS] Domain permanently deleted." in output
    assert ("DELETE", "/admin/lightrag/domains/fatigue?permanent=true", None, "secret-token") in FakeTuiClient.calls


def test_admin_screen_renders_backend_403_without_local_admin_check(tmp_path: Path) -> None:
    store = authenticated_store(tmp_path)
    FakeTuiClient.reset()
    FakeTuiClient.fail_admin = True
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)

    run_tui(
        api_base_url="http://127.0.0.1:8000",
        credential_store=store,
        client_factory=FakeTuiClient,
        console=console,
        input_func=input_sequence(["enter", "a", "down", "enter", "q"]),
    )

    assert ("GET", "/admin/documents", None, "secret-token") in FakeTuiClient.calls
    output = stream.getvalue()
    assert "[ERROR] forbidden: admin role required" in output
    assert "DOCUMENTS / ADMIN ACTIONS / LIST ALL" in output


def test_jobs_screen_uses_warn_semantic_label_for_running_states(tmp_path: Path) -> None:
    output = run_with_inputs(tmp_path, ["down", "down", "down", "down", "enter", "q"], authenticated_store(tmp_path))

    assert "JOBS" in output
    assert "[WARN] Contains active statuses." in output
