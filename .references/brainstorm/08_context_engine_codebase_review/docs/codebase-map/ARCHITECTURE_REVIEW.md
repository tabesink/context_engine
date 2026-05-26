# Architecture Review

## 1. Executive Summary

`context_engine` is a backend-only, multi-user hybrid RAG service. The current architecture is generally strong and does not need a rewrite.

The codebase is moving toward a clear design:

```text
FastAPI API
  → service layer
  → PostgreSQL app state
  → Redis/RQ jobs
  → remote LightRAG semantic retrieval
  → local structured navigation retrieval
  → stable evidence API
```

The most important recommendations are:

1. Document shared-corpus access as intentional.
2. Resolve CLI/TUI support contradiction.
3. Pin LightRAG image versions in staging/production.
4. Add a small retrieval access policy.
5. Keep `/retrieve` as the canonical retrieval/evidence endpoint.

## 2. Major Strengths

### Remote LightRAG Boundary

The app treats LightRAG as an external runtime service instead of embedding LightRAG internals. This is a good low-entropy architecture choice.

### Admin-Only Writes

Document upload, reingest, delete, and domain lifecycle operations are admin-only concepts. This supports a simple multi-user model.

### Structured Document Navigation

The app supports local document structure: documents, pages, sections, chunks, and assets. This enables workspace tree and evidence panel features.

### Single Retrieval API

Moving toward `/retrieve` as the canonical evidence endpoint reduces API duplication.

### Production Guardrails

The config layer includes production safety posture such as rejecting weak secrets, wildcard origins, and SQLite in production.

## 3. Findings by Severity

## Critical

No confirmed critical issue from the reviewed architecture.

The shared-corpus access model becomes critical only if the intended product requires per-user private documents or tenant isolation.

## High

### [High] Shared-Corpus Access Model Must Be Explicit

**Problem:** The app appears to allow all authenticated users to read all ready documents in visible domains.

**Evidence:** Retrieval and document access flows currently treat user identity mainly as authentication, not row-level document filtering.

**Why it matters:** The app is multi-user. Future developers may assume per-user isolation exists when it does not.

**Recommendation:** Add an ADR documenting the V1 shared-corpus model.

**Effort:** Low  
**Risk:** Low  
**Priority:** P0

### [High] Production LightRAG Image Should Be Pinned

**Problem:** Using `latest` image tags risks deployment drift.

**Why it matters:** LightRAG behavior, APIs, environment settings, and storage assumptions can change across versions.

**Recommendation:** Reject `:latest` in staging/production config validation.

**Effort:** Low  
**Risk:** Low  
**Priority:** P1

## Medium

### [Medium] CLI/TUI Support Is Ambiguous

**Problem:** Project docs appear to conflict on whether CLI/TUI is supported.

**Why it matters:** Coding agents and junior developers will not know whether to preserve or ignore CLI-related code/tests.

**Recommendation:** Decide and document one posture.

Recommended posture:

```text
TUI is a developer-only backend API harness, not a product UI.
```

**Effort:** Low  
**Risk:** Low  
**Priority:** P1

### [Medium] Settings Class Is Becoming Too Broad

**Problem:** One settings class owns many unrelated concerns.

**Why it matters:** Future provider/domain/frontend config will make this harder to understand.

**Recommendation:** Keep one public `get_settings()` but split settings internally into named groups.

**Effort:** Medium  
**Risk:** Medium  
**Priority:** P2

### [Medium] Retrieval Authorization Should Be Centralized

**Problem:** Retrieval engines should not be responsible for access semantics, and currently user ID is not meaningful in engines.

**Why it matters:** Future per-domain or per-user access will be easier if policy is centralized.

**Recommendation:** Add `RetrievalAccessPolicy`.

**Effort:** Medium  
**Risk:** Medium  
**Priority:** P1/P2

### [Medium] Local Navigation Retrieval Is Brute-Force

**Problem:** Structured lookup may scan local document structures.

**Why it matters:** Fine for small-team use, but may degrade as corpus grows.

**Recommendation:** Keep simple for now. Add PostgreSQL full-text search only when performance evidence requires it.

**Effort:** Low now / Medium later  
**Risk:** Low  
**Priority:** P2

## Low

### [Low] CORS Should Remain Explicit in Production

Wildcard origins should stay rejected in production. Document expected frontend origins clearly.

### [Low] Query Text Privacy Default Is Good

Do not store raw query text by default unless explicitly enabled.

## Positive Findings

- Route structure is understandable.
- Service/repository split is useful.
- LightRAG HTTP boundary is a good design.
- Tests cover meaningful architecture areas.
- Background job approach is appropriate.
- `/retrieve` simplification is the right direction.

## 4. Architecture Fitness Scorecard

| Lens | Score | Notes |
|---|---:|---|
| Modularity | 4/5 | Good route/service/retrieval separation |
| Separation of concerns | 3.5/5 | Some concrete wiring could move into factories |
| Dependency direction | 3.5/5 | Mostly clean; improve policy/adapters |
| Data flow clarity | 4/5 | Main flows are traceable |
| Scalability | 3/5 | Appropriate for small internal deployment |
| Reliability | 3.5/5 | Good job/runtime model; improve provider failure handling |
| Security | 3.5/5 | Admin boundaries good; access model needs ADR |
| Testing | 4/5 | Meaningful tests exist |
| Observability | 3/5 | Needs tracing/metrics if production grows |
| Deployment readiness | 3.5/5 | Good Compose/migrations; pin images |
| Evolvability | 4/5 | Good foundation |
| Junior readability | 3.5/5 | Good layout; docs conflicts hurt clarity |

## 5. Final Recommendation

Do not rewrite the codebase.

Stabilize the current architecture by documenting decisions, clarifying access policy, keeping LightRAG as an adapter boundary, and preparing `/retrieve` as the frontend's stable evidence API.
