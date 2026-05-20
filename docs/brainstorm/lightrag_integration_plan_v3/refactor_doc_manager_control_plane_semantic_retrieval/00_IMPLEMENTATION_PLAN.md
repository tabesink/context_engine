# Context Engine Implementation Plan: LightRAG-Only Semantic Retrieval with Local Navigation

Repository:

```text
https://github.com/tabesink/context_engine.git
```

Selected direction:

```text
Option B — Context Engine keeps local navigation and document-control metadata.
LightRAG owns semantic retrieval completely.
LightRAG is always enabled.
There is no fallback local semantic retrieval mode.
```

Option 3 infrastructure selection:

```text
Context Engine and LightRAG share the same physical PostgreSQL service, but not
the same retrieval tables. Each LightRAG domain gets its own LightRAG-owned
database and workspace. Context Engine stores only control-plane metadata.
```

For the resolved Option 3 decisions, see:

```text
docs/brainstorm/lightrag_integration_plan_v3/refactor_doc_manager_control_plane_semantic_retrieval/03_RESOLVED_OPTION_3_DECISIONS.md
```

---

## 1. Critical Clarification: What Does “Drop `semantic_chunks` Later” Mean?

Dropping the `semantic_chunks` table later does **not** mean that LightRAG embeddings should be saved in Context Engine PostgreSQL.

It means the opposite.

The current codebase has a local semantic-retrieval table named:

```text
semantic_chunks
```

That table exists for the current local fallback system. It stores:

```text
- chunk text
- embedding vectors
- page range
- chunk metadata
```

In the new architecture, this table becomes obsolete because Context Engine should not own semantic chunks or embedding vectors.

### Correct target rule

```text
Context Engine PostgreSQL must not store LightRAG embeddings.
Context Engine PostgreSQL must not store local fallback embeddings.
Context Engine PostgreSQL may store LightRAG metadata only.
```

Allowed local metadata examples:

```text
- local document id
- owner id
- filename
- storage path for local raw-file copy
- target LightRAG domain id
- remote LightRAG document id
- remote LightRAG track id
- LightRAG indexing status
- LightRAG error message
- audit logs
- query logs
- optional parsed page text for local document browsing
- optional navigation tree for TUI/debugging
```

Not allowed in Context Engine PostgreSQL:

```text
- semantic embedding vectors
- local semantic chunks
- LightRAG internal vector data
- LightRAG graph storage
- duplicate LightRAG retrieval index
```

### Why drop the table later, not immediately?

A safe migration path has two stages:

1. **Runtime removal first.** Remove every code path that reads from or writes to `semantic_chunks`.
2. **Database cleanup second.** After tests confirm no runtime dependency remains, create an Alembic migration to drop the `semantic_chunks` table.

This avoids breaking the app halfway through the refactor.

---

## 2. Final Target Architecture

### 2.1 Responsibility split

| Responsibility | Context Engine | LightRAG |
|---|---:|---:|
| User auth | Yes | No |
| Admin/user roles | Yes | No |
| Document metadata | Yes | No, except its own internal IDs |
| Local raw upload copy | Yes | Optional remote copy after upload |
| Parsed pages for UI/TUI inspection | Yes, optional but recommended | Internal only |
| Navigation tree for UI/TUI inspection | Yes, optional but recommended | Internal graph retrieval |
| Semantic chunks | No | Yes |
| Embeddings | No | Yes |
| Vector search | No | Yes |
| Graph retrieval | Proxy/control only | Yes |
| Query logs | Yes | Optional internal logs |
| Audit logs | Yes | No |
| Domain lifecycle metadata | Yes | Runtime service owns its own data |

### 2.2 Plain-English mental model

Context Engine becomes the **control plane**:

```text
- who can log in;
- what documents exist;
- which domain a document belongs to;
- what upload/indexing status the document has;
- what pages/navigation can be shown in the TUI;
- which LightRAG domain should receive a query;
- how to audit what users/admins did.
```

LightRAG becomes the **semantic retrieval plane**:

```text
- document chunking for retrieval;
- embedding generation/storage;
- vector retrieval;
- graph retrieval;
- semantic ranking;
- answer context retrieval.
```

### 2.3 Target flow

```text
Admin uploads a document
↓
Context Engine authenticates admin
↓
Admin selects semantic_engine="lightrag"
↓
Admin selects lightrag_domain_id="manuals"
↓
Context Engine saves local metadata and optional raw-file copy
↓
Context Engine uploads the file to the selected LightRAG domain
↓
LightRAG performs semantic indexing internally
↓
Context Engine stores remote document_id / track_id / status
↓
Optional local navigation job parses pages and navigation only
↓
Normal users query the selected LightRAG domain
↓
Context Engine calls LightRAG for semantic retrieval
↓
Context Engine returns answer/context/sources to the user
```

---

## 3. Current Code Areas Affected

## 3.1 `app/services/indexing_service.py`

Current behavior:

```text
IndexingService
  - parses document
  - saves parsed pages
  - builds navigation index
  - builds semantic chunks
  - writes semantic chunks to semantic_chunks table
  - marks document READY
```

Target behavior:

```text
DocumentNavigationProcessingService
  - parses document only for local page/navigation display
  - saves parsed pages
  - builds navigation index
  - does not build semantic chunks
  - does not create embeddings
  - does not decide semantic readiness
```

Recommended change:

```text
Rename or refactor IndexingService into DocumentNavigationProcessingService.
```

At minimum, remove:

```python
from app.indexing.semantic_index_builder import SemanticIndexBuilder
```

Remove:

```python
self.semantic_builder = SemanticIndexBuilder()
```

Remove:

```python
chunks = self.semantic_builder.build(parsed)
self.documents.replace_semantic_chunks(document_id=document.id, chunks=chunks)
```

Keep:

```python
self.parser = DocumentParser()
self.navigation_builder = NavigationIndexBuilder()
self.documents.save_parsed(...)
self.documents.save_navigation_index(...)
```

### Important status behavior

Do not let local navigation processing incorrectly mark a LightRAG-uploaded document as semantically ready.

Instead, split statuses:

```text
Document semantic status = LightRAG status
Document local navigation status = Context Engine parser/navigation status
```

Recommended metadata shape:

```json
{
  "original_filename": "manual.pdf",
  "semantic_engine": "lightrag",
  "lightrag": {
    "domain_id": "manuals",
    "document_id": "remote-doc-id",
    "track_id": "remote-track-id",
    "status": "indexing",
    "message": null
  },
  "navigation": {
    "navigation_enabled": true,
    "navigation_status": "ready",
    "parsed_pages_available": true
  }
}
```

---

## 3.2 `app/indexing/semantic_index_builder.py`

Current behavior:

```text
SemanticIndexBuilder
  - chunks parsed document text
  - calls local LightRAGAdapter().embed(...)
  - creates SemanticChunkRow objects
```

Target behavior:

```text
Remove from runtime path.
```

Recommended action:

```text
Delete this file after references are removed, or move it into an archive/test-only module during the transition.
```

Because you explicitly do not want fallback local retrieval mode, do not preserve this as a fallback service.

---

## 3.3 `app/integrations/lightrag_adapter.py`

Current behavior:

This is the local fake/hash embedding adapter used by `SemanticIndexBuilder`.

Target behavior:

```text
Remove from runtime path.
```

Recommended action:

```text
Delete it after all imports are removed.
```

Do not keep it as a fallback.

---

## 3.4 `app/storage/tables.py`

Current behavior:

The code defines:

```text
SemanticChunkRow
__tablename__ = "semantic_chunks"
```

Target behavior:

```text
Remove SemanticChunkRow after runtime code no longer depends on it.
```

Recommended migration approach:

### Phase 1

Do not delete table immediately. First remove runtime references.

### Phase 2

Remove ORM model:

```python
class SemanticChunkRow(Base):
    ...
```

### Phase 3

Create Alembic migration:

```python
op.drop_table("semantic_chunks")
```

If there are indexes or constraints, drop those first as required by database dialect.

---

## 3.5 `app/storage/repositories/documents.py`

Find and remove methods related to semantic chunks, likely including:

```text
replace_semantic_chunks(...)
list_semantic_chunks(...)
```

Target behavior:

```text
DocumentRepository should manage documents, parsed pages, navigation indexes, audit logs, and metadata.
It should not manage embeddings or semantic chunks.
```

Keep methods like:

```text
create document
get document
update status
update metadata
save_parsed
save_navigation_index
get_structure
get_page
```

Remove or deprecate semantic-specific methods.

---

## 3.6 `app/retrieval/semantic_engine.py`

Current behavior:

This likely performs local semantic retrieval over `semantic_chunks`.

Target behavior:

```text
Remove from runtime path.
```

The only semantic retrieval implementation should be:

```text
app/retrieval/lightrag_remote_engine.py
```

If code imports `SemanticRetrievalEngine`, replace it with `LightRAGRemoteRetrievalEngine`.

---

## 3.7 `app/retrieval/lightrag_remote_engine.py`

Target behavior:

This becomes the only semantic retrieval engine.

Required behavior:

```text
- require lightrag_domain_id or resolve default domain;
- call LightRAGRemoteAdapter.for_domain(...);
- send query, retrieval mode, top_k, document filters where supported;
- return normalized Evidence objects;
- never fall back to local semantic search.
```

If LightRAG is unavailable, return a clear error.

Do not silently use local retrieval.

---

## 3.8 `app/retrieval/router.py`

Current behavior:

The router may support:

```text
semantic
navigation
hybrid
```

Target behavior:

```text
semantic = LightRAG only
navigation = local navigation/page search only, optional
hybrid = LightRAG semantic results + local navigation evidence, optional
```

Important rule:

```text
No route should use semantic_chunks.
```

Recommended retrieval policy:

| Retrieval Mode | New Meaning |
|---|---|
| `semantic` | Call selected LightRAG domain only |
| `navigation` | Search local parsed pages/navigation only, no embeddings |
| `hybrid` | LightRAG semantic retrieval plus local navigation/page evidence |

If you want to simplify further, make the first implementation:

```text
semantic = LightRAG only
hybrid = LightRAG only plus metadata enrichment
navigation = local only for document browsing/debugging
```

---

## 3.9 `app/services/document_service.py`

Current behavior:

`DocumentService.upload()` currently checks global settings:

```python
if self.settings.lightrag_enabled:
    return self._upload_remote(...)
```

Target behavior:

LightRAG should always be enabled and upload should be explicit.

New API concept:

```text
POST /documents/upload
  semantic_engine = "lightrag"
  lightrag_domain_id = "manuals"
```

Because you do not want fallback local semantic retrieval mode, `semantic_engine` should either:

1. always be required and only accept `lightrag`; or
2. be optional with default `lightrag`, but reject anything else.

Recommended for clarity:

```text
semantic_engine is accepted for future readability, but only "lightrag" is valid.
Navigation remains separate so a future PageIndex navigation implementation does
not look like a semantic retrieval fallback.
```

Example validation:

```text
if semantic_engine != "lightrag":
    raise 400 "Only semantic_engine='lightrag' is supported. Local semantic indexing has been removed."
```

### Upload behavior

```text
1. Validate user is admin if uploads are admin-only.
2. Validate lightrag_domain_id exists and is enabled.
3. Save local raw file copy.
4. Create document row with semantic_engine='lightrag'.
5. Set document semantic status to INDEXING.
6. Queue LightRAG ingestion for the selected domain.
7. Queue optional local navigation-processing job.
8. Return document metadata and queued job IDs.
```

### Do not queue local semantic indexing

Remove this behavior from LightRAG upload path:

```python
JobService(self.session).enqueue_index_document(document_id=document.id)
```

Replace with one of these:

```text
Option 1: enqueue_navigation_processing_document(document_id=document.id)
Option 2: process_navigation_inline for small docs only
Option 3: skip local parsing entirely if navigation is disabled
```

Recommended:

```text
Use a background navigation-processing job.
```

---

## 4. API Design

## 4.1 Upload endpoint

Target route:

```text
POST /documents/upload
```

Form fields:

```text
file: UploadFile
semantic_engine: "lightrag"
lightrag_domain_id: string
process_navigation: boolean = true
```

Example:

```text
POST /documents/upload
  file=@manual.pdf
  semantic_engine=lightrag
  lightrag_domain_id=manuals
  process_navigation=true
```

Response:

```json
{
  "document": {
    "id": "local-document-id",
    "filename": "manual.pdf",
    "status": "indexing",
    "semantic_engine": "lightrag",
    "lightrag_domain_id": "manuals",
    "lightrag_document_id": "remote-document-id",
    "lightrag_track_id": "remote-track-id",
    "lightrag_status": "queued",
    "navigation_status": "queued"
  },
  "jobs": {
    "lightrag_ingestion_job_id": "job-id",
    "navigation_job_id": "optional-job-id"
  }
}
```

## 4.2 Status endpoint

Add or update:

```text
GET /documents/{document_id}/status
```

Response should separate LightRAG semantic status from local navigation status:

```json
{
  "document_id": "...",
  "overall_status": "indexing",
  "semantic": {
    "engine": "lightrag",
    "domain_id": "manuals",
    "remote_document_id": "...",
    "track_id": "...",
    "status": "indexing"
  },
  "navigation": {
    "enabled": true,
    "status": "ready",
    "parsed_pages_available": true,
    "navigation_index_available": true
  }
}
```

## 4.3 Status refresh endpoint

Add admin-only or authenticated endpoint:

```text
POST /documents/{document_id}/refresh-lightrag-status
```

It should:

```text
1. Read document metadata.
2. Find lightrag.domain_id and lightrag.track_id.
3. Call LightRAGRemoteAdapter.document_status(track_id).
4. Update local metadata.
5. If LightRAG says indexing is complete, mark semantic status ready.
6. If LightRAG says failed, mark semantic status failed.
```

## 4.4 Query endpoint

The query endpoint should accept:

```json
{
  "query": "How do I maintain this equipment?",
  "lightrag_domain_id": "manuals",
  "mode": "semantic",
  "top_k": 8
}
```

Rules:

```text
- lightrag_domain_id is required unless a default domain is configured.
- semantic retrieval always calls LightRAG.
- no local semantic fallback.
- if LightRAG domain is unavailable, return clear 503.
```

---

## 5. Data Model Changes

## 5.1 Keep these tables

```text
users
sessions/tokens if present
documents
parsed_documents
navigation_indexes
jobs
audit_logs
query_logs
```

## 5.2 Remove later

```text
semantic_chunks
```

## 5.3 Add or formalize LightRAG domain metadata

If not already implemented as a table, add:

```text
lightrag_domains
```

Suggested columns:

```text
id                  string primary key, e.g. "manuals"
display_name        string
base_url            string
api_key_ref         optional string, not raw key if avoidable
enabled             boolean
description         text nullable
created_at          datetime
updated_at          datetime
created_by          user id nullable
```

If the current design uses a JSON manifest instead of a DB table, that is acceptable for the first implementation, but the API should still expose a clean domain list.

## 5.4 Document metadata shape

Add or standardize:

```json
{
  "semantic_engine": "lightrag",
  "lightrag": {
    "domain_id": "manuals",
    "document_id": "remote-document-id",
    "track_id": "remote-track-id",
    "status": "indexing",
    "message": null,
    "last_status_check_at": "2026-05-19T00:00:00Z"
  },
  "navigation": {
    "navigation_enabled": true,
    "navigation_status": "queued",
    "parsed_pages_available": false,
    "navigation_index_available": false
  }
}
```

---

## 6. Alembic Migration Plan

## 6.1 Migration 1: Stop writing semantic chunks

This may not require a DB migration.

Code changes only:

```text
- Remove SemanticIndexBuilder import and usage.
- Remove replace_semantic_chunks calls.
- Stop using SemanticRetrievalEngine.
- Make LightRAGRemoteRetrievalEngine the only semantic retrieval engine.
```

## 6.2 Migration 2: Add LightRAG metadata support if needed

If using JSON metadata only, migration may not be required.

If adding formal columns, add:

```text
documents.semantic_engine
documents.lightrag_domain_id
documents.lightrag_document_id
documents.lightrag_track_id
documents.semantic_status
documents.navigation_status
```

Recommended lean approach:

```text
Use existing documents.metadata first.
Add formal columns later only if query/reporting needs demand it.
```

## 6.3 Migration 3: Drop `semantic_chunks`

Only after tests pass and no code references remain:

```python
def upgrade():
    op.drop_table("semantic_chunks")


def downgrade():
    op.create_table(
        "semantic_chunks",
        ...
    )
```

If downgrade support is not important for this internal local-network app, still document that the migration is destructive.

---

## 7. Environment Configuration

Because LightRAG is always enabled, change `.env.example` from:

```text
LIGHTRAG_ENABLED=false
```

to:

```text
LIGHTRAG_ENABLED=true
```

Recommended required variables:

```text
LIGHTRAG_ENABLED=true
LIGHTRAG_DOMAIN=default
LIGHTRAG_DOMAIN_MANIFEST=.data/lightrag/domains.json
LIGHTRAG_TIMEOUT_SECONDS=30
```

For a single domain:

```text
LIGHTRAG_BASE_URL=http://lightrag-default:9621
LIGHTRAG_API_KEY=<optional-service-token>
```

For multiple domains:

```text
LIGHTRAG_DOMAIN_MANIFEST=.data/lightrag/domains.json
```

Recommended rule:

```text
Application startup should fail fast if LIGHTRAG_ENABLED is false.
```

or remove the setting entirely and assume LightRAG is mandatory.

Better production behavior:

```text
- Keep LIGHTRAG_ENABLED for tests only.
- In normal runtime, require true.
- If false, app starts only in explicit TESTING mode.
```

---

## 8. Background Jobs

The existing indexing job should be split or renamed.

Current concept:

```text
index_document = parse + navigation + semantic chunks
```

Target concept:

```text
process_document_navigation = parse + navigation only
refresh_lightrag_document_status = poll LightRAG indexing status
```

Recommended job kinds:

```text
navigation_process_document
lightrag_refresh_document_status
lightrag_ingest_document    # optional if upload should be backgrounded
```

For admin upload while users retrieve:

```text
- Upload to LightRAG should not block normal retrieval longer than necessary.
- If upload is large, queue LightRAG ingestion as a background job.
- Use a per-domain ingestion lock.
```

Redis lock key:

```text
lightrag:domain:<domain_id>:ingest_lock
```

---

## 9. Tests to Add or Update

## 9.1 Remove local semantic tests

Delete or rewrite tests that assert:

```text
- SemanticIndexBuilder creates chunks.
- Local embedding adapter returns vectors.
- semantic_chunks rows are created.
- local semantic retrieval reads semantic_chunks.
```

## 9.2 Add LightRAG-only tests

Required tests:

```text
1. Upload rejects semantic_engine != "lightrag".
2. Upload requires lightrag_domain_id when no default domain is configured.
3. Upload calls LightRAGRemoteAdapter.upload_document.
4. Upload stores remote document_id and track_id in local metadata.
5. Upload does not call JobService.enqueue_index_document for semantic indexing.
6. Optional navigation job saves parsed_documents and navigation_indexes only.
7. No semantic_chunks rows are written during upload or navigation processing.
8. Query semantic mode calls LightRAGRemoteRetrievalEngine.
9. Query semantic mode does not instantiate SemanticRetrievalEngine.
10. LightRAG unavailable returns clear HTTP 503 or configured error.
11. Refresh status updates local metadata.
12. Migration drops semantic_chunks only after code references are removed.
```

## 9.3 Regression tests

Make sure these still work:

```text
- login
- admin upload permission
- document list
- document detail
- document page retrieval if local parsing enabled
- document structure retrieval if navigation enabled
- audit logging
- query logging
- TUI screen route calls
```

---

## 10. TUI / CLI Impact

Update upload screen to ask:

```text
Target LightRAG domain: [manuals]
Process local navigation/pages? [yes]
File path: [...]
```

Do not show:

```text
Use local semantic index?
Use backend embeddings?
Fallback retrieval?
```

Document detail screen should show two statuses:

```text
Semantic engine: LightRAG
LightRAG domain: manuals
LightRAG status: indexing / ready / failed
Navigation status: queued / processing / ready / failed / disabled
```

Query screen should require domain selection:

```text
Select domain:
> manuals
  catalogs
  policies
```

---

## 11. Implementation Phases

## Phase 1 — Make LightRAG mandatory and explicit

Tasks:

```text
[ ] Set default LIGHTRAG_ENABLED=true.
[ ] Add startup validation for LightRAG config.
[ ] Update upload request schema to include semantic_engine and lightrag_domain_id.
[ ] Reject semantic_engine values other than lightrag.
[ ] Ensure upload path always uses _upload_remote.
```

## Phase 2 — Remove local semantic runtime path

Tasks:

```text
[ ] Remove SemanticIndexBuilder import from IndexingService.
[ ] Remove self.semantic_builder.
[ ] Remove semantic_builder.build(parsed).
[ ] Remove replace_semantic_chunks call.
[ ] Rename IndexingService or narrow its responsibility.
[ ] Remove local SemanticRetrievalEngine from retrieval routing.
[ ] Make LightRAGRemoteRetrievalEngine the only semantic engine.
```

## Phase 3 — Preserve local navigation only

Tasks:

```text
[ ] Keep DocumentParser.
[ ] Keep NavigationIndexBuilder.
[ ] Save parsed_documents.
[ ] Save navigation_indexes.
[ ] Store navigation metadata.
[ ] Ensure navigation processing does not overwrite LightRAG semantic status incorrectly.
```

## Phase 4 — Status and domain safety

Tasks:

```text
[ ] Add refresh LightRAG status action/job.
[ ] Add per-domain ingestion lock.
[ ] Add clear failed/unavailable states.
[ ] Ensure users can query previous ready content while admin uploads.
```

## Phase 5 — Remove dead code and DB table

Tasks:

```text
[ ] Delete or archive semantic_index_builder.py.
[ ] Delete or archive local lightrag_adapter.py.
[ ] Remove SemanticChunkRow ORM model.
[ ] Remove repository semantic chunk methods.
[ ] Add Alembic migration to drop semantic_chunks.
[ ] Update tests and docs.
```

---

## 12. Acceptance Criteria

The implementation is complete when:

```text
[ ] There is no code path that writes semantic_chunks.
[ ] There is no code path that reads semantic_chunks.
[ ] There is no runtime import of SemanticIndexBuilder.
[ ] There is no runtime import of local fake LightRAGAdapter for embeddings.
[ ] Upload accepts semantic_engine="lightrag" and lightrag_domain_id.
[ ] Upload rejects local semantic target modes.
[ ] LightRAG upload stores remote document_id and track_id.
[ ] Semantic query calls LightRAGRemoteRetrievalEngine only.
[ ] Local navigation/page parsing still works if enabled.
[ ] TUI shows LightRAG status separately from navigation status.
[ ] Alembic migration drops semantic_chunks after runtime removal.
[ ] Tests confirm no local semantic fallback exists.
```

---

## 13. Junior Developer Explanation

Before this change, Context Engine was doing two jobs:

```text
1. It managed users, documents, and metadata.
2. It also tried to create its own semantic chunks and embeddings.
```

That second job is what we are removing.

After this change, Context Engine should not behave like a vector database. It should not store embeddings. It should not rank semantic chunks. It should not have a backup local semantic retrieval system.

Instead, Context Engine should behave like a controller.

When a document is uploaded, Context Engine records:

```text
- who uploaded it;
- what file it was;
- which LightRAG domain it belongs to;
- whether LightRAG has finished indexing it;
- whether local page/navigation parsing is complete.
```

LightRAG records:

```text
- chunks;
- embeddings;
- graph data;
- retrieval indexes.
```

The important rule is:

```text
If a user asks a semantic question, Context Engine must call LightRAG.
```

It must not say:

```text
LightRAG failed, so I will use my own local embeddings.
```

That fallback is intentionally removed.

---

## 14. Recommended Coding-Agent Instruction Summary

Tell the coding agent:

```text
Refactor Context Engine so LightRAG is the only semantic retrieval engine.
Remove local semantic indexing and local embedding storage.
Preserve optional local parsing/navigation for document browsing and TUI debugging.
Make upload explicit with semantic_engine="lightrag" and lightrag_domain_id.
Stop writing semantic_chunks immediately, then drop the table in a later Alembic migration.
Do not save LightRAG embeddings in Context Engine PostgreSQL.
```
