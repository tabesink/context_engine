"""Domain content screens for the TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from rich.console import Console

from cli.api_client import ApiClientError
from cli.flows.retrieval_compare import build_retrieval_compare_screen, compare_retrieval_modes
from cli.query_payload import build_query_payload
from cli.renderers.tables import render_ascii_table
from cli.renderers.base import render_screen_result
from cli.screens.admin_documents import build_admin_documents_screen
from cli.screens.documents import build_document_detail_screen
from cli.screens.jobs import build_job_status_screen, build_jobs_screen
from cli.screens.lightrag import build_labels_screen
from cli.screens.models import ScreenResult
from cli.screens.observability import build_audit_logs_screen, build_query_logs_screen
from cli.screens.planned import build_backend_gaps_screen
from cli.screens.retrieval import build_answer_screen, build_retrieval_screen
from cli.tui.keys import (
    KEY_BACK,
    KEY_BACKSPACE,
    KEY_DOWN,
    KEY_ENTER,
    KEY_QUIT,
    KEY_REFRESH,
    KEY_TAB,
    KEY_UP,
    KEY_UPLOAD,
)
from cli.tui.navigation import move_selection_down, move_selection_up
from cli.tui.screen import ScreenCommand
from cli.tui.state import TuiState
from cli.tui.styles import (
    render_breadcrumb,
    render_key_footer,
    render_status_line,
    truncate_id,
)

ScreenBuilder = Callable[[Any], ScreenResult]


def _client(state: TuiState) -> Any:
    if state.client is None:
        state.reset_anonymous_client()
    return state.client


@dataclass
class ErrorScreen:
    message: str
    title: str = "Error"

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, self.title)
        render_status_line(console, "error", self.message)
        render_key_footer(console, ["B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        return ScreenCommand.none()


@dataclass
class ApiResultScreen:
    title: str
    path: str
    builder: ScreenBuilder
    payload: Any | None = None
    breadcrumb_trail: tuple[str, ...] = ()

    @staticmethod
    def _level_for_payload(payload: Any) -> str | None:
        if isinstance(payload, list):
            statuses = [str(item.get("status", "")).lower().strip() for item in payload if isinstance(item, dict)]
            if any(status in {"failed", "error"} for status in statuses):
                return "error"
            if any(status in {"queued", "running", "pending"} for status in statuses):
                return "warn"
            if statuses and all(status in {"done", "completed", "succeeded", "success", "ready"} for status in statuses):
                return "success"
            return None
        if not isinstance(payload, dict):
            return None
        status = str(payload.get("status", "")).lower().strip()
        if not status:
            return None
        if status in {"queued", "running", "pending"}:
            return "warn"
        if status in {"failed", "error"}:
            return "error"
        if status in {"done", "completed", "succeeded", "success", "ready"}:
            return "success"
        return None

    def render(self, console: Console, state: TuiState) -> None:
        trail = self.breadcrumb_trail or (self.title,)
        render_breadcrumb(console, *trail)
        try:
            if self.payload is None:
                self.payload = _client(state).get(self.path)
            level = self._level_for_payload(self.payload)
            if level:
                if isinstance(self.payload, dict):
                    message = f"Status: {self.payload.get('status')}"
                else:
                    message = "Contains active statuses."
                render_status_line(console, level, message)
            render_screen_result(self.builder(self.payload), console=console, show_title=False)
        except ApiClientError as exc:
            render_status_line(console, "error", f"{exc.code}: {exc.message}")
        render_key_footer(console, ["Ctrl+R Refresh", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            self.payload = None
            return ScreenCommand.none()
        return ScreenCommand.none()


@dataclass
class BackendGapsScreen:
    title: str = "Backend Gaps"

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Backend Gaps")
        render_screen_result(build_backend_gaps_screen(), console=console, show_title=False)
        render_key_footer(console, ["Ctrl+R Refresh", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            return ScreenCommand.none()
        return ScreenCommand.none()


@dataclass
class DocumentsScreen:
    title: str = "Documents"
    documents: list[dict[str, Any]] | None = None
    selected_index: int = 0
    empty_action_index: int = 0

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Documents", "Library")
        try:
            if self.documents is None:
                self.documents = _client(state).get("/documents")
            if self.documents:
                rows: list[dict[str, Any]] = []
                for index, document in enumerate(self.documents):
                    marker = "> " if index == self.selected_index else "  "
                    rows.append(
                        {
                            "id": f"{marker}{document.get('id', '')}",
                            "filename": document.get("filename", ""),
                            "status": document.get("status", ""),
                        }
                    )
                render_ascii_table("", rows, ["id", "filename", "status"], console=console)
                render_key_footer(
                    console,
                    [
                        "Up/Down Select document",
                        "Enter Open",
                        "U Upload",
                        "Ctrl+R Refresh",
                        "B Back",
                        "Q Quit",
                    ],
                )
            else:
                actions = ("Upload document", "Refresh", "Back", "Quit")
                console.print("No documents found.")
                console.print("")
                for index, action in enumerate(actions):
                    marker = ">" if index == self.empty_action_index else " "
                    console.print(f"{marker} {action}")
                render_key_footer(
                    console,
                    ["Up/Down Select", "Enter Choose", "Ctrl+R Refresh", "B Back", "Q Quit"],
                )
        except ApiClientError as exc:
            render_status_line(console, "error", f"{exc.code}: {exc.message}")
            render_key_footer(console, ["Ctrl+R Refresh", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            self.documents = None
            self.selected_index = 0
            self.empty_action_index = 0
            return ScreenCommand.none()
        count = len(self.documents or [])
        if key == KEY_UP:
            if count:
                self.selected_index = move_selection_up(self.selected_index, count)
            else:
                self.empty_action_index = move_selection_up(self.empty_action_index, 4)
            return ScreenCommand.none()
        if key == KEY_DOWN:
            if count:
                self.selected_index = move_selection_down(self.selected_index, count)
            else:
                self.empty_action_index = move_selection_down(self.empty_action_index, 4)
            return ScreenCommand.none()
        if key in {KEY_UPLOAD, "u", "U"}:
            return ScreenCommand.push(UploadDocumentScreen())
        if key == KEY_ENTER:
            if self.documents:
                document_id = str(self.documents[self.selected_index].get("id", ""))
                if document_id:
                    return ScreenCommand.push(DocumentDetailScreen(document_id=document_id))
                return ScreenCommand.none()
            if self.empty_action_index == 0:
                return ScreenCommand.push(UploadDocumentScreen())
            if self.empty_action_index == 1:
                self.documents = None
                self.selected_index = 0
                self.empty_action_index = 0
                return ScreenCommand.none()
            if self.empty_action_index == 2:
                return ScreenCommand.pop()
            return ScreenCommand.quit()
        return ScreenCommand.none()


@dataclass
class DocumentDetailScreen:
    document_id: str
    title: str = "Document Detail"
    document: dict[str, Any] | None = None

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Documents", "Detail")
        try:
            if self.document is None:
                self.document = _client(state).get(f"/documents/{self.document_id}")
            render_screen_result(build_document_detail_screen(self.document), console=console, show_title=False)
        except ApiClientError as exc:
            render_status_line(console, "error", f"{exc.code}: {exc.message}")
        render_key_footer(console, ["Ctrl+R Refresh", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            self.document = None
            return ScreenCommand.none()
        return ScreenCommand.none()


@dataclass
class UploadDocumentScreen:
    title: str = "Upload Document"
    file_path: str = ""

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Admin Documents", "Upload")
        console.print("File path:")
        console.print(f"  [ {self.file_path} ]")
        render_key_footer(console, ["Enter Submit", "Tab Next field", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_TAB:
            return ScreenCommand.none()
        if key == KEY_BACKSPACE:
            self.file_path = self.file_path[:-1]
            return ScreenCommand.none()
        if key == KEY_ENTER:
            candidate = Path(self.file_path.strip())
            if not candidate.exists() or not candidate.is_file():
                return ScreenCommand.push(UploadErrorScreen(file_path=self.file_path.strip()))
            try:
                payload = _client(state).post_file(
                    "/admin/documents/upload",
                    field_name="file",
                    filename=candidate.name,
                    content=candidate.read_bytes(),
                )
            except ApiClientError as exc:
                if exc.status_code == 403:
                    return ScreenCommand.push(ForbiddenScreen(message=f"{exc.code}: {exc.message}"))
                return ScreenCommand.push(
                    UploadConnectionErrorScreen(
                        message=f"{exc.code}: {exc.message}",
                        file_path=self.file_path.strip(),
                    )
                )
            return ScreenCommand.push(UploadResultScreen(result=payload, file_path=candidate.name))
        self.file_path += key
        return ScreenCommand.none()


@dataclass
class UploadErrorScreen:
    file_path: str
    title: str = "Upload Error"
    selected_index: int = 0

    def render(self, console: Console, state: TuiState) -> None:
        options = ("Edit file path", "Back", "Quit")
        render_breadcrumb(console, "Admin Documents", "Upload", "Error")
        render_status_line(console, "error", "file_not_found: Could not find file:")
        console.print(f"  {self.file_path or '<empty>'}")
        console.print("")
        for index, option in enumerate(options):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {option}")
        render_key_footer(console, ["Up/Down Select", "Enter Choose", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, 3)
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, 3)
            return ScreenCommand.none()
        if key == KEY_ENTER:
            if self.selected_index == 0:
                return ScreenCommand.replace(UploadDocumentScreen(file_path=self.file_path))
            if self.selected_index == 1:
                return ScreenCommand.pop()
            return ScreenCommand.quit()
        return ScreenCommand.none()


@dataclass
class UploadConnectionErrorScreen:
    message: str
    file_path: str
    selected_index: int = 0

    def render(self, console: Console, state: TuiState) -> None:
        options = ("Retry upload", "Edit file path", "Back", "Quit")
        render_breadcrumb(console, "Admin Documents", "Upload", "Error")
        render_status_line(console, "error", self.message)
        console.print(f"File: {self.file_path or '<empty>'}")
        console.print("")
        for index, option in enumerate(options):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {option}")
        render_key_footer(console, ["Up/Down Select", "Enter Choose", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, 4)
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, 4)
            return ScreenCommand.none()
        if key == KEY_ENTER:
            if self.selected_index in {0, 1}:
                return ScreenCommand.replace(UploadDocumentScreen(file_path=self.file_path))
            if self.selected_index == 2:
                return ScreenCommand.pop()
            return ScreenCommand.quit()
        return ScreenCommand.none()


@dataclass
class ForbiddenScreen:
    message: str
    title: str = "Forbidden"

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Admin Documents", "Upload", "Forbidden")
        render_status_line(console, "error", self.message)
        console.print("The backend rejected this upload request.")
        render_key_footer(console, ["B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        return ScreenCommand.none()


@dataclass
class UploadIdDetailsScreen:
    document_id: str
    job_id: str | None

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Admin Documents", "Upload", "Details")
        rows = [
            {"field": "Document ID", "value": self.document_id},
            {"field": "Job ID", "value": self.job_id or "none"},
        ]
        render_ascii_table("", rows, ["field", "value"], console=console)
        render_key_footer(console, ["B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        return ScreenCommand.none()


@dataclass
class UploadResultScreen:
    result: dict[str, Any]
    file_path: str
    title: str = "Upload Complete"
    selected_index: int = 0

    def _document(self) -> dict[str, Any]:
        document = self.result.get("document")
        if isinstance(document, dict):
            return document
        return self.result

    def _metadata(self) -> dict[str, Any]:
        metadata = self._document().get("metadata")
        if isinstance(metadata, dict):
            return metadata
        return {}

    def _lightrag_metadata(self) -> dict[str, Any]:
        payload = self._metadata().get("lightrag")
        if isinstance(payload, dict):
            return payload
        return {}

    def _status(self) -> str:
        return str(self._document().get("status", "uploaded"))

    def _job_id(self) -> str | None:
        value = self.result.get("job_id")
        return str(value) if value else None

    def _is_lightrag_forwarded(self) -> bool:
        if self._status() == "forwarded_to_lightrag":
            return True
        return bool(self._lightrag_metadata())

    def _options(self) -> list[str]:
        job_id = self._job_id()
        if job_id:
            return [
                "View job status",
                "Show full IDs",
                "Return to documents",
                "Upload another document",
                "Quit",
            ]
        if self._is_lightrag_forwarded():
            return [
                "Return to documents",
                "Show full IDs",
                "Upload another document",
                "View LightRAG labels",
                "Quit",
            ]
        return ["Return to documents", "Show full IDs", "Upload another document", "Quit"]

    def render(self, console: Console, state: TuiState) -> None:
        document = self._document()
        job_id = self._job_id()
        render_breadcrumb(console, "Admin Documents", "Upload")
        render_status_line(console, "success", "Upload complete.")
        rows: list[dict[str, str]] = [
            {"field": "File", "value": self.file_path or str(document.get("filename", ""))},
            {"field": "Document ID", "value": truncate_id(str(document.get("id", "")))},
            {"field": "Status", "value": self._status()},
        ]
        if job_id:
            rows.append({"field": "Job ID", "value": truncate_id(job_id)})
        else:
            rows.append({"field": "Local job ID", "value": "none"})
        render_ascii_table("", rows, ["field", "value"], console=console)
        options = self._options()
        for index, option in enumerate(options):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {option}")
        render_key_footer(console, ["Up/Down Select", "Enter Choose", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        options = self._options()
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, len(options))
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, len(options))
            return ScreenCommand.none()
        if key != KEY_ENTER:
            return ScreenCommand.none()

        selected = options[self.selected_index]
        if selected == "View job status":
            job_id = self._job_id()
            if job_id:
                return ScreenCommand.push(
                    ApiResultScreen(
                        "Job Status",
                        f"/jobs/{job_id}",
                        build_job_status_screen,
                        breadcrumb_trail=("Jobs", "Status"),
                    )
                )
            return ScreenCommand.none()
        if selected == "Show full IDs":
            return ScreenCommand.push(
                UploadIdDetailsScreen(
                    document_id=str(self._document().get("id", "")),
                    job_id=self._job_id(),
                )
            )
        if selected == "Return to documents":
            return ScreenCommand.replace(DocumentsScreen())
        if selected == "Upload another document":
            return ScreenCommand.replace(UploadDocumentScreen())
        if selected == "View LightRAG labels":
            return ScreenCommand.push(lightrag_screen())
        return ScreenCommand.quit()


@dataclass
class RetrievalPromptScreen:
    title: str = "Retrieval"
    query: str = ""
    mode: str = "auto"
    top_k: int = 8
    document_filter: str = "none"
    message: str | None = None
    _modes: tuple[str, ...] = ("auto", "semantic", "navigation", "hybrid")

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Retrieval", "Context")
        if self.message:
            render_status_line(console, "warn", self.message)
        console.print(f"Query: [{self.query}]")
        console.print(f"Mode: {self.mode}")
        console.print(f"Top K: {self.top_k}")
        console.print(f"Document filter: {self.document_filter}")
        render_key_footer(console, ["M Mode", "K Top K", "Enter Retrieve", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key in {"m", "M"}:
            index = self._modes.index(self.mode)
            self.mode = self._modes[(index + 1) % len(self._modes)]
            return ScreenCommand.none()
        if key in {"k", "K"}:
            self.top_k = 12 if self.top_k >= 12 else self.top_k + 1
            return ScreenCommand.none()
        if key == KEY_ENTER:
            if not self.query:
                self.message = "Query is required."
                return ScreenCommand.none()
            payload = build_query_payload(
                query=self.query,
                mode=self.mode,  # type: ignore[arg-type]
                top_k=self.top_k,
                include_debug=False,
                allow_general_fallback=False,
            )
            try:
                result = _client(state).post("/query/retrieve", payload)
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}"))
            return ScreenCommand.push(
                RetrievalResultScreen(result, query=self.query, mode=self.mode, top_k=self.top_k)
            )
        self.query += key
        return ScreenCommand.none()


@dataclass
class RetrievalResultScreen:
    payload: dict[str, Any]
    query: str
    mode: str
    top_k: int
    title: str = "Retrieval Result"
    selected_index: int = 0

    def _options(self) -> tuple[str, ...]:
        return ("Generate answer", "Compare modes", "Back", "Quit")

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Retrieval", "Context")
        render_screen_result(build_retrieval_screen(self.payload), console=console, show_title=False)
        console.print("")
        for index, option in enumerate(self._options()):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {option}")
        render_key_footer(console, ["Up/Down Select", "Enter Choose", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, len(self._options()))
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, len(self._options()))
            return ScreenCommand.none()
        if key != KEY_ENTER:
            return ScreenCommand.none()
        selected = self._options()[self.selected_index]
        if selected == "Generate answer":
            payload = build_query_payload(
                query=self.query,
                mode=self.mode,  # type: ignore[arg-type]
                top_k=self.top_k,
                include_debug=False,
                allow_general_fallback=False,
            )
            try:
                answer = _client(state).post("/query/answer", payload)
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}"))
            return ScreenCommand.push(AnswerResultScreen(payload=answer))
        if selected == "Compare modes":
            comparison = compare_retrieval_modes(_client(state), query=self.query, top_k=self.top_k)
            return ScreenCommand.push(RetrievalCompareResultScreen(payload=comparison))
        if selected == "Back":
            return ScreenCommand.pop()
        if selected == "Quit":
            return ScreenCommand.quit()
        return ScreenCommand.none()


@dataclass
class AnswerResultScreen:
    payload: dict[str, Any]

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Retrieval", "Answer")
        render_screen_result(build_answer_screen(self.payload), console=console, show_title=False)
        render_key_footer(console, ["B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        return ScreenCommand.none()


@dataclass
class RetrievalCompareResultScreen:
    payload: dict[str, Any]

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Retrieval", "Compare Modes")
        render_screen_result(build_retrieval_compare_screen(self.payload), console=console, show_title=False)
        render_key_footer(console, ["B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        return ScreenCommand.none()


@dataclass
class ObservabilityScreen:
    title: str = "Observability"
    query_logs: list[dict[str, Any]] | None = None
    audit_logs: list[dict[str, Any]] | None = None
    errors: list[str] = field(default_factory=list)

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Observability")
        try:
            if self.query_logs is None:
                self.query_logs = _client(state).get("/admin/query-logs")
            render_screen_result(build_query_logs_screen(self.query_logs), console=console, show_title=False)
        except ApiClientError as exc:
            self.errors.append(f"{exc.code}: {exc.message}")
        try:
            if self.audit_logs is None:
                self.audit_logs = _client(state).get("/admin/audit-logs")
            console.print("")
            render_screen_result(build_audit_logs_screen(self.audit_logs), console=console, show_title=False)
        except ApiClientError as exc:
            self.errors.append(f"{exc.code}: {exc.message}")
        for error in self.errors:
            render_status_line(console, "error", error)
        render_key_footer(console, ["Ctrl+R Refresh", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            self.query_logs = None
            self.audit_logs = None
            self.errors = []
            return ScreenCommand.none()
        return ScreenCommand.none()


def lightrag_screen() -> ApiResultScreen:
    return ApiResultScreen(
        title="LightRAG Graphs",
        path="/graph/label/popular?limit=20",
        builder=lambda payload: build_labels_screen(payload, title="Popular Labels"),
        breadcrumb_trail=("LightRAG", "Labels"),
    )


def admin_documents_screen() -> ApiResultScreen:
    return ApiResultScreen(
        "Admin Documents",
        "/admin/documents",
        build_admin_documents_screen,
        breadcrumb_trail=("Admin Documents",),
    )


def jobs_screen() -> ApiResultScreen:
    return ApiResultScreen("Jobs", "/jobs", build_jobs_screen, breadcrumb_trail=("Jobs",))
