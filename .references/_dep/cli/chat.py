"""API-backed chat streaming renderer for CLI."""

from __future__ import annotations

import json
import uuid
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from cli.api_client import ApiClient, ApiClientError

OutputMode = Literal["human", "json"]


class ApiChatLoop:
    """Interactive API-backed chat loop."""

    def __init__(
        self,
        *,
        client: ApiClient,
        conversation_id: str,
        output: OutputMode,
        agent_id: str | None = None,
    ) -> None:
        self.client = client
        self.conversation_id = conversation_id
        self.output = output
        self.agent_id = agent_id
        self.console = Console()

    def _print_json_event(self, event: dict) -> None:
        typer.echo(json.dumps(event))

    def _render_human_event(self, event: dict) -> None:
        event_type = str(event.get("event", "message"))
        if event_type == "message.delta":
            self.console.print(str(event.get("delta", "")), end="")
            return
        if event_type == "message.completed":
            self.console.print()
            return
        if event_type == "run.started":
            self.console.print(
                f"[cyan]run started[/cyan] run_id={event.get('run_id')} conversation_id={event.get('conversation_id')}"
            )
            return
        if event_type == "run.cancelled":
            self.console.print(f"[yellow]run cancelled[/yellow] run_id={event.get('run_id')}")
            return
        if event_type == "run.completed":
            self.console.print(f"[green]run completed[/green] run_id={event.get('run_id')}")
            return
        if event_type == "run.failed":
            self.console.print(
                f"[red]run failed[/red] run_id={event.get('run_id')} error_code={event.get('error_code')}"
            )
            return
        if event_type == "approval.required":
            self.console.print(
                f"[magenta]approval required[/magenta] run_id={event.get('run_id')} approval_id={event.get('approval_id')} "
                f"tool={event.get('tool_name')} risk={event.get('risk_class')}"
            )
            return
        self.console.print(f"[dim]{event_type}[/dim] {event}")

    def _handle_approval_event(self, event: dict, interactive: bool) -> bool:
        run_id = str(event.get("run_id", ""))
        approval_id = str(event.get("approval_id", ""))
        if not run_id or not approval_id:
            return False

        if not interactive:
            if self.output == "json":
                self._print_json_event(
                    {
                        "event": "approval.pending",
                        "run_id": run_id,
                        "approval_id": approval_id,
                        "next": {
                            "approve": f"claw runs approvals approve --run-id {run_id} --approval-id {approval_id}",
                            "reject": f"claw runs approvals reject --run-id {run_id} --approval-id {approval_id}",
                        },
                    }
                )
            else:
                self.console.print(
                    f"[yellow]paused for approval[/yellow] run_id={run_id} approval_id={approval_id}\n"
                    f"Approve: claw runs approvals approve --run-id {run_id} --approval-id {approval_id}\n"
                    f"Reject:  claw runs approvals reject --run-id {run_id} --approval-id {approval_id}"
                )
            return False

        choice = Prompt.ask("Approve tool call? [a/r]", choices=["a", "r"], default="r")
        endpoint = "approve" if choice == "a" else "reject"
        self.client.post(f"/v1/runs/{run_id}/approvals/{approval_id}/{endpoint}")
        if self.output == "human":
            self.console.print(f"[cyan]approval {endpoint}d[/cyan] run_id={run_id}")
        else:
            self._print_json_event({"event": "approval.resolved", "run_id": run_id, "approval_id": approval_id})
        return True

    def stream_run(self, run_id: str, interactive: bool) -> None:
        keep_streaming = True
        while keep_streaming:
            keep_streaming = False
            for event in self.client.stream(f"/v1/runs/{run_id}/stream"):
                if self.output == "json":
                    self._print_json_event(event)
                else:
                    self._render_human_event(event)
                if event.get("event") == "approval.required":
                    keep_streaming = self._handle_approval_event(event, interactive=interactive)
                    if keep_streaming:
                        break

    def send_and_stream(
        self, message: str, interactive: bool, idempotency_key: str | None = None
    ) -> None:
        payload = {
            "content": message,
            "idempotency_key": idempotency_key or str(uuid.uuid4()),
        }
        run = self.client.post(f"/v1/conversations/{self.conversation_id}/messages", payload)
        run_id = str(run["id"])
        if self.output == "json":
            self._print_json_event(
                {
                    "event": "chat.request.accepted",
                    "conversation_id": self.conversation_id,
                    "run_id": run_id,
                }
            )
        self.stream_run(run_id=run_id, interactive=interactive)

    def run(self, first_message: str | None = None) -> None:
        interactive = first_message is None
        if self.output == "human":
            self.console.print(
                Panel(
                    Text("Welcome to claw chat", style="bold cyan"),
                    title=f"Conversation {self.conversation_id}",
                    border_style="cyan",
                )
            )
            self.console.print("Type 'quit' or 'exit' to end.\n")

        if first_message:
            self.send_and_stream(first_message, interactive=False)
            return

        try:
            while True:
                user_input = Prompt.ask(Text("You", style="cyan"), console=self.console).strip()
                if user_input.lower() in {"quit", "exit", "q"}:
                    if self.output == "human":
                        self.console.print("[bold yellow]Goodbye![/bold yellow]")
                    return
                if not user_input:
                    continue
                self.send_and_stream(user_input, interactive=True)
        except (KeyboardInterrupt, EOFError):
            if self.output == "human":
                self.console.print("\n[bold yellow]Goodbye![/bold yellow]")


def chat_command(
    *,
    client: ApiClient,
    conversation_id: str,
    output: OutputMode,
    message: str | None = None,
    agent_id: str | None = None,
) -> None:
    """Execute API-backed chat flow for one conversation."""
    loop = ApiChatLoop(
        client=client,
        conversation_id=conversation_id,
        output=output,
        agent_id=agent_id,
    )
    loop.run(first_message=message)
