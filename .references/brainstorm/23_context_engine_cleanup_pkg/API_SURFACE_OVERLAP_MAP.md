# API Surface and Overlap Map

This map focuses on known high-entropy surfaces. Verify paths against the current branch before implementation.

## Route groups observed

| Route file | Surface | Cleanup concern |
|---|---|---|
| `app/api/routes/auth.py` | Authentication | Preserve. Do not refactor during cleanup unless tests exist. |
| `app/api/routes/users.py` | User/admin user surface | Preserve authz boundaries. |
| `app/api/routes/ai_settings.py` | Provider/model settings | Check naming alignment with frontend settings route. |
| `app/api/routes/lightrag_admin.py` | Admin LightRAG domain lifecycle | Highest overlap risk. |
| `app/api/routes/lightrag.py` | User LightRAG graph/proxy routes | Keep separate from admin lifecycle routes. |
| `app/api/routes/documents.py` | Documents, structure, assets, chunks, pages, ingestion status | Rich surface; reduce repeated projection/loading logic. |
| `app/api/routes/jobs.py` | Admin job listing/retry/status | Clarify relationship to document ingestion status. |
| `app/api/routes/retrieve.py` | Retrieval/chat query surface | Preserve Evidence contract. |
| `app/api/routes/workspace_tree.py` | Workspace/source tree | Align with context panel and evidence/source contract. |
| `app/api/routes/health.py` | Health/readiness | Preserve; avoid mixing with domain health semantics. |
| `app/api/routes/admin.py` | General admin | Check if it duplicates lightrag_admin/users/jobs responsibilities. |

## LightRAG admin lifecycle endpoints

| Operation | Likely public role | Overlap risk | Recommendation |
|---|---|---|---|
| Create domain | Public admin | Low | Keep. If `start=true`, ensure it uses canonical repair/start behavior. |
| Up | Public admin/advanced | Medium | Keep as Start if users need explicit start. Otherwise fold into Repair/Recover. |
| Down | Public admin/advanced | Medium | Keep as Stop. Different from Archive/Delete. |
| Recreate | Compatibility/advanced | High | Deprecate from normal UI. Route can remain temporarily. |
| Repair | Canonical recovery | Low | Keep and make canonical. |
| Regenerate | Internal/advanced maintenance | High | Hide from normal UI. Consider internal helper. |
| Delete/archive | Public admin destructive/non-destructive | Medium | Rename clearly as Archive if data remains. |
| Purge preview | Public admin safety check | Low | Keep. |
| Purge | Public admin destructive | High but necessary | Keep with explicit confirmation and audit logs. |
| Status/health | Public/admin projection | Medium | Clarify source of truth and staleness. |

## Minimal recommended public/admin API

### Normal user routes

- Auth/session routes.
- List allowed domains.
- Retrieve/query selected domain.
- Workspace tree/context routes.
- Document/source navigation routes users are authorized to view.

### Normal admin routes

- Create domain.
- Start domain.
- Stop domain.
- Repair domain.
- Archive domain.
- Purge preview.
- Purge with explicit confirmation.
- Upload document.
- View document/job status.
- Retry failed ingestion job.
- Provider/settings management.

### Advanced/internal/compatibility routes

- Recreate.
- Regenerate.
- Raw Docker/runtime operation helpers.
- Artifact rewrite helpers.

## API cleanup rules

1. Do not remove a route in the same PR that changes its implementation.
2. Add deprecation markers and tests before route removal.
3. Keep response schemas stable unless the frontend is updated in the same branch.
4. Dangerous operations must require explicit confirmation and audit logs.
5. Status routes must include `updated_at` or equivalent freshness metadata where possible.
