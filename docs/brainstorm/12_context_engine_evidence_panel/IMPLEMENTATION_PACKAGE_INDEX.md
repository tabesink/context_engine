# Implementation Package Index

## Package Name

`context_engine_evidence_panel_pkg`

## Purpose

This package gives a junior developer and coding agent a clear implementation path to connect `context_engine` retrieval evidence to a WebUI right-hand side evidence panel.

## Main Design Decision

Use a backend-owned normalized evidence contract.

Canonical route:

```text
POST /retrieve
```

`/query/retrieve` is not part of the current backend surface. The backend is retrieve-only, and tests assert removed `/query/*` routes return 404.

## Current Backend Baseline

The route already calls:

```python
RetrievalService(session).retrieve(request=request, user=user)
```

Do not duplicate retrieval logic.

Recent backend work also projects common evidence display fields (`source_path`, `document_title`, `chunk_id`, `reference_id`) and adds focused `/retrieve` behavior tests.

## Minimal WebUI Change

Call `/retrieve`, then render `response.evidence` as cards in the side panel.

## Fast Start

Give the coding agent this file first:

```text
IMPLEMENT.md
```

Then give the junior developer:

```text
checklists/junior_dev_checklist.md
```

## Acceptance Criteria

- `/retrieve` exists.
- `/query/retrieve` remains removed unless a future product decision restores it deliberately.
- Evidence panel renders backend evidence.
- Tests pass.
- No duplicate backend surfaces are added.
