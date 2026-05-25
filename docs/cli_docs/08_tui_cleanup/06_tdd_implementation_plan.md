# 6. TDD Implementation Plan

## Slice 1: Root Menu Cleanup

### Test first

Add/update tests:

```text
tests/test_cli_tui.py
tests/test_cli_screen_renderers.py
```

Assertions:

```text
root menu includes Documents
root menu includes Retrieval
root menu includes Graphs
root menu includes LightRAG Domains
root menu does not include LightRAG Graphs
root menu does not include Admin Documents
root menu does not include Create LightRAG Domain
root menu does not include Start LightRAG Domain
root menu does not include Stop LightRAG Domain
root menu does not include Recreate LightRAG Domain
root menu does not include Remove LightRAG Domain
```

### Implement

Update the root menu builder under `cli/tui/`.

## Slice 2: LightRAG Domains Nested Actions

### Test first

Assertions:

```text
LightRAG Domains screen includes Create Domain
LightRAG Domains screen includes Start Domain
LightRAG Domains screen includes Stop Domain
LightRAG Domains screen includes Recreate Domain
LightRAG Domains screen includes Regenerate Domain Files
LightRAG Domains screen includes Archive Remove Domain
LightRAG Domains screen includes Permanent Delete Domain
```

### Implement

Move existing action entries into `LightRAG Domains` screen.

No backend changes needed.

## Slice 3: Rename LightRAG Graphs to Graphs

### Test first

Assertions:

```text
root menu shows Graphs
graph screen title is GRAPHS
graph service still calls GET /graphs and /graph/label/...
```

### Implement

Change UI label only.

No backend changes needed.

## Slice 4: Documents Menu Consolidation

### Test first

Assertions:

```text
root menu shows Documents
root menu does not show Admin Documents
Documents screen shows Admin Actions for admin users
Documents screen hides Admin Actions for normal users, or renders disabled with backend-auth explanation
Admin Actions screen calls /admin/documents routes
Browse Documents calls /documents routes
```

### Implement

Move admin document actions under the Documents screen.

No backend route merge required.

## Slice 5: Documentation Update

Update:

```text
docs/cli_docs/tui_ux.md
docs/cli_docs/frontend_traceability.md
docs/cli_docs/commands.md
docs/cli_docs/api-contract.md
```

Make sure docs say:

- `context-engine` and `context-tui` are the supported entrypoints.
- Root menu is capability areas only.
- LightRAG domain CRUD lives under `LightRAG Domains`.
- `Graphs` is the operator-facing graph screen.
- `Documents` contains admin actions when user is admin.

## Slice 6: Conformance Tests

Run:

```bash
pytest tests/test_cli_tui.py tests/test_cli_screen_renderers.py tests/test_cli_services.py -q
```

If ASCII conformance tests exist:

```bash
pytest tests/test_cli_ascii_samples.py -q
```

## Slice 7: Optional Backend Route Simplification Later

Do not do this now unless explicitly scoped.

Potential future simplifications:

| Current | Future |
|---|---|
| `/query/answer` + `/query` | Keep one public answer endpoint |
| `/admin/documents/{id}/reingest` + `/refresh-status` | `POST /admin/documents/{id}/reingest` |
| `/graph/label/list`, `/popular`, `/search` | `GET /graph/labels?q=&sort=&limit=` |
| `/admin/documents` + `/documents` | maybe `GET /documents?scope=all`, admin-only |
