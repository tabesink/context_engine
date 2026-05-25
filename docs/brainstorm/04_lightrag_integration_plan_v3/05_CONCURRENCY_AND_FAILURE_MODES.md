# Concurrency and Failure Modes

_Last verified against the codebase: May 2026. Admin domain APIs and `GET /lightrag/domains` are implemented; status polling and per-domain ingest locks described below are still open work._

## Scenario 1: Five users retrieve at the same time

### Local backend retrieval

Expected behavior:

```text
Users send POST /query/retrieve
↓
Backend reads ready documents / semantic chunks
↓
Backend scores chunks
↓
Backend returns evidence/context
```

Likely safe for 5–10 users if the document set is modest.

Main risk:

```text
semantic_chunks.embedding is JSON/JSONB and scoring happens in Python.
```

That is simple but not efficient for large corpora.

### Remote LightRAG retrieval

Expected behavior:

```text
Users send POST /query/retrieve with domain
↓
Backend resolves domain to LightRAG base_url
↓
Backend sends HTTP request to LightRAG
↓
LightRAG retrieves context
↓
Backend normalizes evidence and logs query
```

Likely safe only if the LightRAG service and LLM/embedding provider can handle 5–10 requests.

Main risks:

```text
- LightRAG runtime concurrency unknown.
- LLM provider rate limits.
- No domain rate limiting in backend.
- No per-user domain ACL in current design.
```

## Scenario 2: Admin uploads while users retrieve

### Local backend indexing

Expected safe behavior:

```text
Admin uploads document
↓
Document saved locally
↓
Index job queued in Redis
↓
Users continue querying existing READY docs
↓
Worker indexes new document
↓
New document becomes READY
```

This is the desired model.

### Remote LightRAG indexing

Expected safe behavior to implement:

```text
Admin uploads to domain manuals
↓
Backend saves local copy and document row
↓
Backend sends file to LightRAG
↓
LightRAG returns track_id
↓
Backend marks local document INDEXING
↓
Users continue querying manuals
↓
Backend periodically checks track_id
↓
When LightRAG says processed, backend marks document READY
```

What must be added:

```text
- status polling or refresh job;
- same-domain ingestion lock;
- clear UI/TUI status display;
- failure isolation and retry behavior.
```

## Failure modes and expected response

| Failure | User-visible behavior | Admin-visible behavior | Recovery |
|---|---|---|---|
| LightRAG server down | Query returns clear remote unavailable error | Domain health shows down | Restart domain service |
| Upload to LightRAG fails | Upload route returns clear error | Document status FAILED | Retry upload |
| LightRAG indexing fails | Existing docs still queryable | New document FAILED with message | Retry indexing/upload |
| Redis down | Background jobs unavailable | Health check degraded | Restart Redis; retry jobs |
| Worker down | Upload creates job but indexing does not progress | Jobs remain queued | Restart worker |
| Postgres down | API fails most operations | Health fails | Restore DB/service |
| Domain compose invalid | Domain does not start | Admin sees failed start | Regenerate compose and validate env |
| Two admin uploads same domain | Should be queued/rejected | Show ingestion lock message | Wait or retry |

## Recommended locking policy

For the first implementation:

```text
Only one active ingestion job per LightRAG domain.
```

Lock key:

```text
lightrag:domain:<domain_id>:ingest_lock
```

Lock behavior:

```text
- Acquire before remote upload/index.
- Release when remote status is READY or FAILED.
- Use timeout so stale lock can recover.
- Show admin a useful message if lock exists.
```

## Minimal load test

Before declaring production-ready for local network:

```text
1. Start backend and one LightRAG domain.
2. Upload 3–5 representative documents.
3. Run 10 concurrent `/query/retrieve` calls.
4. During those calls, upload one new document.
5. Verify queries return useful results or clear errors.
6. Verify new document eventually becomes READY.
7. Verify no duplicate ingestion jobs corrupt domain state.
```
