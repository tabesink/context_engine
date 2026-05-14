"""CLI interface for claw using Typer."""

import json
from pathlib import Path
import uuid
from typing import Literal
from urllib.parse import quote

import typer
from rich.console import Console
from rich.table import Table

from agent.utils.config import Config
from cli.api_client import ApiClient, ApiClientError
from cli.chat import ApiChatLoop, chat_command
from cli.credentials import CredentialStore, StoredCredentials
from cli.menu import MenuOption, run_menu_loop
from env_bootstrap import load_project_env

app = typer.Typer(
    name="claw",
    help="claw: Backend-first AI CLI",
    no_args_is_help=True,
    add_completion=True,
)
users_app = typer.Typer(help="User management commands")
agents_app = typer.Typer(help="Agent listing commands")
conversations_app = typer.Typer(help="Conversation commands")
messages_app = typer.Typer(help="Message commands")
documents_app = typer.Typer(help="Shared corpus document commands")
runs_app = typer.Typer(help="Run and approval commands")
runs_approvals_app = typer.Typer(help="Run approval commands")
app.add_typer(users_app, name="users")
app.add_typer(agents_app, name="agents")
app.add_typer(conversations_app, name="conversations")
app.add_typer(messages_app, name="messages")
app.add_typer(documents_app, name="documents")
app.add_typer(runs_app, name="runs")
runs_app.add_typer(runs_approvals_app, name="approvals")

console = Console()
OutputMode = Literal["human", "json"]


def workspace_callback(ctx: typer.Context, workspace: str) -> Path:
    """Store workspace path in context for later use."""
    workspace_path = Path(workspace)
    ctx.ensure_object(dict)
    ctx.obj["workspace"] = workspace_path
    ctx.obj["credential_store"] = CredentialStore(workspace_path=workspace_path)
    return workspace_path


@app.callback()
def main(
    ctx: typer.Context,
    workspace: str = typer.Option(
        "../default_workspace",
        "--workspace",
        "-w",
        help="Path to workspace directory",
        callback=workspace_callback,
    ),
    api_base_url: str = typer.Option(
        "http://127.0.0.1:8000",
        "--api-base-url",
        help="Base URL for backend API",
    ),
) -> None:
    """Attach workspace config and API settings to context."""
    workspace_path: Path = ctx.obj["workspace"]
    load_project_env(workspace_path)
    ctx.obj["api_base_url"] = api_base_url

    config_file = workspace_path / "config.user.yaml"
    if config_file.exists():
        try:
            config = Config.load(workspace_path)
            ctx.obj["config"] = config
            if api_base_url == "http://127.0.0.1:8000":
                # Respect workspace config default unless explicit flag overrides it.
                ctx.obj["api_base_url"] = config.api_base_url
        except Exception as exc:
            console.print(f"[red]Error loading config: {exc}[/red]")
            raise typer.Exit(1) from exc
    else:
        ctx.obj["config"] = None


def _print_output(payload: dict, output: OutputMode) -> None:
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    if payload.get("message"):
        console.print(payload["message"])


def _handle_api_error(exc: ApiClientError, output: OutputMode) -> None:
    payload = {"error": {"code": exc.code, "message": exc.message, "status": exc.status_code}}
    if exc.code == "connection_failed":
        hint = (
            "Backend is unreachable. Deploy/start the backend for this API URL "
            "and retry, or choose a different --api-base-url."
        )
        payload["error"]["hint"] = hint
    if output == "json":
        typer.echo(json.dumps(payload))
    else:
        console.print(f"[red]{exc.code}[/red]: {exc.message}")
        if exc.code == "connection_failed":
            console.print(
                "[yellow]warning:[/yellow] backend appears undeployed or offline for the selected API URL."
            )
            console.print("[yellow]next:[/yellow] run deploy-cli or start the backend, then retry.")
    raise typer.Exit(1)


def _store_from_ctx(ctx: typer.Context) -> CredentialStore:
    return ctx.obj["credential_store"]


def _authed_client(ctx: typer.Context) -> ApiClient:
    store = _store_from_ctx(ctx)
    creds = store.load()
    if creds is None:
        raise RuntimeError("No saved credentials. Run login first.")
    configured_base = str(ctx.obj.get("api_base_url", "")).rstrip("/")
    if configured_base and creds.base_url.rstrip("/") != configured_base:
        typer.echo(
            "warning: saved session points to a different --api-base-url; re-run login to switch sessions",
            err=True,
        )
    return ApiClient(base_url=creds.base_url, token=creds.access_token)


def _require_authed_client(ctx: typer.Context, output: OutputMode) -> ApiClient:
    try:
        return _authed_client(ctx)
    except RuntimeError:
        payload = {"error": {"code": "auth_required", "message": "Run `claw login` first."}}
        if output == "json":
            typer.echo(json.dumps(payload))
        else:
            console.print("[red]auth_required[/red]: Run `claw login` first.")
        raise typer.Exit(1)


@app.command("login")
def login(
    ctx: typer.Context,
    username: str = typer.Option(..., "--username", "-u", prompt=True),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Login and save backend session token."""
    base_url: str = ctx.obj["api_base_url"]
    client = ApiClient(base_url=base_url)
    try:
        result = client.post(
            "/v1/auth/login",
            {"username": username, "password": password, "client_label": "cli"},
        )
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return

    token = str(result["access_token"])
    store = _store_from_ctx(ctx)
    warning = store.save(StoredCredentials(base_url=base_url, access_token=token))
    payload = {
        "message": f"Logged in as {username}",
        "username": username,
        "base_url": base_url,
        "rolling_expires_at": result.get("rolling_expires_at"),
        "absolute_expires_at": result.get("absolute_expires_at"),
    }
    _print_output(payload, output)
    if warning:
        typer.echo(warning, err=True)


@app.command("logout")
def logout(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Logout and clear saved token."""
    store = _store_from_ctx(ctx)
    creds = store.load()
    if creds is None:
        if output == "json":
            typer.echo(json.dumps({"message": "No active session"}))
        else:
            console.print("[yellow]No active session[/yellow]")
        raise typer.Exit(0)

    client = ApiClient(base_url=creds.base_url, token=creds.access_token)
    try:
        client.post("/v1/auth/logout")
    except ApiClientError:
        # Clear local token even when server session is already invalid.
        pass
    store.clear()
    _print_output({"message": "Logged out"}, output)


@users_app.command("create")
def users_create(
    ctx: typer.Context,
    username: str = typer.Option(..., "--username", "-u"),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
    role: Literal["admin", "user"] = typer.Option("user", "--role"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Create a user (admin only)."""
    client = _require_authed_client(ctx, output)
    try:
        created = client.post("/v1/users", {"username": username, "password": password, "role": role})
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return

    payload = {"message": f"Created user {created['username']}", "user": created}
    _print_output(payload, output)


@agents_app.command("list")
def agents_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """List active agents via backend."""
    client = _require_authed_client(ctx, output)
    try:
        result = client.get("/v1/agents")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return

    agents = result.get("agents", [])
    if output == "json":
        typer.echo(json.dumps({"agents": agents}))
        return

    table = Table(title="Agents")
    table.add_column("id")
    table.add_column("name")
    table.add_column("description")
    for row in agents:
        table.add_row(str(row["id"]), str(row["display_name"]), str(row.get("description", "")))
    console.print(table)


@conversations_app.command("create")
def conversations_create(
    ctx: typer.Context,
    agent_id: str = typer.Option(..., "--agent-id"),
    title: str | None = typer.Option(None, "--title"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Create conversation for an agent."""
    client = _require_authed_client(ctx, output)
    try:
        conversation = client.post("/v1/conversations", {"agent_id": agent_id, "title": title})
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    payload = {
        "message": f"Created conversation {conversation['id']}",
        "conversation": conversation,
    }
    _print_output(payload, output)


@conversations_app.command("list")
def conversations_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """List owned conversations."""
    client = _require_authed_client(ctx, output)
    try:
        result = client.get("/v1/conversations")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    conversations = result.get("conversations", [])
    if output == "json":
        typer.echo(json.dumps({"conversations": conversations}))
        return

    table = Table(title="Conversations")
    table.add_column("id")
    table.add_column("agent_id")
    table.add_column("status")
    for row in conversations:
        table.add_row(str(row["id"]), str(row["agent_id"]), str(row["status"]))
    console.print(table)


@conversations_app.command("show")
def conversations_show(
    ctx: typer.Context,
    conversation_id: str = typer.Option(..., "--conversation-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Show one conversation."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.get(f"/v1/conversations/{conversation_id}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(
        f"Conversation {payload['id']} agent={payload['agent_id']} status={payload['status']} title={payload.get('title') or ''}"
    )


@app.command("chat")
def chat(
    ctx: typer.Context,
    conversation_id: str | None = typer.Option(None, "--conversation-id"),
    agent_id: str | None = typer.Option(
        None,
        "--agent-id",
        help="Agent used only when creating a new conversation",
    ),
    message: str | None = typer.Option(None, "--message", help="Send one message and exit"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Start API-backed chat session."""
    client = _require_authed_client(ctx, output)
    chosen_conversation_id = conversation_id
    if chosen_conversation_id is None:
        chosen_agent_id = agent_id
        if chosen_agent_id is None:
            cfg = ctx.obj.get("config")
            chosen_agent_id = getattr(cfg, "default_agent", None) if cfg is not None else None
        if not chosen_agent_id:
            payload = {
                "error": {
                    "code": "invalid_request",
                    "message": "agent_id is required when conversation_id is not provided",
                }
            }
            if output == "json":
                typer.echo(json.dumps(payload))
            else:
                console.print("[red]invalid_request[/red]: provide --conversation-id or --agent-id")
            raise typer.Exit(1)
        try:
            created = client.post("/v1/conversations", {"agent_id": chosen_agent_id})
        except ApiClientError as exc:
            _handle_api_error(exc, output)
            return
        chosen_conversation_id = str(created["id"])
        if output == "human":
            console.print(
                f"[cyan]Created conversation[/cyan] {chosen_conversation_id} for agent {chosen_agent_id}"
            )

    try:
        chat_command(
            client=client,
            conversation_id=chosen_conversation_id,
            output=output,
            message=message,
            agent_id=agent_id,
        )
    except ApiClientError as exc:
        _handle_api_error(exc, output)


def _menu_login(ctx: typer.Context) -> None:
    username = typer.prompt("Username")
    password = typer.prompt("Password", hide_input=True)
    login(ctx=ctx, username=username, password=password, output="human")


def _menu_chat(ctx: typer.Context) -> None:
    chat(ctx=ctx, conversation_id=None, agent_id=None, message=None, output="human")


def _menu_agents_list(ctx: typer.Context) -> None:
    agents_list(ctx=ctx, output="human")


@app.command("menu")
def menu(ctx: typer.Context) -> None:
    """Open interactive menu for common CLI flows."""
    run_menu_loop(
        options=[
            MenuOption(label="Login", action=lambda: _menu_login(ctx)),
            MenuOption(label="Chat", action=lambda: _menu_chat(ctx)),
            MenuOption(label="Agents List", action=lambda: _menu_agents_list(ctx)),
        ],
        title="claw menu",
    )


@messages_app.command("list")
def messages_list(
    ctx: typer.Context,
    conversation_id: str = typer.Option(..., "--conversation-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """List conversation message history."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.get(f"/v1/conversations/{conversation_id}/messages")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    rows = payload.get("messages", [])
    if output == "json":
        typer.echo(json.dumps({"messages": rows}))
        return
    table = Table(title=f"Messages for {conversation_id}")
    table.add_column("seq")
    table.add_column("role")
    table.add_column("status")
    table.add_column("content")
    for row in rows:
        table.add_row(
            str(row.get("sequence_no")),
            str(row.get("role")),
            str(row.get("status")),
            str(row.get("content", "")),
        )
    console.print(table)


@messages_app.command("send")
def messages_send(
    ctx: typer.Context,
    conversation_id: str = typer.Option(..., "--conversation-id"),
    content: str = typer.Option(..., "--content"),
    idempotency_key: str | None = typer.Option(None, "--idempotency-key"),
    stream: bool = typer.Option(
        False, "--stream/--no-stream", help="Consume run SSE stream after sending"
    ),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Send one message to backend conversation."""
    client = _require_authed_client(ctx, output)
    effective_key = idempotency_key or str(uuid.uuid4())
    if stream:
        loop = ApiChatLoop(client=client, conversation_id=conversation_id, output=output)
        try:
            loop.send_and_stream(content, interactive=False, idempotency_key=effective_key)
        except ApiClientError as exc:
            _handle_api_error(exc, output)
        return
    try:
        payload = client.post(
            f"/v1/conversations/{conversation_id}/messages",
            {"content": content, "idempotency_key": effective_key},
        )
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(
        f"Accepted run {payload['id']} (conversation={conversation_id}, idempotency_key={effective_key})"
    )


@documents_app.command("list")
def documents_list(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """List active shared corpus documents."""
    client = _require_authed_client(ctx, output)
    try:
        result = client.get("/v1/documents")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    documents = result.get("documents", [])
    if output == "json":
        typer.echo(json.dumps({"documents": documents}))
        return
    table = Table(title="Documents")
    table.add_column("id")
    table.add_column("name")
    table.add_column("type")
    for row in documents:
        table.add_row(str(row["id"]), str(row["doc_name"]), str(row["doc_type"]))
    console.print(table)


@documents_app.command("show")
def documents_show(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Show active corpus document metadata."""
    client = _require_authed_client(ctx, output)
    try:
        document = client.get(f"/v1/documents/{document_id}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    payload = {"document": document}
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(json.dumps(payload, indent=2))


@documents_app.command("structure")
def documents_structure(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Fetch active corpus document structure."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.get(f"/v1/documents/{document_id}/structure")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(json.dumps(payload, indent=2))


@documents_app.command("content")
def documents_content(
    ctx: typer.Context,
    document_id: str = typer.Option(..., "--document-id"),
    pages: str = typer.Option(..., "--pages", help='Page selector, e.g. "1-3" or "4,7"'),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Fetch active corpus document content for selected pages/lines."""
    client = _require_authed_client(ctx, output)
    try:
        encoded_pages = quote(pages, safe=", -")
        payload = client.get(f"/v1/documents/{document_id}/content?pages={encoded_pages}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(json.dumps(payload, indent=2))


@documents_app.command("upload")
def documents_upload(
    ctx: typer.Context,
    file_path: Path = typer.Option(..., "--file"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Upload a Markdown/PDF file into a draft corpus version (admin only)."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.post_file(
            "/v1/admin/documents/upload",
            field_name="file",
            filename=file_path.name,
            content=file_path.read_bytes(),
        )
    except OSError as exc:
        console.print(f"[red]failed to read file: {exc}[/red]")
        raise typer.Exit(1) from exc
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    version = payload["corpus_version"]["id"]
    doc_name = payload["document"]["doc_name"]
    console.print(f"Uploaded {doc_name} into draft version {version}")


@documents_app.command("publish")
def documents_publish(
    ctx: typer.Context,
    corpus_version_id: str = typer.Option(..., "--corpus-version-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Publish a draft corpus version (admin only)."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.post(f"/v1/admin/corpus/versions/{corpus_version_id}/publish")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(f"Published corpus version {payload['id']}")


@documents_app.command("cleanup")
def documents_cleanup(
    ctx: typer.Context,
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Cleanup expired failed/unpublished staged corpus artifacts (admin only)."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.post("/v1/admin/corpus/cleanup")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(f"Removed {payload.get('removed', 0)} staged artifact directories")


@documents_app.command("rollback")
def documents_rollback(
    ctx: typer.Context,
    corpus_version_id: str = typer.Option(..., "--corpus-version-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Rollback active corpus to a previous published version (admin only)."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.post(f"/v1/admin/corpus/versions/{corpus_version_id}/rollback")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(f"Rolled back active corpus to version {payload['id']}")


@runs_app.command("status")
def runs_status(
    ctx: typer.Context,
    run_id: str = typer.Option(..., "--run-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Show run status for recovery."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.get(f"/v1/runs/{run_id}")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(
        f"Run {payload['id']} status={payload['status']} conversation={payload['conversation_id']} error={payload.get('error_code') or '-'}"
    )


@runs_app.command("cancel")
def runs_cancel(
    ctx: typer.Context,
    run_id: str = typer.Option(..., "--run-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Cancel one run (best effort)."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.post(f"/v1/runs/{run_id}/cancel")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(f"Cancelled run {payload['id']} status={payload['status']}")


@runs_approvals_app.command("list")
def runs_approvals_list(
    ctx: typer.Context,
    run_id: str = typer.Option(..., "--run-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """List approvals for a run."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.get(f"/v1/runs/{run_id}/approvals")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    approvals = payload.get("approvals", [])
    if output == "json":
        typer.echo(json.dumps({"approvals": approvals}))
        return
    table = Table(title=f"Approvals for run {run_id}")
    table.add_column("approval_id")
    table.add_column("tool")
    table.add_column("risk")
    table.add_column("scope")
    table.add_column("status")
    for row in approvals:
        table.add_row(
            str(row["id"]),
            str(row["tool_name"]),
            str(row["risk_class"]),
            str(row["approval_scope"]),
            str(row["status"]),
        )
    console.print(table)


@runs_approvals_app.command("approve")
def runs_approvals_approve(
    ctx: typer.Context,
    run_id: str = typer.Option(..., "--run-id"),
    approval_id: str = typer.Option(..., "--approval-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Approve one pending tool approval request."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.post(f"/v1/runs/{run_id}/approvals/{approval_id}/approve")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(f"Approved {payload['id']} for run {payload['run_id']}")


@runs_approvals_app.command("reject")
def runs_approvals_reject(
    ctx: typer.Context,
    run_id: str = typer.Option(..., "--run-id"),
    approval_id: str = typer.Option(..., "--approval-id"),
    output: OutputMode = typer.Option("human", "--output"),
) -> None:
    """Reject one pending tool approval request."""
    client = _require_authed_client(ctx, output)
    try:
        payload = client.post(f"/v1/runs/{run_id}/approvals/{approval_id}/reject")
    except ApiClientError as exc:
        _handle_api_error(exc, output)
        return
    if output == "json":
        typer.echo(json.dumps(payload))
        return
    console.print(f"Rejected {payload['id']} for run {payload['run_id']}")


if __name__ == "__main__":
    app()
