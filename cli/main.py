"""Typer command tree for ragcli."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlencode

import typer
from rich.console import Console

from cli.api_client import ApiClient, ApiClientError
from cli.credentials import CredentialStore, StoredCredentials
from cli.flows.admin_dashboard import build_admin_dashboard_screen, load_admin_dashboard
from cli.flows.retrieval_compare import build_retrieval_compare_screen, compare_retrieval_modes
from cli.flows.upload_document import upload_document_flow
from cli.query_payload import build_query_payload
from cli.renderers.base import render_screen_result
from cli.renderers.tables import render_ascii_table
from cli.screens.admin_documents import (
    build_admin_document_action_screen,
    build_admin_documents_screen,
    build_upload_result_screen,
)
from cli.screens.documents import (
    build_document_detail_screen,
    build_document_library_screen,
    build_document_page_screen,
    build_document_structure_screen,
)
from cli.screens.jobs import build_jobs_screen, build_job_retry_screen, build_job_status_screen
from cli.screens.lightrag import build_graph_screen, build_labels_screen
from cli.screens.observability import build_audit_logs_screen, build_query_logs_screen
from cli.screens.planned import backend_gap_message, build_backend_gap_screen, build_backend_gaps_screen
from cli.screens.retrieval import build_answer_screen, build_retrieval_screen
from cli.screens.session import build_login_screen, build_logout_screen, build_session_screen
from cli.tui.app import run_tui

OutputMode = Literal["human", "json"]
RetrievalMode = Literal["auto", "semantic", "navigation", "hybrid"]

console = Console(width=120)

app = typer.Typer(name="ragcli", help="CLI for the context-engine backend.", no_args_is_help=True)
auth_app = typer.Typer(help="Authentication commands.")
documents_app = typer.Typer(help="Document and retrieval commands.")
admin_app = typer.Typer(help="Admin commands.")
admin_documents_app = typer.Typer(help="Admin document commands.")
admin_corpus_app = typer.Typer(help="Admin corpus commands.")
admin_audit_logs_app = typer.Typer(help="Admin audit log commands.")
admin_query_logs_app = typer.Typer(help="Admin query log commands.")
jobs_app = typer.Typer(help="Indexing job commands.")
retrieval_app = typer.Typer(help="Retrieval workflow commands.")
screen_app = typer.Typer(help="Frontend-like screen aliases.")
lightrag_app = typer.Typer(help="LightRAG graph commands.")
lightrag_graphs_app = typer.Typer(help="LightRAG graph commands.")
lightrag_labels_app = typer.Typer(help="LightRAG label commands.")

users_app = typer.Typer(help="Planned user commands.")
agents_app = typer.Typer(help="Planned agent commands.")
retrievers_app = typer.Typer(help="Planned retriever commands.")
conversations_app = typer.Typer(help="Planned conversation commands.")
messages_app = typer.Typer(help="Planned message commands.")
runs_app = typer.Typer(help="Planned run commands.")
runs_approvals_app = typer.Typer(help="Planned approval commands.")

app.add_typer(auth_app, name="auth")
app.add_typer(documents_app, name="documents")
app.add_typer(admin_app, name="admin")
admin_app.add_typer(admin_documents_app, name="documents")
admin_app.add_typer(admin_corpus_app, name="corpus")
admin_app.add_typer(admin_audit_logs_app, name="audit-logs")
admin_app.add_typer(admin_query_logs_app, name="query-logs")
app.add_typer(jobs_app, name="jobs")
app.add_typer(retrieval_app, name="retrieval")
app.add_typer(screen_app, name="screen")
app.add_typer(lightrag_app, name="lightrag")
lightrag_app.add_typer(lightrag_graphs_app, name="graphs")
lightrag_app.add_typer(lightrag_labels_app, name="labels")

app.add_typer(users_app, name="users")
app.add_typer(agents_app, name="agents")
app.add_typer(retrievers_app, name="retrievers")
app.add_typer(conversations_app, name="conversations")
app.add_typer(messages_app, name="messages")
app.add_typer(runs_app, name="runs")
runs_app.add_typer(runs_approvals_app, name="approvals")


@admin_app.command("dashboard")
def admin_dashboard(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        dashboard = load_admin_dashboard(client)
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(dashboard)
    else:
        render_screen_result(build_admin_dashboard_screen(dashboard), console=console)


def default_config_dir() -> Path:
    return Path.home() / ".context-engine" / "ragcli"


@app.callback()
def main(
    ctx: typer.Context,
    api_base_url: str = typer.Option(
        "http://127.0.0.1:8000",
        "--api-base-url",
        help="Base URL for the context-engine backend.",
    ),
    config_dir: Path = typer.Option(
        default_config_dir(),
        "--config-dir",
        help="Directory used for local credential fallback.",
    ),
    keyring_enabled: bool = typer.Option(
        True,
        "--keyring/--no-keyring",
        help="Use OS keyring when available.",
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["api_base_url"] = api_base_url.rstrip("/")
    ctx.obj["credential_store"] = CredentialStore(
        config_dir=config_dir,
        keyring_enabled=keyring_enabled,
    )


def _store(ctx: typer.Context) -> CredentialStore:
    return ctx.obj["credential_store"]


def _json(payload: Any) -> None:
    typer.echo(json.dumps(payload, default=str))


def _print_payload(payload: Any, output: OutputMode, *, wrapper: str | None = None) -> None:
    if wrapper is not None:
        payload = {wrapper: payload}
    if output == "json":
        _json(payload)
        return
    console.print(json.dumps(payload, indent=2, default=str))


def _error_payload(code: str, message: str, status: int) -> dict[str, dict[str, Any]]:
    return {"error": {"code": code, "message": message, "status": status}}


def _exit_error(code: str, message: str, output: OutputMode, *, status: int = 1) -> None:
    if output == "json":
        _json(_error_payload(code, message, status))
    else:
        _render_error(code, message, status=status)
    raise typer.Exit(1)


def _handle_api_error(exc: ApiClientError, output: OutputMode) -> None:
    message = exc.message
    if exc.code == "connection_failed":
        message = f"Could not connect to backend at {console_safe_backend(message)}."
    _exit_error(exc.code, message, output, status=exc.status_code)


def _client_from_credentials(ctx: typer.Context, output: OutputMode) -> ApiClient:
    creds = _store(ctx).load()
    if creds is None:
        _exit_error("auth_required", "Run `ragcli login` first.", output)
    configured_base_url = str(ctx.obj["api_base_url"]).rstrip("/")
    if creds.base_url.rstrip("/") != configured_base_url:
        typer.echo(
            "warning: saved session uses a different --api-base-url; re-run login to switch",
            err=True,
        )
    return ApiClient(base_url=creds.base_url, token=creds.access_token)


def _query_payload(
    query: str,
    mode: RetrievalMode,
    top_k: int,
    include_debug: bool,
    allow_general_fallback: bool,
    document_ids: list[str] | None = None,
) -> dict[str, Any]:
    return build_query_payload(
        query=query,
        mode=mode,
        top_k=top_k,
        include_debug=include_debug,
        allow_general_fallback=allow_general_fallback,
        document_ids=document_ids,
    )


def _print_table(title: str, rows: list[dict[str, Any]], columns: list[str]) -> None:
    render_ascii_table(title, rows, columns, console=console)


def _unsupported(command: str, output: OutputMode) -> None:
    if output == "json":
        _exit_error(
            "not_supported_by_backend",
            f"{backend_gap_message(command)} See docs/cli_docs/api-contract.md.",
            output,
        )
    render_screen_result(build_backend_gap_screen(command), console=console)
    raise typer.Exit(1)


def console_safe_backend(message: str) -> str:
    if " at " in message:
        return message.rsplit(" at ", 1)[-1].strip(".")
    return str(message).strip(".")


def _render_error(code: str, message: str, *, status: int) -> None:
    titles = {
        "auth_required": "AUTH REQUIRED",
        "connection_failed": "CONNECTION FAILED",
        "connection_error": "CONNECTION FAILED",
        "forbidden": "FORBIDDEN",
        "auth_failed": "LOGIN FAILED",
    }
    title = titles.get(code, "API ERROR")
    console.print(title)
    console.print("")
    console.print(f"{code}: {message}")
    if code in {"connection_failed", "connection_error"}:
        console.print("")
        console.print("Next:")
        console.print("  Start the backend:")
        console.print("    python -m uvicorn app.main:create_app --factory --reload")
        console.print("")
        console.print("  Or pass a different backend:")
        console.print("    ragcli --api-base-url http://localhost:8000 auth me")
        return
    if code == "forbidden":
        console.print("")
        console.print("Reason:")
        console.print("  The backend rejected this request.")
        console.print("")
        console.print("Next:")
        console.print("  ragcli auth me")
        return
    if status:
        console.print("")
        console.print("Status:")
        console.print(f"  {status}")
    console.print("")
    console.print("Next:")
    if code in {"auth_required", "auth_failed"}:
        console.print("  ragcli login --email admin@example.com")
    else:
        console.print("  ragcli documents list")


@app.command("login")
def login(
    ctx: typer.Context,
    email: str = typer.Option(..., "--email", "-e", prompt=True),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = ApiClient(base_url=ctx.obj["api_base_url"])
    try:
        result = client.post("/auth/login", {"email": email, "password": password})
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return

    token = str(result["access_token"])
    warning = _store(ctx).save(
        StoredCredentials(base_url=ctx.obj["api_base_url"], access_token=token)
    )
    payload = {"message": f"Logged in as {email}", "email": email, "base_url": ctx.obj["api_base_url"]}
    if warning and output == "json":
        payload["warning"] = warning
    if output == "json":
        _json(payload)
    else:
        render_screen_result(
            build_login_screen(email=email, base_url=ctx.obj["api_base_url"]),
            console=console,
        )
    if warning and output != "json":
        typer.echo(warning, err=True)


@app.command("logout")
def logout(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _store(ctx).clear()
    payload = {"message": "Logged out"}
    if output == "json":
        _json(payload)
    else:
        render_screen_result(build_logout_screen(), console=console)


@auth_app.command("me")
def auth_me(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.get("/auth/me")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"user": payload})
    else:
        render_screen_result(
            build_session_screen(payload, base_url=ctx.obj["api_base_url"]),
            console=console,
        )


@documents_app.command("list")
def documents_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        documents = client.get("/documents")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"documents": documents})
    else:
        render_screen_result(
            build_document_library_screen(documents, base_url=ctx.obj["api_base_url"]),
            console=console,
        )


@documents_app.command("show")
def documents_show(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.get(f"/documents/{document_id}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"document": payload})
    else:
        render_screen_result(build_document_detail_screen(payload), console=console)


@documents_app.command("structure")
def documents_structure(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.get(f"/documents/{document_id}/structure")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(payload)
    else:
        render_screen_result(build_document_structure_screen(payload), console=console)


@documents_app.command("page")
def documents_page(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    page_number: int = typer.Option(..., "--page-number"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.get(f"/documents/{document_id}/pages/{page_number}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"page": payload})
    else:
        render_screen_result(build_document_page_screen(payload), console=console)


@documents_app.command("content")
def documents_content(
    document_id: str = typer.Option(..., "--document-id"),
    pages: str = typer.Option(..., "--pages"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported(f"ragcli documents content --pages {pages}", output)


@documents_app.command("search")
def documents_search(
    query: str = typer.Option(..., "--query"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli documents search", output)


@documents_app.command("retrieve")
def documents_retrieve(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query"),
    mode: RetrievalMode = typer.Option("auto", "--mode"),
    top_k: int = typer.Option(8, "--top-k"),
    include_debug: bool = typer.Option(False, "--debug", "--include-debug"),
    allow_general_fallback: bool = typer.Option(False, "--allow-general-fallback"),
    document_ids: list[str] | None = typer.Option(None, "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.post(
            "/query/retrieve",
            _query_payload(query, mode, top_k, include_debug, allow_general_fallback, document_ids),
        )
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(payload)
    else:
        payload = {
            **payload,
            "top_k": top_k,
            "document_filter": ", ".join(document_ids or []) or "none",
            "allow_general_fallback": allow_general_fallback,
        }
        render_screen_result(build_retrieval_screen(payload), console=console)


@documents_app.command("answer")
def documents_answer(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query"),
    mode: RetrievalMode = typer.Option("auto", "--mode"),
    top_k: int = typer.Option(8, "--top-k"),
    include_debug: bool = typer.Option(False, "--debug", "--include-debug"),
    allow_general_fallback: bool = typer.Option(False, "--allow-general-fallback"),
    document_ids: list[str] | None = typer.Option(None, "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.post(
            "/query/answer",
            _query_payload(query, mode, top_k, include_debug, allow_general_fallback, document_ids),
        )
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(payload)
    else:
        render_screen_result(build_answer_screen(payload), console=console)


@app.command("query")
def query_command(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query"),
    mode: RetrievalMode = typer.Option("auto", "--mode"),
    top_k: int = typer.Option(8, "--top-k"),
    include_debug: bool = typer.Option(False, "--debug", "--include-debug"),
    allow_general_fallback: bool = typer.Option(False, "--allow-general-fallback"),
    document_ids: list[str] | None = typer.Option(None, "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.post(
            "/query",
            _query_payload(query, mode, top_k, include_debug, allow_general_fallback, document_ids),
        )
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(payload)
    else:
        render_screen_result(build_answer_screen(payload, title="Query Answer"), console=console)


@app.command("ui")
def ui_command(
    ctx: typer.Context,
) -> None:
    """Open a lightweight interactive TUI."""
    run_tui(
        api_base_url=ctx.obj["api_base_url"],
        credential_store=_store(ctx),
        client_factory=ApiClient,
        console=console,
    )


@retrieval_app.command("compare")
def retrieval_compare(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query"),
    top_k: int = typer.Option(5, "--top-k"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    comparison = compare_retrieval_modes(client, query=query, top_k=top_k)
    if output == "json":
        _json(comparison)
    else:
        render_screen_result(build_retrieval_compare_screen(comparison), console=console)


@screen_app.command("documents")
def screen_documents(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        documents = client.get("/documents")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _exit_error("json_not_supported", "`ragcli screen documents` is a human screen alias.", output)
    else:
        render_screen_result(
            build_document_library_screen(documents, base_url=ctx.obj["api_base_url"]),
            console=console,
        )


@screen_app.command("retrieval")
def screen_retrieval(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.post(
            "/query/retrieve",
            _query_payload(query, "auto", 8, False, False, None),
        )
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _exit_error("json_not_supported", "`ragcli screen retrieval` is a human screen alias.", output)
    else:
        render_screen_result(build_retrieval_screen(payload), console=console)


@screen_app.command("graph")
def screen_graph(
    ctx: typer.Context,
    label: str = typer.Option("manual", "--label"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        graph = client.get(f"/graphs?{urlencode({'label': label, 'max_depth': 2, 'max_nodes': 100})}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _exit_error("json_not_supported", "`ragcli screen graph` is a human screen alias.", output)
    else:
        render_screen_result(build_graph_screen(graph), console=console)


@screen_app.command("admin")
def screen_admin(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        dashboard = load_admin_dashboard(client)
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _exit_error("json_not_supported", "`ragcli screen admin` is a human screen alias.", output)
    else:
        render_screen_result(build_admin_dashboard_screen(dashboard), console=console)


@screen_app.command("gaps")
def screen_gaps(output: OutputMode = typer.Option("human", "--output")) -> None:
    if output == "json":
        _json({"gaps": build_backend_gaps_screen().raw})
    else:
        render_screen_result(build_backend_gaps_screen(), console=console)


@admin_documents_app.command("upload")
def admin_documents_upload(
    ctx: typer.Context,
    file_path: Path = typer.Option(..., "--file", exists=True, dir_okay=False),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.post_file(
            "/admin/documents/upload",
            field_name="file",
            filename=file_path.name,
            content=file_path.read_bytes(),
        )
    except OSError as exc:
        _exit_error("file_read_failed", str(exc), output)
        return
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(payload)
    else:
        render_screen_result(build_upload_result_screen(payload, filename=file_path.name), console=console)


@admin_documents_app.command("upload-flow")
def admin_documents_upload_flow(
    ctx: typer.Context,
    file_path: Path = typer.Option(..., "--file", exists=True, dir_okay=False),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = upload_document_flow(client, file_path)
    except OSError as exc:
        _exit_error("file_read_failed", str(exc), output)
        return
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(payload)
    else:
        screen = build_upload_result_screen(payload["upload"], filename=payload["file"])
        render_screen_result(screen, console=console)
        if payload.get("job"):
            render_screen_result(build_job_status_screen(payload["job"]), console=console)


@admin_documents_app.command("index")
def admin_documents_index(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.post(f"/admin/documents/{document_id}/index")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(payload)
    else:
        render_screen_result(build_admin_document_action_screen(payload, title="Index Document"), console=console)


@admin_documents_app.command("reindex")
def admin_documents_reindex(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.post(f"/admin/documents/{document_id}/reindex")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json(payload)
    else:
        render_screen_result(build_admin_document_action_screen(payload, title="Reindex Document"), console=console)


@admin_documents_app.command("delete")
def admin_documents_delete(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.delete(f"/admin/documents/{document_id}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"document": payload})
    else:
        render_screen_result(build_admin_document_action_screen(payload, title="Delete Document"), console=console)


@admin_documents_app.command("list")
def admin_documents_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        documents = client.get("/admin/documents")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"documents": documents})
    else:
        render_screen_result(build_admin_documents_screen(documents), console=console)


@admin_audit_logs_app.command("list")
def admin_audit_logs_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        audit_logs = client.get("/admin/audit-logs")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"audit_logs": audit_logs})
    else:
        render_screen_result(build_audit_logs_screen(audit_logs), console=console)


@admin_query_logs_app.command("list")
def admin_query_logs_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        query_logs = client.get("/admin/query-logs")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"query_logs": query_logs})
    else:
        render_screen_result(build_query_logs_screen(query_logs), console=console)


@jobs_app.command("list")
def jobs_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        jobs = client.get("/jobs")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"jobs": jobs})
    else:
        render_screen_result(build_jobs_screen(jobs), console=console)


@jobs_app.command("status")
def jobs_status(
    ctx: typer.Context,
    job_id: str = typer.Option(..., "--job-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.get(f"/jobs/{job_id}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"job": payload})
    else:
        render_screen_result(build_job_status_screen(payload), console=console)


@jobs_app.command("retry")
def jobs_retry(
    ctx: typer.Context,
    job_id: str = typer.Option(..., "--job-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        payload = client.post(f"/jobs/{job_id}/retry")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"job": payload})
    else:
        render_screen_result(build_job_retry_screen(job_id, payload), console=console)


@lightrag_labels_app.command("list")
def lightrag_labels_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        labels = client.get("/graph/label/list")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"labels": labels})
    else:
        render_screen_result(build_labels_screen(labels, title="LightRAG Labels"), console=console)


@lightrag_labels_app.command("popular")
def lightrag_labels_popular(
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        labels = client.get(f"/graph/label/popular?{urlencode({'limit': limit})}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"labels": labels})
    else:
        render_screen_result(build_labels_screen(labels, title="Popular LightRAG Labels"), console=console)


@lightrag_labels_app.command("search")
def lightrag_labels_search(
    ctx: typer.Context,
    query: str = typer.Option(..., "--query"),
    limit: int = typer.Option(20, "--limit"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        labels = client.get(f"/graph/label/search?{urlencode({'q': query, 'limit': limit})}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"labels": labels})
    else:
        render_screen_result(build_labels_screen(labels, title="LightRAG Label Search"), console=console)


@lightrag_graphs_app.command("show")
def lightrag_graphs_show(
    ctx: typer.Context,
    label: str = typer.Option(..., "--label"),
    max_depth: int = typer.Option(3, "--max-depth"),
    max_nodes: int = typer.Option(1000, "--max-nodes"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    client = _client_from_credentials(ctx, output)
    try:
        graph = client.get(
            f"/graphs?{urlencode({'label': label, 'max_depth': max_depth, 'max_nodes': max_nodes})}"
        )
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        _json({"graph": graph})
    else:
        render_screen_result(build_graph_screen(graph), console=console)


@admin_corpus_app.command("publish")
def admin_corpus_publish(
    corpus_version_id: str | None = typer.Option(None, "--corpus-version-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    command = "ragcli admin corpus publish"
    if corpus_version_id:
        command = f"{command} --corpus-version-id {corpus_version_id}"
    _unsupported(command, output)


@admin_corpus_app.command("rollback")
def admin_corpus_rollback(
    corpus_version_id: str | None = typer.Option(None, "--corpus-version-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    command = "ragcli admin corpus rollback"
    if corpus_version_id:
        command = f"{command} --corpus-version-id {corpus_version_id}"
    _unsupported(command, output)


@admin_corpus_app.command("cleanup")
def admin_corpus_cleanup(output: OutputMode = typer.Option("human", "--output")) -> None:
    _unsupported("ragcli admin corpus cleanup", output)


@users_app.command("create")
def users_create(
    email: str | None = typer.Option(None, "--email"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli users create", output)


@users_app.command("list")
def users_list(output: OutputMode = typer.Option("human", "--output")) -> None:
    _unsupported("ragcli users list", output)


@agents_app.command("list")
def agents_list(output: OutputMode = typer.Option("human", "--output")) -> None:
    _unsupported("ragcli agents list", output)


@retrievers_app.command("list")
def retrievers_list(output: OutputMode = typer.Option("human", "--output")) -> None:
    _unsupported("ragcli retrievers list", output)


@conversations_app.command("create")
def conversations_create(output: OutputMode = typer.Option("human", "--output")) -> None:
    _unsupported("ragcli conversations create", output)


@conversations_app.command("list")
def conversations_list(output: OutputMode = typer.Option("human", "--output")) -> None:
    _unsupported("ragcli conversations list", output)


@conversations_app.command("show")
def conversations_show(
    conversation_id: str | None = typer.Option(None, "--conversation-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli conversations show", output)


@app.command("chat")
def chat(output: OutputMode = typer.Option("human", "--output")) -> None:
    _unsupported("ragcli chat", output)


@messages_app.command("send")
def messages_send(
    conversation_id: str | None = typer.Option(None, "--conversation-id"),
    content: str | None = typer.Option(None, "--content"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli messages send", output)


@messages_app.command("list")
def messages_list(
    conversation_id: str | None = typer.Option(None, "--conversation-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli messages list", output)


@runs_app.command("status")
def runs_status(
    run_id: str | None = typer.Option(None, "--run-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli runs status", output)


@runs_app.command("cancel")
def runs_cancel(
    run_id: str | None = typer.Option(None, "--run-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli runs cancel", output)


@runs_approvals_app.command("list")
def runs_approvals_list(output: OutputMode = typer.Option("human", "--output")) -> None:
    _unsupported("ragcli runs approvals list", output)


@runs_approvals_app.command("approve")
def runs_approvals_approve(
    approval_id: str | None = typer.Option(None, "--approval-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli runs approvals approve", output)


@runs_approvals_app.command("reject")
def runs_approvals_reject(
    approval_id: str | None = typer.Option(None, "--approval-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    _unsupported("ragcli runs approvals reject", output)


if __name__ == "__main__":
    app()

