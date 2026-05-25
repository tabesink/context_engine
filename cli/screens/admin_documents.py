"""Admin document screen builders."""

from __future__ import annotations

from typing import Any

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


def build_admin_documents_screen(documents: list[dict[str, Any]]) -> ScreenResult:
    return ScreenResult(
        title="Admin Documents",
        api_group="admin",
        sections=[
            ScreenSection(
                title="",
                rows=documents,
                columns=["id", "filename", "status", "indexed_by", "updated_at"],
            )
        ],
        actions=[
            ScreenAction("Upload", "context-engine admin documents upload --file <path>"),
            ScreenAction("Reingest", "context-engine admin documents reingest --document-id <id>"),
            ScreenAction(
                "Refresh status",
                "context-engine admin documents refresh-status --document-id <id>",
            ),
            ScreenAction("Delete", "context-engine admin documents delete --document-id <id>"),
        ],
        raw=documents,
    )


def build_upload_result_screen(result: dict[str, Any], *, filename: str | None = None) -> ScreenResult:
    document = result.get("document") if isinstance(result.get("document"), dict) else result
    job_id = result.get("job_id")
    actions = [ScreenAction("Show document", f"context-engine documents show --document-id {document.get('id', '<id>')}")]
    if job_id:
        actions.append(ScreenAction("Check job", f"context-engine jobs status --job-id {job_id}"))
    return ScreenResult(
        title="Admin Document Upload",
        api_group="admin",
        summary={"file": filename or document.get("filename", "")},
        sections=[
            ScreenSection(
                title="Upload result",
                rows=[
                    {"field": "Document ID", "value": document.get("id", "")},
                    {"field": "Filename", "value": document.get("filename", filename or "")},
                    {"field": "Status", "value": document.get("status", "uploaded")},
                    {"field": "Job ID", "value": job_id or document.get("job_id", "")},
                    {
                        "field": "LightRAG remote status",
                        "value": result.get("lightrag_status", result.get("remote_status", "")),
                    },
                ],
                columns=["field", "value"],
            )
        ],
        actions=actions,
        raw=result,
    )


def build_admin_document_action_screen(result: dict[str, Any], *, title: str) -> ScreenResult:
    action = title.replace(" Document", "").lower()
    document_id = result.get("document_id", result.get("id", ""))
    job_id = result.get("job_id", result.get("new_job_id", ""))
    if "delete" in title.lower():
        sections = [
            ScreenSection(
                title="Deleted",
                rows=[
                    {"field": "Document ID", "value": document_id},
                    {"field": "Filename", "value": result.get("filename", "")},
                    {"field": "Status", "value": result.get("status", "deleted")},
                ],
                columns=["field", "value"],
            )
        ]
        actions = [ScreenAction("List documents", "context-engine admin documents list")]
    else:
        sections = [
            ScreenSection(
                title="Request",
                rows=[
                    {"field": "Document ID", "value": document_id},
                    {"field": "Action", "value": action},
                ],
                columns=["field", "value"],
            ),
            ScreenSection(
                title="Result",
                rows=[
                    {"field": "Status", "value": result.get("status", "accepted")},
                    {"field": "Job ID", "value": job_id},
                ],
                columns=["field", "value"],
            ),
        ]
        actions = [ScreenAction("Check job", f"context-engine jobs status --job-id {job_id}")]
    return ScreenResult(
        title=f"Admin Document {action}".strip(),
        api_group="admin",
        sections=sections,
        actions=actions,
        raw=result,
    )
