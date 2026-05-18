# Testing Strategy and Fixtures for context-engine TDD

## Test philosophy

Tests should verify behavior through public interfaces.

For this CLI, public interfaces are:

- CLI commands
- JSON output
- human output
- TUI app entrypoint/screen behavior
- screen builder public functions

Avoid testing private methods, internal call order, or low-level widget internals.

## What to mock

Mock system boundaries only:

- backend HTTP API
- credential/keyring storage
- file system for upload file-not-found cases
- time/randomness if needed

Do not mock:

- internal renderers
- internal screen builders
- internal helper functions
- command modules you control

## Recommended test types

## 1. CLI behavior tests

These are the most important tests.

Use a CLI runner to execute commands as a user would.

Examples:

```text
context-engine documents list --output json
context-engine documents list
context-engine documents retrieve --query "reset procedure"
context-engine lightrag labels popular
context-engine admin documents upload --file ./manual.pdf
```

Mock HTTP responses at the backend boundary.

Assert:

- exit code
- output shape
- expected backend route
- no secrets
- stable JSON

## 2. Renderer tests

Use sparingly.

Test renderer behavior when output rules are important:

- ASCII table borders
- no Unicode box drawing
- no secrets
- useful empty states
- actionable errors

Do not test exact spacing unless necessary.

## 3. Screen builder tests

Test public screen builder functions.

Good:

```text
test_build_document_library_screen_returns_rows_actions_and_raw
```

Bad:

```text
test_document_screen_calls_internal_format_status_helper
```

## 4. TUI smoke tests

Keep TUI tests light.

Test:

- starts
- renders main menu
- opens a few screens
- exits
- uses ASCII tables
- shows backend gaps

Avoid brittle tests around exact widget hierarchy.

## 5. Flow tests

Test guided flows through CLI commands.

Examples:

```text
test_retrieval_compare_calls_all_modes
test_upload_flow_handles_job_id
test_admin_dashboard_handles_backend_403
```

## Fixture strategy

## Fake API responses

Keep fixtures small and readable.

```python
DOCUMENTS_RESPONSE = [
    {"id": "doc_123", "filename": "manual.pdf", "status": "ready"}
]

RETRIEVAL_RESPONSE = {
    "query": "reset procedure",
    "mode": "navigation",
    "evidence": [
        {
            "evidence_id": "ev_1",
            "document_id": "doc_123",
            "source_engine": "navigation",
            "text": "Reset procedure...",
            "score": 0.82,
            "page_start": 12,
            "page_end": 12,
            "section_title": "Troubleshooting",
            "metadata": {}
        }
    ],
    "debug": {
        "requested_mode": "auto",
        "selected_engine": "navigation"
    }
}
```

## Test data files

Use temporary files for upload tests.

```python
def test_upload_success(tmp_path):
    pdf = tmp_path / "manual.pdf"
    pdf.write_bytes(b"%PDF test")
    ...
```

## Secret safety assertions

Every auth/admin/error test should ensure:

```text
assert "access_token" not in output
assert "Bearer" not in output
assert "password" not in output.lower()
```

Use this carefully so legitimate text like "password is not stored" in help output does not create false positives.

## Golden JSON tests

Use exact JSON comparison for stable contracts.

Example:

```python
payload = json.loads(result.output)
assert payload == {
    "documents": [
        {"id": "doc_123", "filename": "manual.pdf", "status": "ready"}
    ]
}
```

## Human output tests

Use partial assertions.

Good:

```python
assert "Documents" in output
assert "+--------" in output
assert "doc_123" in output
assert "manual.pdf" in output
```

Avoid fragile exact full-screen snapshots early.

## TDD cycle checklist

For each vertical slice:

```text
[ ] Write one failing behavior test
[ ] Implement only enough code to pass
[ ] Run focused test
[ ] Run related tests
[ ] Refactor only while green
[ ] Run full CLI tests before moving on
```

## Regression checklist

Before merging:

```text
[ ] Existing auth tests pass
[ ] Existing document/retrieval tests pass
[ ] Existing admin/jobs tests pass
[ ] Existing LightRAG graph tests pass
[ ] Unsupported planned command tests pass
[ ] JSON output unchanged
[ ] No token/password output
[ ] TUI starts/exits
[ ] ASCII table rule enforced
[ ] No direct LightRAG calls from CLI
```
