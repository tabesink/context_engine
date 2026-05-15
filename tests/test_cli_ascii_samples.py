import json
import re
import shlex
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from cli.credentials import CredentialStore, StoredCredentials
from cli.main import app


runner = CliRunner()
SPEC_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "cli_docs"
    / "04_ragcli_api_surface_ascii_example"
    / "ragcli_ascii_api_surface_examples.md"
)


class SampleApiClient:
    calls: list[tuple[str, str, Any, str | None]] = []

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url
        self.token = token

    @classmethod
    def reset(cls) -> None:
        cls.calls = []

    def get(self, path: str) -> Any:
        self.calls.append(("GET", path, None, self.token))
        if path == "/auth/me":
            return {"email": "admin@example.com", "role": "admin"}
        if path == "/documents":
            return [
                {
                    "id": "doc_123",
                    "filename": "bed_manual.pdf",
                    "status": "ready",
                    "pages": 42,
                    "updated_at": "2026-05-14",
                },
                {
                    "id": "doc_456",
                    "filename": "mattress_specs.pdf",
                    "status": "ready",
                    "pages": 18,
                    "updated_at": "2026-05-13",
                },
                {
                    "id": "doc_789",
                    "filename": "service_guide.pdf",
                    "status": "indexing",
                    "updated_at": "2026-05-14",
                },
            ]
        if path == "/documents/doc_123":
            return {
                "id": "doc_123",
                "filename": "bed_manual.pdf",
                "status": "ready",
                "pages": 42,
                "created_at": "2026-05-13 09:41",
                "updated_at": "2026-05-14 10:22",
            }
        if path == "/documents/doc_123/structure":
            return {
                "document_id": "doc_123",
                "tree": {
                    "sections": [
                        {"level": 1, "title": "Introduction", "pages": "1-2"},
                        {"level": 1, "title": "Installation", "pages": "3-8"},
                        {"level": 2, "title": "Pendant Reset", "pages": "13"},
                    ]
                },
            }
        if path == "/documents/doc_123/pages/13":
            return {
                "document_id": "doc_123",
                "filename": "bed_manual.pdf",
                "page_number": 13,
                "section": "Pendant Reset",
                "text": "If the pendant does not respond, verify that the cable is seated correctly.",
            }
        if path == "/admin/documents":
            return [
                {
                    "id": "doc_123",
                    "filename": "bed_manual.pdf",
                    "status": "ready",
                    "indexed_by": "local",
                    "updated_at": "2026-05-14",
                }
            ]
        if path == "/admin/audit-logs":
            return [
                {
                    "created_at": "2026-05-14 10:41:22",
                    "user": "admin@example.com",
                    "event": "document.upload",
                    "status": "success",
                }
            ]
        if path == "/admin/query-logs":
            return [
                {
                    "created_at": "2026-05-14 10:47:01",
                    "user": "user@example.com",
                    "mode": "hybrid",
                    "top_k": 5,
                    "query": "reset procedure",
                }
            ]
        if path == "/jobs":
            return [
                {
                    "id": "job_789",
                    "kind": "reindex",
                    "status": "failed",
                    "document_id": "doc_789",
                    "updated_at": "2026-05-14 10:44:19",
                }
            ]
        if path == "/jobs/job_789":
            return {
                "id": "job_789",
                "kind": "reindex",
                "status": "failed",
                "document_id": "doc_789",
                "created_at": "2026-05-14 10:40:00",
                "updated_at": "2026-05-14 10:44:19",
                "error": "Could not parse document. The file appears to be corrupted.",
            }
        if path == "/graph/label/list":
            return ["installation", "pendant reset", "controller recovery"]
        if path == "/graph/label/popular?limit=10":
            return [{"label": "installation", "count": 42}, {"label": "reset", "count": 35}]
        if path == "/graph/label/search?q=reset&limit=5":
            return [{"label": "reset", "score": "1.00"}, {"label": "pendant reset", "score": "0.92"}]
        if path == "/graphs?label=pendant+reset&max_depth=2&max_nodes=100":
            return {
                "label": "pendant reset",
                "max_depth": 2,
                "max_nodes": 100,
                "node_count": 37,
                "edge_count": 52,
                "depth_returned": 2,
                "nodes": [{"labels": ["pendant"]}, {"labels": ["controller"]}],
                "edges": [1, 2],
            }
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        self.calls.append(("POST", path, payload, self.token))
        if path == "/auth/login":
            return {"access_token": "secret-token", "token_type": "bearer"}
        if path in {"/query/retrieve", "/query/answer", "/query"}:
            query = payload["query"]
            evidence = [
                {
                    "id": "nav-1",
                    "document_id": "doc_123",
                    "source_engine": "navigation",
                    "score": "0.84",
                    "page_start": 12,
                    "section": "Troubleshooting",
                    "text": "To reset the pendant, disconnect the bed from power.",
                }
            ]
            response = {"query": query, "mode": payload["mode"], "evidence": evidence}
            if payload.get("include_debug"):
                response["debug"] = {"selected_engine": "navigation", "final_evidence_count": 1}
            if path in {"/query/answer", "/query"}:
                response["answer"] = "To reset the pendant, start with the connection checks."
            return response
        if path == "/admin/documents/doc_123/index":
            return {"document_id": "doc_123", "status": "accepted", "job_id": "job_456"}
        if path == "/admin/documents/doc_123/reindex":
            return {"document_id": "doc_123", "status": "accepted", "job_id": "job_789"}
        if path == "/jobs/job_789/retry":
            return {"id": "job_790", "kind": "reindex", "status": "accepted", "document_id": "doc_789"}
        raise AssertionError(f"unexpected POST {path}")

    def delete(self, path: str) -> Any:
        self.calls.append(("DELETE", path, None, self.token))
        if path == "/admin/documents/doc_789":
            return {"id": "doc_789", "filename": "service_guide.pdf", "status": "deleted"}
        raise AssertionError(f"unexpected DELETE {path}")

    def post_file(self, path: str, field_name: str, filename: str, content: bytes) -> Any:
        self.calls.append(("FILE", path, {"field": field_name, "filename": filename}, self.token))
        if path == "/admin/documents/upload":
            return {"document": {"id": "doc_123", "filename": filename}, "job_id": "job_456"}
        raise AssertionError(f"unexpected FILE {path}")


def load_ascii_examples() -> dict[str, str]:
    text = SPEC_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r"Command:\s*```bash\s*(?P<command>ragcli[^\n]+)\s*```.*?"
        r"Example human output[^:]*:\s*```text\s*(?P<output>.*?)\s*```",
        re.DOTALL,
    )
    examples: dict[str, str] = {}
    for match in pattern.finditer(text):
        examples.setdefault(match.group("command"), normalize_output(match.group("output")))
    return examples


def normalize_output(output: str) -> str:
    return "\n".join(line.rstrip() for line in output.strip().splitlines())


def base_args(config_dir: Path) -> list[str]:
    return ["--config-dir", str(config_dir), "--no-keyring"]


def save_session(config_dir: Path) -> None:
    CredentialStore(config_dir, keyring_enabled=False).save(
        StoredCredentials(base_url="http://127.0.0.1:8000", access_token="secret-token")
    )


def invoke_sample(command: str, config_dir: Path, upload_file: Path | None = None):
    args = shlex.split(command.removeprefix("ragcli "))
    if upload_file is not None and "--file" in args:
        args[args.index("--file") + 1] = str(upload_file)
    return runner.invoke(app, base_args(config_dir) + args)


def assert_sample_contract(actual: str, expected_sample: str) -> None:
    actual = normalize_output(actual)
    sample_lines = expected_sample.splitlines()
    assert sample_lines[0] in actual
    assert "┌" not in actual
    assert "│" not in actual
    assert "secret-token" not in actual
    assert "password" not in actual.lower()
    sample_commands: list[str] = []
    for line in sample_lines:
        stripped = line.strip()
        if (
            stripped
            and not stripped.startswith(("+", "|"))
            and not stripped.startswith(("http://", "python -m"))
            and len(stripped) > 3
        ):
            token = stripped.split(":", 1)[0] if ":" in stripped else stripped
            if token.startswith("ragcli "):
                sample_commands.append(token)
            elif token.isupper() or token in {"Next", "Reason", "Status"}:
                assert token in actual
    if sample_commands:
        assert any(" ".join(command.split()[:2]) in actual for command in sample_commands)


def test_ascii_spec_loader_extracts_broad_cli_surface() -> None:
    examples = load_ascii_examples()

    assert len(examples) >= 30
    assert "ragcli documents list" in examples
    assert "ragcli admin documents list" in examples
    assert "ragcli runs approvals list" in examples


def test_documents_list_matches_the_tracer_sample(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", SampleApiClient)
    SampleApiClient.reset()
    save_session(tmp_path)

    result = invoke_sample("ragcli documents list", tmp_path)

    assert result.exit_code == 0, result.output
    assert_sample_contract(result.output, load_ascii_examples()["ragcli documents list"])
    assert "Backend:" in result.output
    assert "Pages" in result.output
    assert "Updated" in result.output


def test_supported_ascii_samples_render_with_sample_titles(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", SampleApiClient)
    SampleApiClient.reset()
    save_session(tmp_path)
    upload_file = tmp_path / "manual.pdf"
    upload_file.write_text("manual", encoding="utf-8")
    examples = load_ascii_examples()
    commands = [
        "ragcli auth me",
        "ragcli documents show --document-id doc_123",
        "ragcli documents structure --document-id doc_123",
        "ragcli documents page --document-id doc_123 --page-number 13",
        'ragcli documents retrieve --query "how do I reset the pendant?" --mode hybrid --top-k 3 --document-id doc_123',
        'ragcli documents retrieve --query "installation steps" --mode auto --top-k 3 --include-debug',
        'ragcli documents answer --query "how do I reset the pendant?" --document-id doc_123',
        'ragcli query --query "what does the manual say about reset?"',
        "ragcli lightrag labels list",
        "ragcli lightrag labels popular --limit 10",
        'ragcli lightrag labels search --query "reset" --limit 5',
        'ragcli lightrag graphs show --label "pendant reset" --max-depth 2 --max-nodes 100',
        "ragcli admin documents upload --file ./manual.pdf",
        "ragcli admin documents list",
        "ragcli admin documents index --document-id doc_123",
        "ragcli admin documents reindex --document-id doc_123",
        "ragcli admin documents delete --document-id doc_789",
        "ragcli admin audit-logs list",
        "ragcli admin query-logs list",
        "ragcli jobs list",
        "ragcli jobs status --job-id job_789",
        "ragcli jobs retry --job-id job_789",
    ]

    for command in commands:
        result = invoke_sample(command, tmp_path, upload_file=upload_file)
        assert result.exit_code == 0, f"{command}\n{result.output}"
        assert_sample_contract(result.output, examples[command])


def test_planned_backend_gap_samples_are_invocable(tmp_path: Path) -> None:
    examples = load_ascii_examples()
    commands = [
        "ragcli documents content --document-id doc_123 --pages 1-3",
        'ragcli documents search --query "reset"',
        "ragcli admin corpus publish",
        "ragcli users create --email user@example.com",
        "ragcli users list",
        "ragcli retrievers list",
        "ragcli agents list",
        "ragcli conversations list",
        "ragcli chat",
        'ragcli messages send --conversation-id conv_123 --content "hello"',
        "ragcli runs status --run-id run_123",
        "ragcli runs approvals list",
    ]

    for command in commands:
        result = invoke_sample(command, tmp_path)
        assert result.exit_code == 1, f"{command}\n{result.output}"
        assert_sample_contract(result.output, examples[command])
        assert "not_supported_by_backend" in result.output


def test_json_mode_keeps_human_screen_chrome_out(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("cli.main.ApiClient", SampleApiClient)
    SampleApiClient.reset()
    save_session(tmp_path)

    result = runner.invoke(app, base_args(tmp_path) + ["documents", "list", "--output", "json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["documents"][0]["id"] == "doc_123"
    assert "DOCUMENTS" not in result.output
    assert "Next:" not in result.output
    assert "+" not in result.output
