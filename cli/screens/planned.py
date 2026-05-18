"""Screen builders for backend gaps."""

from __future__ import annotations

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


PLANNED_GAPS = [
    "context-engine chat",
    "context-engine users list",
    "context-engine conversations list",
    "context-engine messages list",
    "context-engine runs status",
    "context-engine runs approvals list",
    "context-engine admin corpus publish",
    "context-engine admin corpus rollback",
    "context-engine admin corpus cleanup",
]

GAP_DETAILS = {
    "context-engine users create": ("user creation", "none", "POST /users"),
    "context-engine users list": ("user listing", "none", "GET /users"),
    "context-engine retrievers list": ("retriever registry", "none", "GET /retrievers"),
    "context-engine agents list": ("agent registry", "none", "GET /agents"),
    "context-engine conversations list": ("conversation history", "none", "GET /conversations"),
    "context-engine conversations create": ("conversation creation", "none", "POST /conversations"),
    "context-engine conversations show": ("conversation detail", "none", "GET /conversations/{conversation_id}"),
    "context-engine chat": ("interactive chat", "none", "POST /chat or /messages"),
    "context-engine messages send": ("send conversation message", "none", "POST /messages"),
    "context-engine messages list": ("conversation messages", "none", "GET /messages"),
    "context-engine runs status": ("agent run status", "none", "GET /runs/{run_id}"),
    "context-engine runs cancel": ("agent run cancellation", "none", "POST /runs/{run_id}/cancel"),
    "context-engine runs approvals list": ("human approval queue", "none", "GET /runs/approvals"),
    "context-engine runs approvals approve": ("approve run action", "none", "POST /runs/approvals/{approval_id}/approve"),
    "context-engine runs approvals reject": ("reject run action", "none", "POST /runs/approvals/{approval_id}/reject"),
    "context-engine admin corpus publish": ("corpus version publish", "none", "POST /admin/corpus/publish"),
    "context-engine admin corpus rollback": ("corpus version rollback", "none", "POST /admin/corpus/rollback"),
    "context-engine admin corpus cleanup": ("corpus cleanup", "none", "POST /admin/corpus/cleanup"),
    "context-engine documents content": (
        "page range content",
        "none",
        "GET /documents/{document_id}/content?pages=",
    ),
    "context-engine documents search": ("document text search", "none", "GET /documents/search?q="),
}


def backend_gap_message(command: str) -> str:
    return f"`{command}` needs a backend route first."


def build_backend_gap_screen(command: str) -> ScreenResult:
    detail_key = _detail_key(command)
    capability, current_route, suggested_api = GAP_DETAILS.get(
        detail_key,
        ("planned CLI/API surface", "none", "backend route required"),
    )
    return ScreenResult(
        title="Backend Gap",
        api_group="gaps",
        summary={"code": "not_supported_by_backend", "command": command},
        sections=[
            ScreenSection(title="not_supported_by_backend", text=backend_gap_message(command)),
            ScreenSection(
                title="Reason",
                rows=[
                    {"field": "Capability", "value": capability},
                    {"field": "Current route", "value": current_route},
                    {"field": "Suggested API", "value": suggested_api},
                ],
                columns=["field", "value"],
            ),
        ],
        actions=[
            ScreenAction(
                "Implement backend route",
                "docs/cli_docs/api-contract.md",
                disabled=True,
                reason="not_supported_by_backend",
            )
        ],
        raw={"code": "not_supported_by_backend", "message": backend_gap_message(command)},
    )


def build_backend_gaps_screen() -> ScreenResult:
    return ScreenResult(
        title="Backend Gaps",
        api_group="gaps",
        sections=[
            ScreenSection(
                title="Planned Unsupported Surfaces",
                rows=[{"command": command, "status": "not_supported_by_backend"} for command in PLANNED_GAPS],
                columns=["command", "status"],
            )
        ],
        raw=PLANNED_GAPS,
    )


def _detail_key(command: str) -> str:
    if command.startswith("context-engine admin corpus publish"):
        return "context-engine admin corpus publish"
    if command.startswith("context-engine admin corpus rollback"):
        return "context-engine admin corpus rollback"
    if command.startswith("context-engine documents content"):
        return "context-engine documents content"
    if command.startswith("context-engine documents search"):
        return "context-engine documents search"
    return command
