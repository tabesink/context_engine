from io import StringIO

from rich.console import Console

from cli.renderers.base import render_screen_result
from cli.renderers.tables import render_ascii_table
from cli.screens.documents import build_document_library_screen
from cli.screens.jobs import build_job_status_screen
from cli.screens.planned import build_backend_gap_screen
from cli.screens.retrieval import build_retrieval_screen


def test_ascii_table_renders_headers_rows_and_ascii_borders() -> None:
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)

    render_ascii_table(
        "Documents",
        [{"id": "doc_123", "filename": "manual.pdf", "status": "ready"}],
        ["id", "filename", "status"],
        console=console,
    )

    output = stream.getvalue()
    assert "+" in output
    assert "|" in output
    assert "doc_123" in output
    assert "manual.pdf" in output
    assert "┌" not in output
    assert "│" not in output


def test_build_document_library_screen_returns_title_rows_actions_and_raw_data() -> None:
    documents = [{"id": "doc_123", "filename": "manual.pdf", "status": "ready"}]

    screen = build_document_library_screen(documents)

    assert screen.title == "Documents"
    assert screen.api_group == "documents"
    assert screen.sections[0].rows[0]["id"] == "doc_123"
    assert any("documents show" in action.command for action in screen.actions)
    assert screen.raw is documents


def test_build_retrieval_screen_includes_evidence_and_optional_debug() -> None:
    screen = build_retrieval_screen(
        {
            "query": "reset procedure",
            "mode": "auto",
            "evidence": [
                {
                    "document_id": "doc_123",
                    "source_engine": "navigation",
                    "score": 0.82,
                    "page_start": 12,
                    "page_end": 12,
                    "text": "Reset procedure...",
                }
            ],
            "debug": {"selected_engine": "navigation"},
        }
    )

    results = next(section for section in screen.sections if section.title == "Results")
    assert screen.summary["query"] == "reset procedure"
    assert results.rows[0]["source"] == "doc_123"
    assert any(section.title == "Debug" for section in screen.sections)


def test_build_job_status_screen_shows_failure_and_retry_action() -> None:
    screen = build_job_status_screen(
        {"id": "job_123", "kind": "index_document", "status": "failed", "error": "boom"}
    )

    fields = screen.sections[0].rows
    assert {"field": "Status", "value": "failed"} in fields
    assert any("jobs retry" in action.command for action in screen.actions)


def test_build_backend_gap_screen_shows_command_and_missing_backend_route() -> None:
    screen = build_backend_gap_screen("ragcli chat")

    assert screen.api_group == "gaps"
    assert screen.summary["code"] == "not_supported_by_backend"
    assert "ragcli chat" in screen.sections[0].text
    assert screen.actions[0].disabled


def test_screen_renderer_redacts_secret_summary_values() -> None:
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)
    screen = build_document_library_screen([])
    redacted = screen.__class__(
        title=screen.title,
        api_group=screen.api_group,
        summary={"access_token": "secret-token"},
        sections=screen.sections,
    )

    render_screen_result(redacted, console=console)

    output = stream.getvalue()
    assert "secret-token" not in output
    assert "redacted" in output
