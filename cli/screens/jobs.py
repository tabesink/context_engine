"""Job screen builders."""

from __future__ import annotations

from typing import Any

from cli.screens.models import ScreenAction, ScreenResult, ScreenSection


def build_jobs_screen(jobs: list[dict[str, Any]]) -> ScreenResult:
    return ScreenResult(
        title="Jobs",
        api_group="jobs",
        sections=[
            ScreenSection(
                title="",
                rows=jobs,
                columns=["id", "kind", "status", "document_id", "updated_at"],
            )
        ],
        actions=[
            ScreenAction(
                "Job status",
                f"ragcli jobs status --job-id {jobs[0].get('id', '<id>') if jobs else '<id>'}",
            )
        ],
        raw=jobs,
    )


def build_job_status_screen(job: dict[str, Any]) -> ScreenResult:
    actions: list[ScreenAction] = []
    if str(job.get("status", "")).lower() in {"failed", "error"}:
        actions.append(ScreenAction("Retry job", f"ragcli jobs retry --job-id {job.get('id', '<id>')}"))
        if job.get("document_id"):
            actions.append(
                ScreenAction(
                    "Delete document",
                    f"ragcli admin documents delete --document-id {job.get('document_id')}",
                )
            )
    elif job.get("document_id"):
        actions.append(
            ScreenAction("Show document", f"ragcli documents show --document-id {job.get('document_id')}")
        )
    return ScreenResult(
        title="Job Status",
        api_group="jobs",
        sections=[
            ScreenSection(
                title="",
                rows=[
                    {"field": "Job ID", "value": job.get("id", "")},
                    {"field": "Type", "value": job.get("kind", job.get("type", ""))},
                    {"field": "Status", "value": job.get("status", "")},
                    {"field": "Document ID", "value": job.get("document_id", "")},
                    {"field": "Created", "value": job.get("created_at", "")},
                    {"field": "Updated", "value": job.get("updated_at", "")},
                ],
                columns=["field", "value"],
            ),
            *[
                ScreenSection(title="Error", text=str(job.get("error")))
                for _ in [None]
                if job.get("error")
            ],
            *[
                ScreenSection(title="Result", text=str(job.get("result")))
                for _ in [None]
                if job.get("result")
            ],
        ],
        actions=actions,
        raw=job,
    )


def build_job_retry_screen(previous_job_id: str, job: dict[str, Any]) -> ScreenResult:
    new_job_id = job.get("id", job.get("job_id", job.get("new_job_id", "")))
    return ScreenResult(
        title="Job Retry",
        api_group="jobs",
        sections=[
            ScreenSection(
                title="Request",
                rows=[
                    {"field": "Previous Job", "value": previous_job_id},
                    {"field": "Action", "value": "retry"},
                ],
                columns=["field", "value"],
            ),
            ScreenSection(
                title="Result",
                rows=[
                    {"field": "Status", "value": job.get("status", "accepted")},
                    {"field": "New Job ID", "value": new_job_id},
                ],
                columns=["field", "value"],
            ),
        ],
        actions=[ScreenAction("Job status", f"ragcli jobs status --job-id {new_job_id}")],
        raw=job,
    )
