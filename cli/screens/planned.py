"""Screen builders for backend gaps."""

from __future__ import annotations

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


PLANNED_GAPS = [
    "ragcli chat",
    "ragcli users list",
    "ragcli conversations list",
    "ragcli messages list",
    "ragcli runs status",
    "ragcli runs approvals list",
    "ragcli admin corpus publish",
    "ragcli admin corpus rollback",
    "ragcli admin corpus cleanup",
]

GAP_DETAILS = {
    "ragcli users create": ("user creation", "none", "POST /users"),
    "ragcli users list": ("user listing", "none", "GET /users"),
    "ragcli retrievers list": ("retriever registry", "none", "GET /retrievers"),
    "ragcli agents list": ("agent registry", "none", "GET /agents"),
    "ragcli conversations list": ("conversation history", "none", "GET /conversations"),
    "ragcli conversations create": ("conversation creation", "none", "POST /conversations"),
    "ragcli conversations show": ("conversation detail", "none", "GET /conversations/{conversation_id}"),
    "ragcli chat": ("interactive chat", "none", "POST /chat or /messages"),
    "ragcli messages send": ("send conversation message", "none", "POST /messages"),
    "ragcli messages list": ("conversation messages", "none", "GET /messages"),
    "ragcli runs status": ("agent run status", "none", "GET /runs/{run_id}"),
    "ragcli runs cancel": ("agent run cancellation", "none", "POST /runs/{run_id}/cancel"),
    "ragcli runs approvals list": ("human approval queue", "none", "GET /runs/approvals"),
    "ragcli runs approvals approve": ("approve run action", "none", "POST /runs/approvals/{approval_id}/approve"),
    "ragcli runs approvals reject": ("reject run action", "none", "POST /runs/approvals/{approval_id}/reject"),
    "ragcli admin corpus publish": ("corpus version publish", "none", "POST /admin/corpus/publish"),
    "ragcli admin corpus rollback": ("corpus version rollback", "none", "POST /admin/corpus/rollback"),
    "ragcli admin corpus cleanup": ("corpus cleanup", "none", "POST /admin/corpus/cleanup"),
    "ragcli documents content": (
        "page range content",
        "none",
        "GET /documents/{document_id}/content?pages=",
    ),
    "ragcli documents search": ("document text search", "none", "GET /documents/search?q="),
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
    if command.startswith("ragcli admin corpus publish"):
        return "ragcli admin corpus publish"
    if command.startswith("ragcli admin corpus rollback"):
        return "ragcli admin corpus rollback"
    if command.startswith("ragcli documents content"):
        return "ragcli documents content"
    if command.startswith("ragcli documents search"):
        return "ragcli documents search"
    return command
