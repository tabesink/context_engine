"""Domain content screens for the TUI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from rich.console import Console

from cli.api_client import ApiClientError
from cli.flows.retrieval_compare import build_retrieval_compare_screen, compare_retrieval_modes
from cli.renderers.tables import render_ascii_table
from cli.renderers.base import render_screen_result
from cli.screens.admin_documents import build_admin_documents_screen
from cli.screens.documents import build_document_detail_screen, build_document_structure_screen
from cli.screens.jobs import build_job_status_screen, build_jobs_screen
from cli.screens.lightrag import build_labels_screen
from cli.screens.lightrag_domains import build_lightrag_domains_screen
from cli.screens.models import ScreenResult
from cli.screens.observability import build_audit_logs_screen, build_query_logs_screen
from cli.screens.planned import build_backend_gaps_screen
from cli.screens.retrieval import build_answer_screen, build_retrieval_screen
from cli.tui.keys import (
    KEY_BACK,
    KEY_BACKSPACE,
    KEY_DOWN,
    KEY_ENTER,
    KEY_INSPECT,
    KEY_QUIT,
    KEY_RAW_JSON,
    KEY_REFRESH,
    KEY_TAB,
    KEY_TOGGLE_FULL_IDS,
    KEY_UP,
    KEY_UPLOAD,
    text_input_key,
)
from cli.tui.navigation import move_selection_down, move_selection_up
from cli.tui.renderers.inspect import render_inspect_view
from cli.tui.renderers.json_view import render_json_view
from cli.tui.screen import ScreenCommand
from cli.tui.state import TuiState
from cli.tui.styles import (
    render_api_footer,
    render_breadcrumb,
    render_key_footer,
    render_status_line,
    truncate_id,
)

ScreenBuilder = Callable[[Any], ScreenResult]
PayloadFetcher = Callable[[TuiState], Any]


def _last_request(state: TuiState) -> Any:
    return getattr(state.get_client(), "last_request", None)


def _metadata_route(metadata: Any) -> tuple[str | None, str | None, int | None, int | None]:
    if metadata is None:
        return None, None, None, None
    return (
        getattr(metadata, "method", None),
        getattr(metadata, "route", None),
        getattr(metadata, "status_code", None),
        getattr(metadata, "elapsed_ms", None),
    )


@dataclass
class PayloadViewScreen:
    title: str
    payload: Any
    breadcrumb_trail: tuple[str, ...]
    view: str = "raw"
    metadata: Any = None
    request_payload: Any = None
    selected_ids: dict[str, Any] | None = None
    full_ids: bool = True

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, *self.breadcrumb_trail)
        if self.view == "inspect":
            render_inspect_view(
                console,
                metadata=self.metadata,
                request_payload=self.request_payload,
                response_payload=self.payload,
                selected_ids=self.selected_ids,
            )
        else:
            render_json_view(console, self.payload, full_ids=self.full_ids)
        render_key_footer(console, ["B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        return ScreenCommand.none()


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
    builder: ScreenBuilder
    fetcher: PayloadFetcher
    payload: Any | None = None
    breadcrumb_trail: tuple[str, ...] = ()
    full_ids: bool = False

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
        metadata = None
        try:
            if self.payload is None:
                self.payload = self.fetcher(state)
            metadata = _last_request(state)
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
            metadata = _last_request(state)
        method, route, status_code, elapsed_ms = _metadata_route(metadata)
        render_api_footer(console, method=method, route=route, status_code=status_code, elapsed_ms=elapsed_ms)

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            self.payload = None
            return ScreenCommand.none()
        if key == KEY_TOGGLE_FULL_IDS:
            self.full_ids = not self.full_ids
            return ScreenCommand.none()
        if key == KEY_RAW_JSON:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title=f"{self.title} Raw JSON",
                    payload=self.payload,
                    breadcrumb_trail=(*(self.breadcrumb_trail or (self.title,)), "Raw JSON"),
                    view="raw",
                    full_ids=True,
                )
            )
        if key == KEY_INSPECT:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title=f"{self.title} Inspect API",
                    payload=self.payload,
                    breadcrumb_trail=(*(self.breadcrumb_trail or (self.title,)), "Inspect API"),
                    view="inspect",
                    metadata=_last_request(state),
                )
            )
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

    @staticmethod
    def _is_admin(state: TuiState) -> bool:
        return (state.user_role or "").lower() == "admin"

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Documents", "Library")
        is_admin = self._is_admin(state)
        try:
            if self.documents is None:
                self.documents = state.document_service().list_documents()
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
                if is_admin:
                    console.print("")
                    console.print("Admin Actions: press A")
                render_key_footer(
                    console,
                    ["Up/Down Select document", "Enter Open", "A Admin actions", "Ctrl+R Refresh", "B Back", "Q Quit"]
                    if is_admin
                    else ["Up/Down Select document", "Enter Open", "Ctrl+R Refresh", "B Back", "Q Quit"],
                )
            else:
                actions = ("Admin Actions", "Refresh", "Back", "Quit") if is_admin else ("Refresh", "Back", "Quit")
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
                action_count = 4 if self._is_admin(state) else 3
                self.empty_action_index = move_selection_up(self.empty_action_index, action_count)
            return ScreenCommand.none()
        if key == KEY_DOWN:
            if count:
                self.selected_index = move_selection_down(self.selected_index, count)
            else:
                action_count = 4 if self._is_admin(state) else 3
                self.empty_action_index = move_selection_down(self.empty_action_index, action_count)
            return ScreenCommand.none()
        if key in {"a", "A"} and self._is_admin(state):
            return ScreenCommand.push(DocumentsAdminActionsScreen())
        if key in {KEY_UPLOAD, "u", "U"} and self._is_admin(state):
            return ScreenCommand.push(UploadDocumentScreen())
        if key == KEY_ENTER:
            if self.documents:
                document_id = str(self.documents[self.selected_index].get("id", ""))
                if document_id:
                    return ScreenCommand.push(DocumentDetailScreen(document_id=document_id))
                return ScreenCommand.none()
            is_admin = self._is_admin(state)
            if is_admin and self.empty_action_index == 0:
                return ScreenCommand.push(DocumentsAdminActionsScreen())
            refresh_index = 1 if is_admin else 0
            back_index = 2 if is_admin else 1
            quit_index = 3 if is_admin else 2
            if self.empty_action_index == refresh_index:
                self.documents = None
                self.selected_index = 0
                self.empty_action_index = 0
                return ScreenCommand.none()
            if self.empty_action_index == back_index:
                return ScreenCommand.pop()
            if self.empty_action_index == quit_index:
                return ScreenCommand.quit()
            return ScreenCommand.quit()
        return ScreenCommand.none()


@dataclass
class DocumentDetailScreen:
    document_id: str
    title: str = "Document Detail"
    document: dict[str, Any] | None = None
    structure_quality: dict[str, Any] | None = None
    toc_refinement_report: dict[str, Any] | None = None

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Documents", "Detail")
        try:
            if self.document is None:
                self.document = state.document_service().get_document(self.document_id)
            if self.structure_quality is None:
                self.structure_quality = self._load_structure_quality(state)
            if self.toc_refinement_report is None:
                self.toc_refinement_report = self._load_toc_refinement_report(state)
            render_screen_result(
                build_document_detail_screen(
                    self.document,
                    structure_quality=self.structure_quality,
                    toc_refinement_report=self.toc_refinement_report,
                ),
                console=console,
                show_title=False,
            )
        except ApiClientError as exc:
            render_status_line(console, "error", f"{exc.code}: {exc.message}")
        render_key_footer(console, ["Ctrl+R Refresh", "B Back", "Q Quit"])

    def _load_structure_quality(self, state: TuiState) -> dict[str, Any]:
        try:
            return state.document_service().get_structure_quality(self.document_id)
        except ApiClientError:
            return {}

    def _load_toc_refinement_report(self, state: TuiState) -> dict[str, Any]:
        try:
            return state.document_service().get_toc_refinement_report(self.document_id)
        except ApiClientError:
            return {}

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            self.document = None
            self.structure_quality = None
            self.toc_refinement_report = None
            return ScreenCommand.none()
        if key == KEY_ENTER:
            return ScreenCommand.push(
                ApiResultScreen(
                    "Document Structure",
                    build_document_structure_screen,
                    lambda s: s.document_service().get_structure(
                        self.document_id,
                        include_blocks=True,
                        include_assets=True,
                    ),
                    breadcrumb_trail=("Documents", "Detail", "Structure"),
                )
            )
        return ScreenCommand.none()


@dataclass
class AdminDocumentMutationResultScreen:
    title: str
    message: str
    payload: dict[str, Any]

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Documents", "Admin Actions", self.title)
        render_status_line(console, "success", self.message)
        rows = [{"field": str(key), "value": str(value)} for key, value in self.payload.items()]
        if rows:
            render_ascii_table("", rows, ["field", "value"], console=console)
        render_key_footer(console, ["B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        return ScreenCommand.none()


@dataclass
class AdminDocumentMutationScreen:
    title: str
    method_name: str
    success_message: str
    document_id: str = ""
    message: str | None = None

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Documents", "Admin Actions", self.title)
        if self.message:
            render_status_line(console, "error", self.message)
        console.print(f"> Document ID: [ {self.document_id} ]")
        render_key_footer(console, ["Enter Submit", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_BACKSPACE:
            self.document_id = self.document_id[:-1]
            return ScreenCommand.none()
        if key == KEY_ENTER:
            document_id = self.document_id.strip()
            if not document_id:
                self.message = "Document ID is required."
                return ScreenCommand.none()
            try:
                service = state.admin_document_service()
                payload = getattr(service, self.method_name)(document_id)
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}", title=f"Documents / Admin Actions / {self.title}"))
            return ScreenCommand.push(AdminDocumentMutationResultScreen(self.title, self.success_message, payload))
        self.document_id += text_input_key(key)
        return ScreenCommand.none()


@dataclass
class DocumentsAdminActionsScreen:
    selected_index: int = 0

    def _options(self) -> tuple[str, ...]:
        return (
            "Upload Document",
            "List All Documents",
            "Index Document",
            "Reindex Document",
            "Delete Document",
            "Back",
        )

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Documents", "Admin Actions")
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
        if selected == "Upload Document":
            return ScreenCommand.push(UploadDocumentScreen())
        if selected == "List All Documents":
            return ScreenCommand.push(admin_documents_screen())
        if selected == "Index Document":
            return ScreenCommand.push(AdminDocumentMutationScreen("Index Document", "index_document", "Index submitted."))
        if selected == "Reindex Document":
            return ScreenCommand.push(AdminDocumentMutationScreen("Reindex Document", "reindex_document", "Reindex submitted."))
        if selected == "Delete Document":
            return ScreenCommand.push(AdminDocumentMutationScreen("Delete Document", "delete_document", "Delete submitted."))
        return ScreenCommand.pop()


@dataclass
class UploadDocumentScreen:
    title: str = "Upload Document"
    file_path: str = ""

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Documents", "Admin Actions", "Upload")
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
                payload = state.admin_document_service().upload_document(
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
        self.file_path += text_input_key(key)
        return ScreenCommand.none()


@dataclass
class UploadErrorScreen:
    file_path: str
    title: str = "Upload Error"
    selected_index: int = 0

    def render(self, console: Console, state: TuiState) -> None:
        options = ("Edit file path", "Back", "Quit")
        render_breadcrumb(console, "Documents", "Admin Actions", "Upload", "Error")
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
        render_breadcrumb(console, "Documents", "Admin Actions", "Upload", "Error")
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
        render_breadcrumb(console, "Documents", "Admin Actions", "Upload", "Forbidden")
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
        render_breadcrumb(console, "Documents", "Admin Actions", "Upload", "Details")
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
    full_ids: bool = False

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
        render_breadcrumb(console, "Documents", "Admin Actions", "Upload")
        render_status_line(console, "success", "Upload complete.")
        rows: list[dict[str, str]] = [
            {"field": "File", "value": self.file_path or str(document.get("filename", ""))},
            {
                "field": "Document ID",
                "value": str(document.get("id", "")) if self.full_ids else truncate_id(str(document.get("id", ""))),
            },
            {"field": "Status", "value": self._status()},
        ]
        if job_id:
            rows.append({"field": "Job ID", "value": job_id if self.full_ids else truncate_id(job_id)})
        else:
            rows.append({"field": "Local job ID", "value": "none"})
        render_ascii_table("", rows, ["field", "value"], console=console)
        options = self._options()
        for index, option in enumerate(options):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {option}")
        method, route, status_code, elapsed_ms = _metadata_route(_last_request(state))
        if method and route:
            console.print("")
            console.print(f"Route: {method} {route}    Status: {status_code or 'unknown'}    Time: {elapsed_ms if elapsed_ms is not None else 'unknown'} ms")
        render_key_footer(
            console,
            ["Up/Down Select", "Enter Choose", "I Inspect API", "J Raw JSON", "F Toggle full IDs", "B Back", "Q Quit"],
        )

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        options = self._options()
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_TOGGLE_FULL_IDS:
            self.full_ids = not self.full_ids
            return ScreenCommand.none()
        if key == KEY_RAW_JSON:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Upload Raw JSON",
                    payload=self.result,
                    breadcrumb_trail=("Documents", "Admin Actions", "Upload", "Raw JSON"),
                    view="raw",
                    full_ids=True,
                )
            )
        if key == KEY_INSPECT:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Upload Inspect API",
                    payload=self.result,
                    breadcrumb_trail=("Documents", "Admin Actions", "Upload", "Inspect API"),
                    view="inspect",
                    metadata=_last_request(state),
                    selected_ids={"document_id": self._document().get("id"), "job_id": self._job_id()},
                )
            )
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
                        build_job_status_screen,
                        lambda s: s.job_service().get_job(job_id),
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
    lightrag_domain_id: str | None = None
    lightrag_domains: list[dict[str, Any]] | None = None
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
        try:
            if self.lightrag_domains is None:
                payload = state.lightrag_domain_service().list_user_domains()
                self.lightrag_domains = payload.get("domains", [])
            domain_label = self.lightrag_domain_id or self._default_domain_label()
            console.print(f"LightRAG domain: {domain_label}")
        except ApiClientError as exc:
            render_status_line(console, "warn", f"{exc.code}: {exc.message}")
            console.print("LightRAG domain: default")
        render_key_footer(console, ["M Mode", "K Top K", "Tab Domain", "Enter Retrieve", "B Back", "Q Quit"])

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
        if key == KEY_TAB:
            self._cycle_domain()
            return ScreenCommand.none()
        if key == KEY_ENTER:
            if not self.query:
                self.message = "Query is required."
                return ScreenCommand.none()
            try:
                result = state.retrieval_service().retrieve(
                    query=self.query,
                    mode=self.mode,  # type: ignore[arg-type]
                    top_k=self.top_k,
                    lightrag_domain_id=self.lightrag_domain_id,
                )
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}"))
            return ScreenCommand.push(
                RetrievalResultScreen(
                    result,
                    query=self.query,
                    mode=self.mode,
                    top_k=self.top_k,
                    lightrag_domain_id=self.lightrag_domain_id,
                )
            )
        self.query += text_input_key(key)
        return ScreenCommand.none()

    def _default_domain_label(self) -> str:
        domains = self.lightrag_domains or []
        default = next((domain for domain in domains if domain.get("is_default")), None)
        return str(default.get("id")) if isinstance(default, dict) and default.get("id") else "default"

    def _cycle_domain(self) -> None:
        domains = [str(domain.get("id")) for domain in self.lightrag_domains or [] if domain.get("id")]
        if not domains:
            self.lightrag_domain_id = None
            return
        current = self.lightrag_domain_id or domains[0]
        index = domains.index(current) if current in domains else 0
        self.lightrag_domain_id = domains[(index + 1) % len(domains)]


@dataclass
class RetrievalResultScreen:
    payload: dict[str, Any]
    query: str
    mode: str
    top_k: int
    lightrag_domain_id: str | None = None
    title: str = "Retrieval Result"
    selected_index: int = 0
    full_ids: bool = False

    def _options(self) -> tuple[str, ...]:
        return ("Generate answer", "Compare modes", "Back", "Quit")

    def _request_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": self.query,
            "mode": self.mode,
            "top_k": self.top_k,
            "include_debug": False,
        }
        if self.lightrag_domain_id:
            payload["lightrag_domain_id"] = self.lightrag_domain_id
        return payload

    def _display_payload(self) -> dict[str, Any]:
        payload = dict(self.payload)
        payload.update(self._request_payload())
        payload.setdefault("document_filter", "none")
        payload.setdefault("lightrag_domain_id", self.lightrag_domain_id or "default")
        return payload

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Retrieval", "Context")
        render_screen_result(build_retrieval_screen(self._display_payload()), console=console, show_title=False)
        console.print("")
        for index, option in enumerate(self._options()):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {option}")
        method, route, status_code, elapsed_ms = _metadata_route(_last_request(state))
        render_api_footer(console, method=method, route=route, status_code=status_code, elapsed_ms=elapsed_ms)

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_TOGGLE_FULL_IDS:
            self.full_ids = not self.full_ids
            return ScreenCommand.none()
        if key == KEY_RAW_JSON:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Retrieval Raw JSON",
                    payload=self.payload,
                    breadcrumb_trail=("Retrieval", "Context", "Raw JSON"),
                    view="raw",
                    full_ids=True,
                )
            )
        if key == KEY_INSPECT:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Retrieval Inspect API",
                    payload=self.payload,
                    breadcrumb_trail=("Retrieval", "Context", "Inspect API"),
                    view="inspect",
                    metadata=_last_request(state),
                    request_payload=self._request_payload(),
                    selected_ids={"document_filter": "none", "lightrag_domain_id": self.lightrag_domain_id or "default"},
                )
            )
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
            try:
                answer = state.retrieval_service().answer(
                    query=self.query,
                    mode=self.mode,  # type: ignore[arg-type]
                    top_k=self.top_k,
                    lightrag_domain_id=self.lightrag_domain_id,
                )
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}"))
            return ScreenCommand.push(AnswerResultScreen(payload=answer))
        if selected == "Compare modes":
            comparison = compare_retrieval_modes(state.get_client(), query=self.query, top_k=self.top_k)
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
        method, route, status_code, elapsed_ms = _metadata_route(_last_request(state))
        render_api_footer(console, method=method, route=route, status_code=status_code, elapsed_ms=elapsed_ms)

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_RAW_JSON:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Answer Raw JSON",
                    payload=self.payload,
                    breadcrumb_trail=("Retrieval", "Answer", "Raw JSON"),
                    view="raw",
                )
            )
        if key == KEY_INSPECT:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Answer Inspect API",
                    payload=self.payload,
                    breadcrumb_trail=("Retrieval", "Answer", "Inspect API"),
                    view="inspect",
                    metadata=_last_request(state),
                )
            )
        return ScreenCommand.none()


@dataclass
class RetrievalCompareResultScreen:
    payload: dict[str, Any]

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Retrieval", "Compare Modes")
        render_screen_result(build_retrieval_compare_screen(self.payload), console=console, show_title=False)
        render_key_footer(console, ["J Raw JSON", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_RAW_JSON:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Compare Raw JSON",
                    payload=self.payload,
                    breadcrumb_trail=("Retrieval", "Compare Modes", "Raw JSON"),
                    view="raw",
                )
            )
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
                self.query_logs = state.observability_service().query_logs()
            render_screen_result(build_query_logs_screen(self.query_logs), console=console, show_title=False)
        except ApiClientError as exc:
            self.errors.append(f"{exc.code}: {exc.message}")
        try:
            if self.audit_logs is None:
                self.audit_logs = state.observability_service().audit_logs()
            console.print("")
            render_screen_result(build_audit_logs_screen(self.audit_logs), console=console, show_title=False)
        except ApiClientError as exc:
            self.errors.append(f"{exc.code}: {exc.message}")
        for error in self.errors:
            render_status_line(console, "error", error)
        method, route, status_code, elapsed_ms = _metadata_route(_last_request(state))
        render_api_footer(console, method=method, route=route, status_code=status_code, elapsed_ms=elapsed_ms)

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
        if key == KEY_RAW_JSON:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Observability Raw JSON",
                    payload={"query_logs": self.query_logs, "audit_logs": self.audit_logs},
                    breadcrumb_trail=("Observability", "Raw JSON"),
                    view="raw",
                )
            )
        if key == KEY_INSPECT:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Observability Inspect API",
                    payload={"query_logs": self.query_logs, "audit_logs": self.audit_logs},
                    breadcrumb_trail=("Observability", "Inspect API"),
                    view="inspect",
                    metadata=_last_request(state),
                )
            )
        return ScreenCommand.none()


def lightrag_screen() -> ApiResultScreen:
    return ApiResultScreen(
        title="Graphs",
        builder=lambda payload: build_labels_screen(payload, title="Popular Labels"),
        fetcher=lambda state: state.lightrag_service().popular_labels(limit=20),
        breadcrumb_trail=("Graphs", "Labels"),
    )


@dataclass
class LightRAGDomainsScreen:
    title: str = "LightRAG Domains"
    domains_payload: dict[str, Any] | None = None
    selected_index: int = 0

    def _actions(self) -> tuple[str, ...]:
        return (
            "List Domains",
            "Create Domain",
            "Show Domain Detail",
            "Start Domain",
            "Stop Domain",
            "Recreate Domain",
            "Regenerate Domain Files",
            "Archive Remove Domain",
            "Permanent Delete Domain",
            "Back",
        )

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "LightRAG", "Domains")
        try:
            if self.domains_payload is None:
                self.domains_payload = state.lightrag_domain_service().list_admin_domains()
            render_screen_result(build_lightrag_domains_screen(self.domains_payload), console=console, show_title=False)
        except ApiClientError as exc:
            render_status_line(console, "error", f"{exc.code}: {exc.message}")
        console.print("")
        for index, action in enumerate(self._actions()):
            marker = ">" if index == self.selected_index else " "
            console.print(f"{marker} {action}")
        render_key_footer(console, ["Up/Down Select", "Enter Choose", "Ctrl+R Refresh", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            self.domains_payload = None
            return ScreenCommand.none()
        if key == KEY_UP:
            self.selected_index = move_selection_up(self.selected_index, len(self._actions()))
            return ScreenCommand.none()
        if key == KEY_DOWN:
            self.selected_index = move_selection_down(self.selected_index, len(self._actions()))
            return ScreenCommand.none()
        if key != KEY_ENTER:
            return ScreenCommand.none()
        selected = self._actions()[self.selected_index]
        if selected == "List Domains":
            self.domains_payload = None
            return ScreenCommand.none()
        if selected == "Create Domain":
            return ScreenCommand.push(create_lightrag_domain_screen())
        if selected == "Show Domain Detail":
            return ScreenCommand.push(show_lightrag_domain_screen())
        if selected == "Start Domain":
            return ScreenCommand.push(start_lightrag_domain_screen())
        if selected == "Stop Domain":
            return ScreenCommand.push(stop_lightrag_domain_screen())
        if selected == "Recreate Domain":
            return ScreenCommand.push(recreate_lightrag_domain_screen())
        if selected == "Regenerate Domain Files":
            return ScreenCommand.push(regenerate_lightrag_domain_screen())
        if selected == "Archive Remove Domain":
            return ScreenCommand.push(remove_lightrag_domain_screen())
        if selected == "Permanent Delete Domain":
            return ScreenCommand.push(remove_lightrag_domain_screen(permanent_default=True))
        return ScreenCommand.pop()


def lightrag_domains_screen() -> LightRAGDomainsScreen:
    return LightRAGDomainsScreen()


@dataclass
class CreateLightRAGDomainScreen:
    title: str = "Create LightRAG Domain"
    domain_id: str = ""
    display_name: str = ""
    host_port: str = ""
    make_default: str = "n"
    active_field: int = 0
    message: str | None = None

    def _fields(self) -> tuple[tuple[str, str], ...]:
        return (
            ("Domain ID", self.domain_id),
            ("Display name", self.display_name),
            ("Host port", self.host_port),
            ("Make default", self.make_default),
        )

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "LightRAG", "Domains", "Create")
        if self.message:
            render_status_line(console, "error", self.message)
        for index, (label, value) in enumerate(self._fields()):
            marker = ">" if index == self.active_field else " "
            hint = " (y/N)" if label == "Make default" else ""
            console.print(f"{marker} {label}{hint}: [ {value} ]")
        render_key_footer(console, ["Tab Next field", "Enter Create", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_TAB:
            self.active_field = (self.active_field + 1) % len(self._fields())
            return ScreenCommand.none()
        if key == KEY_BACKSPACE:
            self._set_active_value(self._active_value()[:-1])
            return ScreenCommand.none()
        if key == KEY_ENTER:
            payload = self._payload()
            if payload is None:
                return ScreenCommand.none()
            try:
                result = state.lightrag_domain_service().create_domain(payload)
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}", title="LightRAG / Domains / Create"))
            return ScreenCommand.push(
                LightRAGDomainResultScreen(
                    breadcrumb_trail=("LightRAG", "Domains", "Create"),
                    message="Domain created.",
                    payload=result,
                )
            )
        self._set_active_value(self._active_value() + text_input_key(key))
        return ScreenCommand.none()

    def _active_value(self) -> str:
        if self.active_field == 0:
            return self.domain_id
        if self.active_field == 1:
            return self.display_name
        if self.active_field == 2:
            return self.host_port
        return self.make_default

    def _set_active_value(self, value: str) -> None:
        if self.active_field == 0:
            self.domain_id = value
        elif self.active_field == 1:
            self.display_name = value
        elif self.active_field == 2:
            self.host_port = value
        else:
            self.make_default = value[-1:] if value else ""

    def _payload(self) -> dict[str, Any] | None:
        domain_id = self.domain_id.strip()
        if not domain_id:
            self.message = "Domain ID is required."
            return None
        payload: dict[str, Any] = {"domain_id": domain_id}
        display_name = self.display_name.strip()
        if display_name:
            payload["display_name"] = display_name
        port = self.host_port.strip()
        if port:
            try:
                payload["host_port"] = int(port)
            except ValueError:
                self.message = "Host port must be a number."
                return None
        payload["make_default"] = self.make_default.strip().lower() in {"1", "true", "y", "yes"}
        self.message = None
        return payload


@dataclass
class LightRAGDomainOperationScreen:
    title: str
    operation: str
    service_method: str
    confirmation_word: str | None = None
    domain_id: str = ""
    confirmation: str = ""
    active_field: int = 0
    message: str | None = None

    def _fields(self) -> tuple[tuple[str, str], ...]:
        if self.confirmation_word:
            return (("Domain ID", self.domain_id), ("Confirmation", self.confirmation))
        return (("Domain ID", self.domain_id),)

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "LightRAG", "Domains", self.title)
        if self.message:
            render_status_line(console, "error", self.message)
        if self.confirmation_word:
            console.print(f"Type {self.confirmation_word} to confirm.")
            console.print("")
        for index, (label, value) in enumerate(self._fields()):
            marker = ">" if index == self.active_field else " "
            console.print(f"{marker} {label}: [ {value} ]")
        render_key_footer(console, ["Tab Next field", f"Enter {self.title}", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_TAB:
            self.active_field = (self.active_field + 1) % len(self._fields())
            return ScreenCommand.none()
        if key == KEY_BACKSPACE:
            self._set_active_value(self._active_value()[:-1])
            return ScreenCommand.none()
        if key == KEY_ENTER:
            domain_id = self.domain_id.strip()
            if not domain_id:
                self.message = "Domain ID is required."
                return ScreenCommand.none()
            if self.confirmation_word and self.confirmation.strip() != self.confirmation_word:
                self.message = f"Type {self.confirmation_word} to confirm."
                return ScreenCommand.none()
            try:
                service = state.lightrag_domain_service()
                result = getattr(service, self.service_method)(domain_id)
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}", title=f"LightRAG / Domains / {self.title}"))
            return ScreenCommand.push(
                LightRAGDomainResultScreen(
                    breadcrumb_trail=("LightRAG", "Domains", self.title),
                    message=f"{self.operation} {str(result.get('status', 'submitted')).lower()}.",
                    payload=result,
                )
            )
        self._set_active_value(self._active_value() + text_input_key(key))
        return ScreenCommand.none()

    def _active_value(self) -> str:
        return self.domain_id if self.active_field == 0 else self.confirmation

    def _set_active_value(self, value: str) -> None:
        if self.active_field == 0:
            self.domain_id = value
        else:
            self.confirmation = value


@dataclass
class RemoveLightRAGDomainScreen:
    title: str = "Remove LightRAG Domain"
    domain_id: str = ""
    permanent_input: str = "n"
    confirmation: str = ""
    active_field: int = 0
    message: str | None = None
    permanent_default: bool = False

    def __post_init__(self) -> None:
        if self.permanent_default:
            self.permanent_input = "y"

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "LightRAG", "Domains", "Remove")
        if self.message:
            render_status_line(console, "error", self.message)
        confirmation_word = self._confirmation_word()
        console.print(f"Type {confirmation_word} to confirm.")
        console.print("")
        fields = (
            ("Domain ID", self.domain_id),
            ("Permanent delete (y/N)", self.permanent_input),
            ("Confirmation", self.confirmation),
        )
        for index, (label, value) in enumerate(fields):
            marker = ">" if index == self.active_field else " "
            console.print(f"{marker} {label}: [ {value} ]")
        render_key_footer(console, ["Tab Next field", "Enter Remove", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_TAB:
            self.active_field = (self.active_field + 1) % 3
            return ScreenCommand.none()
        if key == KEY_BACKSPACE:
            self._set_active_value(self._active_value()[:-1])
            return ScreenCommand.none()
        if key == KEY_ENTER:
            domain_id = self.domain_id.strip()
            if not domain_id:
                self.message = "Domain ID is required."
                return ScreenCommand.none()
            if self.confirmation.strip() != self._confirmation_word():
                self.message = f"Type {self._confirmation_word()} to confirm."
                return ScreenCommand.none()
            try:
                result = state.lightrag_domain_service().remove_domain(domain_id, permanent=self._permanent())
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}", title="LightRAG / Domains / Remove"))
            message = "Domain permanently deleted." if self._permanent() else "Domain removed."
            return ScreenCommand.push(
                LightRAGDomainResultScreen(
                    breadcrumb_trail=("LightRAG", "Domains", "Remove"),
                    message=message,
                    payload=result,
                )
            )
        self._set_active_value(self._active_value() + text_input_key(key))
        return ScreenCommand.none()

    def _confirmation_word(self) -> str:
        return "PERMANENT DELETE" if self._permanent() else "REMOVE"

    def _permanent(self) -> bool:
        return self.permanent_input.strip().lower() in {"1", "true", "y", "yes"}

    def _active_value(self) -> str:
        if self.active_field == 0:
            return self.domain_id
        if self.active_field == 1:
            return self.permanent_input
        return self.confirmation

    def _set_active_value(self, value: str) -> None:
        if self.active_field == 0:
            self.domain_id = value
        elif self.active_field == 1:
            self.permanent_input = value[-1:] if value else ""
        else:
            self.confirmation = value


@dataclass
class ShowLightRAGDomainScreen:
    title: str = "Show Domain Detail"
    domain_id: str = ""
    message: str | None = None

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "LightRAG", "Domains", "Show Detail")
        if self.message:
            render_status_line(console, "error", self.message)
        console.print(f"> Domain ID: [ {self.domain_id} ]")
        render_key_footer(console, ["Enter Show detail", "B Back", "Q Quit"])

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_BACKSPACE:
            self.domain_id = self.domain_id[:-1]
            return ScreenCommand.none()
        if key == KEY_ENTER:
            domain_id = self.domain_id.strip()
            if not domain_id:
                self.message = "Domain ID is required."
                return ScreenCommand.none()
            try:
                payload = state.lightrag_domain_service().show_domain(domain_id)
            except ApiClientError as exc:
                return ScreenCommand.push(ErrorScreen(f"{exc.code}: {exc.message}", title="LightRAG / Domains / Show Detail"))
            return ScreenCommand.push(
                LightRAGDomainResultScreen(
                    breadcrumb_trail=("LightRAG", "Domains", "Show Detail"),
                    message="Domain detail loaded.",
                    payload=payload,
                )
            )
        self.domain_id += text_input_key(key)
        return ScreenCommand.none()


@dataclass
class LightRAGDomainResultScreen:
    breadcrumb_trail: tuple[str, ...]
    message: str
    payload: dict[str, Any]
    title: str = "LightRAG Domain Result"

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, *self.breadcrumb_trail)
        render_status_line(console, "success", self.message)
        rows = [{"field": key, "value": value} for key, value in self.payload.items() if value is not None]
        render_ascii_table("", rows, ["field", "value"], console=console)
        method, route, status_code, elapsed_ms = _metadata_route(_last_request(state))
        render_api_footer(console, method=method, route=route, status_code=status_code, elapsed_ms=elapsed_ms)

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_RAW_JSON:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="LightRAG Domain Raw JSON",
                    payload=self.payload,
                    breadcrumb_trail=(*self.breadcrumb_trail, "Raw JSON"),
                    view="raw",
                )
            )
        if key == KEY_INSPECT:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="LightRAG Domain Inspect API",
                    payload=self.payload,
                    breadcrumb_trail=(*self.breadcrumb_trail, "Inspect API"),
                    view="inspect",
                    metadata=_last_request(state),
                )
            )
        return ScreenCommand.none()


def create_lightrag_domain_screen() -> CreateLightRAGDomainScreen:
    return CreateLightRAGDomainScreen()


def start_lightrag_domain_screen() -> LightRAGDomainOperationScreen:
    return LightRAGDomainOperationScreen("Start", "start", "up_domain")


def stop_lightrag_domain_screen() -> LightRAGDomainOperationScreen:
    return LightRAGDomainOperationScreen("Stop", "stop", "down_domain")


def recreate_lightrag_domain_screen() -> LightRAGDomainOperationScreen:
    return LightRAGDomainOperationScreen("Recreate", "recreate", "recreate_domain", confirmation_word="RECREATE")


def regenerate_lightrag_domain_screen() -> LightRAGDomainOperationScreen:
    return LightRAGDomainOperationScreen("Regenerate", "regenerate", "regenerate_domain")


def show_lightrag_domain_screen() -> ShowLightRAGDomainScreen:
    return ShowLightRAGDomainScreen()


def remove_lightrag_domain_screen(*, permanent_default: bool = False) -> RemoveLightRAGDomainScreen:
    return RemoveLightRAGDomainScreen(permanent_default=permanent_default)


def admin_documents_screen() -> ApiResultScreen:
    return ApiResultScreen(
        "Documents Admin",
        build_admin_documents_screen,
        lambda state: state.admin_document_service().list_documents(),
        breadcrumb_trail=("Documents", "Admin Actions", "List All"),
    )


def jobs_screen() -> ApiResultScreen:
    return ApiResultScreen(
        "Jobs",
        build_jobs_screen,
        lambda state: state.job_service().list_jobs(),
        breadcrumb_trail=("Jobs",),
    )


@dataclass
class HealthScreen:
    health_payload: dict[str, Any] | None = None
    readiness_payload: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)

    def render(self, console: Console, state: TuiState) -> None:
        render_breadcrumb(console, "Health")
        service = state.health_service()
        self.errors = []
        try:
            if self.health_payload is None:
                self.health_payload = service.health()
        except ApiClientError as exc:
            self.errors.append(f"{exc.code}: {exc.message}")
        try:
            if self.readiness_payload is None:
                self.readiness_payload = service.readiness()
        except ApiClientError as exc:
            self.errors.append(f"{exc.code}: {exc.message}")

        rows: list[dict[str, str]] = [
            {
                "check": "health",
                "status": str((self.health_payload or {}).get("status", "unknown")),
                "detail": str((self.health_payload or {}).get("detail", "")),
            },
            {
                "check": "readiness",
                "status": str((self.readiness_payload or {}).get("status", "unknown")),
                "detail": str((self.readiness_payload or {}).get("detail", "")),
            },
        ]
        render_ascii_table("", rows, ["check", "status", "detail"], console=console)
        for error in self.errors:
            render_status_line(console, "error", error)
        method, route, status_code, elapsed_ms = _metadata_route(_last_request(state))
        render_api_footer(console, method=method, route=route, status_code=status_code, elapsed_ms=elapsed_ms)

    def handle_key(self, key: str, state: TuiState) -> ScreenCommand:
        if key == KEY_QUIT:
            return ScreenCommand.quit()
        if key == KEY_BACK:
            return ScreenCommand.pop()
        if key == KEY_REFRESH:
            self.health_payload = None
            self.readiness_payload = None
            self.errors = []
            return ScreenCommand.none()
        if key == KEY_RAW_JSON:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Health Raw JSON",
                    payload={"health": self.health_payload, "readiness": self.readiness_payload},
                    breadcrumb_trail=("Health", "Raw JSON"),
                    view="raw",
                )
            )
        if key == KEY_INSPECT:
            return ScreenCommand.push(
                PayloadViewScreen(
                    title="Health Inspect API",
                    payload={"health": self.health_payload, "readiness": self.readiness_payload},
                    breadcrumb_trail=("Health", "Inspect API"),
                    view="inspect",
                    metadata=_last_request(state),
                )
            )
        return ScreenCommand.none()
