# LightRAG-Style Status Reporting Recreation Package

Generated: 2026-05-26

Repository reviewed:

```text
https://github.com/HKUDS/LightRAG.git
```

## Purpose

This documentation package explains how LightRAG reports document upload and ingestion status, and how to recreate the same pattern in another codebase, such as `context_engine`.

It is written for:

- coding agents
- junior developers
- frontend developers wiring status panels
- backend developers building ingestion/job status APIs
- reviewers trying to preserve LightRAG-style UX without copying its whole internals

## Main Finding

LightRAG status reporting is not one single script. It is a coordinated backend + frontend pattern:

```text
upload/insert/scan request
  → track_id generated immediately
  → background task enqueues documents
  → doc_status storage records per-document state
  → processing pipeline updates global pipeline_status
  → WebUI polls per-document and global status APIs
  → status filters, progress dialog, health badge, and pipeline activity indicators update
```

There is no dedicated standalone CLI polling script in the current status-reporting design. The closest operational scripts in the repo are setup/release/test scripts; runtime status is exposed by API routes and consumed by WebUI components.

## Package Contents

Recommended reading order:

1. `ARCHITECTURE_OVERVIEW.md`
2. `BACKEND_STATUS_API_MAP.md`
3. `BACKEND_STORAGE_AND_PIPELINE_STATE.md`
4. `WEBUI_STATUS_REFERENCE_MAP.md`
5. `UX_BEHAVIOR_TO_RECREATE.md`
6. `RECREATE_IMPLEMENTATION_PLAN.md`
7. `CONCRETE_CODING_TASKS.md`
8. `API_CONTRACTS.md`
9. `FRONTEND_COMPONENT_CONTRACTS.md`
10. `TEST_PLAN.md`
11. `CODING_AGENT_PROMPT.md`
12. `ADRS_TO_WRITE.md`

## Short Version for Coding Agent

Recreate this pattern:

```text
POST upload returns track_id
GET /track_status/{track_id} returns per-upload document states
GET /pipeline_status returns global job/progress/messages
GET /paginated returns document table rows + status counts
GET /health returns pipeline_active for high-level UI polling
Frontend polls:
  - /health at normal cadence
  - /paginated every 5s when active, 30s idle
  - /pipeline_status every 2s while dialog open
  - /track_status/{track_id} when tracking a specific upload batch
```
