# Context Engine Entropy Cleanup Implementation Plan

**Project:** `context_engine`  
**Goal:** Remove local semantic fallback paths and make remote LightRAG the mandatory semantic retrieval backend.  
**Audience:** Coding agents, junior developers, reviewers, and maintainers.  
**Design principle:** Keep the system lean. Remove ambiguity. Preserve local navigation. Do not reintroduce local embeddings.

---

## 1. Target Architecture

The desired architecture is:

```text
Context Engine owns:
- FastAPI API surfaces
- authentication, users, roles
- document metadata
- admin upload orchestration
- local document structure/navigation
- page, section, chunk, asset, thumbnail lookup
- job orchestration
- LightRAG domain management and selection

LightRAG owns:
- semantic indexing
- vector retrieval
- graph retrieval
- semantic query execution
```

The important distinction is:

```text
Semantic retrieval = remote LightRAG only
Navigation retrieval = local Context Engine only
Hybrid retrieval = remote LightRAG semantic evidence + local navigation enrichment
```

Do **not** delete local navigation. Delete or disable only local semantic fallback behavior.

---

## 2. Current Problems to Remove

The codebase currently contains fallback and transitional paths that make the architecture harder to understand.

### High-priority entropy sources

| Area | Current issue | Target behavior |
|---|---|---|
| LightRAG config | `LIGHTRAG_ENABLED` can behave like an optional feature flag. | LightRAG must be required. If disabled, fail fast. |
| Upload/indexing | Upload can fall back to local-only indexing when LightRAG is disabled. | Upload must create local navigation artifacts and send semantic payload to LightRAG. |
| Local semantic index | `SemanticIndexBuilder`, `SemanticChunkRow`, local semantic repository methods still exist. | Remove runtime use. Drop table later through migration if safe. |
| Local fake LightRAG | `app/integrations/lightrag_adapter.py` uses deterministic hashed embeddings for local/test behavior. | Remove from production runtime. Replace tests with remote adapter fakes/mocks. |
| Retrieval routing | `semantic_engine=self.navigation_engine` makes navigation pretend to be semantic retrieval. | Semantic engine must mean LightRAG remote only. |
| Status fallback | Unknown LightRAG statuses can normalize to indexing. | Unknown statuses should fail clearly or map to explicit error state. |
| Structure parse fallback | Structure-aware ingestion can fail and fall back to raw LightRAG upload. | Decide explicitly: either allow raw fallback by config/name, or fail document ingestion. Recommended: fail if structure is required. |

---

## 3. Non-Goals

Do not do these in this implementation:

- Do not add local embeddings.
- Do not add a local vector database.
- Do not add a new semantic backend.
- Do not remove local navigation, pages, sections, assets, thumbnails, or source chunks.
- Do not add tenant isolation.
- Do not rewrite the whole retrieval system.
- Do not introduce LLM answer synthesis.
- Do not change external API contracts unless required for clarity or safety.

---

## 4. Implementation Phases

### Phase 0 — Baseline and safety

Before changing code:

1. Create a branch:

```bash
git checkout -b cleanup/mandatory-lightrag-semantic
```

2. Run existing tests:

```bash
pytest
```

3. Capture failing tests, if any, before modifications.

4. Search for fallback terms:

```bash
rg "LIGHTRAG_ENABLED|lightrag_enabled|SemanticIndexBuilder|SemanticChunk|semantic_engine|lightrag_adapter|fallback|allow_general_fallback|INDEX_JOBS_INLINE|create_all|normalize_status|upload_document"
```

5. Do not delete large files blindly. First remove runtime references, update tests, then decide whether files/tables can be removed.

---

### Phase 1 — Make LightRAG mandatory in configuration

Files to inspect:

- `app/core/config.py`
- `.env.example`
- tests referencing settings/config

Required changes:

1. Set LightRAG default to enabled.
2. Validate that `LIGHTRAG_ENABLED=false` is invalid.
3. Validate that LightRAG base URL/domain settings are present when the app boots.
4. Update `.env.example` so the required state is obvious.
5. Add tests for config validation.

Recommended behavior:

```text
If LIGHTRAG_ENABLED is false:
  raise configuration error:
  "LightRAG is required. Local semantic retrieval is no longer supported. Set LIGHTRAG_ENABLED=true and configure LIGHTRAG_BASE_URL or a LightRAG domain."
```

Possible implementation shape:

```python
# app/core/config.py

@model_validator(mode="after")
def validate_lightrag_required(self) -> "Settings":
    if not self.lightrag_enabled:
        raise ValueError(
            "LightRAG is required. Local semantic retrieval is no longer supported. "
            "Set LIGHTRAG_ENABLED=true."
        )
    if not self.lightrag_base_url and not self.lightrag_domains_manifest_path:
        raise ValueError(
            "LightRAG is enabled but no LightRAG base URL or domain manifest is configured."
        )
    return self
```

Keep the variable temporarily for backward compatibility, but force it to be true.

---

### Phase 2 — Remove local semantic runtime usage

Files to inspect:

- `app/indexing/semantic_index_builder.py`
- `app/storage/tables.py`
- `app/storage/repositories/documents.py`
- `app/services/indexing_service.py`
- `app/integrations/lightrag_adapter.py`
- related tests

Required changes:

1. Remove `SemanticIndexBuilder` from runtime services.
2. Remove calls to `replace_semantic_chunks()` and `list_semantic_chunks()` from runtime code.
3. Do not build local embeddings.
4. Do not query local semantic chunks.
5. Keep database table removal as a later migration unless no tests/runtime paths depend on it.

Recommended staged approach:

```text
Stage A:
- Stop using local semantic builder and local semantic chunks.
- Leave table/model temporarily if migration risk is high.

Stage B:
- Add Alembic migration to drop semantic_chunks after runtime is clean.
- Remove table model and repository methods.
```

Acceptance for Phase 2:

```bash
rg "SemanticIndexBuilder|replace_semantic_chunks|list_semantic_chunks|SemanticChunkRow"
```

The only allowed hits after Stage A should be migration/backward-compat comments or explicit deprecation notes. After Stage B, there should be no runtime hits.

---

### Phase 3 — Clean retrieval routing

Files to inspect:

- `app/services/retrieval_service.py`
- `app/retrieval/routing_policy.py`
- `app/retrieval/router.py`
- `app/retrieval/strategies.py`
- `app/retrieval/navigation_engine.py`
- `app/retrieval/lightrag_remote_engine.py`
- `app/api/routes/query.py`
- `app/schemas/query.py`

Target rules:

| Requested mode | Required backend |
|---|---|
| `semantic` | Remote LightRAG only |
| `hybrid` | Remote LightRAG + local navigation |
| `navigation` | Local navigation only |
| `auto` | Remote LightRAG first; optional local navigation enrichment only if explicitly implemented |

Required changes:

1. Remove misleading wiring such as:

```python
semantic_engine=self.navigation_engine
```

2. Make naming explicit:

```text
LightRAGRemoteRetrievalEngine = semantic retrieval
NavigationRetrievalEngine = navigation retrieval
HybridRetrieval = LightRAG semantic + navigation enrichment
```

3. If LightRAG is unavailable for `semantic`, `hybrid`, or `auto`, return a clear service/config error. Do not fall back to navigation as semantic.

4. Preserve direct navigation mode.

Recommended code direction:

```python
class RetrievalService:
    def __init__(...):
        self.navigation_engine = NavigationRetrievalEngine(...)
        self.lightrag_engine = LightRAGRemoteRetrievalEngine(...)

    def retrieve(...):
        if mode == RetrievalMode.NAVIGATION:
            return self.navigation_engine.retrieve(...)

        if mode == RetrievalMode.SEMANTIC:
            return self.lightrag_engine.retrieve(...)

        if mode == RetrievalMode.HYBRID:
            semantic = self.lightrag_engine.retrieve(...)
            navigation = self.navigation_engine.retrieve(...)
            return merge_results(semantic, navigation)

        if mode == RetrievalMode.AUTO:
            return self.lightrag_engine.retrieve(...)
```

Do not copy this blindly. Fit it to the existing class structure and tests.

---

### Phase 4 — Harden document upload and ingestion

Files to inspect:

- `app/services/document_service.py`
- `app/services/indexing_service.py`
- `app/services/lightrag_ingestion_service.py`
- `app/services/job_service.py`
- `app/workers/tasks.py`

Target upload flow:

```text
Admin upload
  ├── save raw file locally
  ├── create document metadata
  ├── extract local structure/navigation artifacts
  ├── persist pages, sections, chunks, assets, thumbnails
  ├── send semantic chunks or document payload to remote LightRAG
  └── mark document ready only when required local + LightRAG states are acceptable
```

Required changes:

1. Remove upload path that treats LightRAG as optional.
2. If LightRAG domain configuration is missing, reject upload clearly.
3. If structure-aware parsing fails and product requirements require chunks/assets, mark ingestion failed instead of silently raw-uploading.
4. If raw upload fallback is intentionally kept, rename it explicitly:

```text
allow_raw_lightrag_upload_when_structure_fails
```

Do not call it generic “fallback.” Make the behavior visible in config and logs.

Recommended policy:

```text
For this lean architecture, fail document ingestion when structure-aware processing fails.
Reason: the system needs source chunks/assets/page references for document navigation and evidence grounding.
```

---

### Phase 5 — Remove or tighten status fallbacks

Files to inspect:

- `app/integrations/lightrag_remote_adapter.py`
- `app/services/lightrag_ingestion_service.py`
- tests for LightRAG status handling

Required changes:

1. Unknown LightRAG statuses should not silently become `indexing`.
2. Map only known statuses.
3. Unknown upstream responses should become explicit integration errors or failed document states.
4. Add tests for unknown LightRAG status values.

Recommended behavior:

```text
LightRAG status = processed/completed/ready/success → ready
LightRAG status = processing/pending/queued/indexing → indexing
LightRAG status = failed/error → failed
Unknown status → integration error, not indexing
```

---

### Phase 6 — Remove answer fallback ambiguity

Files to inspect:

- `app/schemas/query.py`
- `app/retrieval/answer_composer.py`
- `app/api/routes/query.py`
- CLI query payload builders
- tests referencing `allow_general_fallback`

Current issue:

`allow_general_fallback` suggests the app can produce a general answer when evidence is missing, but the app does not currently have a configured LLM synthesis provider.

Recommended change:

1. Remove `allow_general_fallback`, or keep it deprecated and ignored with explicit docs.
2. Make `/query/answer` evidence-bound.
3. If no evidence is found, return an honest “no evidence found” response.

Target behavior:

```text
No evidence → no grounded answer.
Do not synthesize unsupported content.
```

---

### Phase 7 — Decide which dev conveniences stay

These are not semantic fallbacks. They can remain, but document them clearly.

| Convenience | Recommended action |
|---|---|
| `INDEX_JOBS_INLINE` | Keep for tests/local debug only. Default false in realistic runtime. |
| SQLite default DB | Keep for unit tests only; Docker/local app should use Postgres. |
| `create_all()` startup | Move toward Alembic for runtime. Keep create_all only in tests/dev bootstrap. |
| CLI keyring fallback file | Keep. Not retrieval architecture entropy. |
| CLI default API URL | Keep. Developer convenience. |

---

### Phase 8 — Update documentation

Files to update:

- `README.md`
- `.env.example`
- relevant docs under `docs/`
- CLI docs if query modes are explained

Required documentation statements:

```text
LightRAG is required.
Context Engine does not provide local semantic retrieval.
Local navigation remains available for structure, pages, sections, chunks, assets, thumbnails, and hybrid enrichment.
Semantic mode routes to remote LightRAG only.
Hybrid mode means remote LightRAG semantic retrieval plus local navigation enrichment.
Navigation mode is local only.
```

Add a short architecture diagram:

```text
/query/retrieve
    ├── mode=navigation → NavigationRetrievalEngine → local DB/navigation index
    ├── mode=semantic   → LightRAGRemoteRetrievalEngine → remote LightRAG
    ├── mode=hybrid     → LightRAG remote + local navigation merge
    └── mode=auto       → LightRAG remote first
```

---

## 5. Required Tests

Add or update tests for these behaviors.

### Config tests

- `LIGHTRAG_ENABLED` defaults to true.
- `LIGHTRAG_ENABLED=false` raises a clear config error.
- Missing LightRAG base URL/domain config raises a clear error.

### Retrieval tests

- `semantic` mode calls remote LightRAG engine.
- `semantic` mode does not call navigation engine as fallback.
- `hybrid` mode calls LightRAG and navigation.
- `navigation` mode calls only navigation.
- `auto` mode calls LightRAG first.
- LightRAG unavailable returns clear error for semantic/hybrid/auto.

### Upload/ingestion tests

- Upload requires LightRAG config/domain.
- Upload does not enqueue local-only semantic indexing.
- Structure-aware processing failure fails clearly if raw fallback is removed.
- LightRAG ingestion status maps known statuses correctly.
- Unknown LightRAG status raises or marks failed explicitly.

### Regression tests

- Local navigation document structure endpoints still work.
- Page lookup still works.
- Section lookup still works.
- Asset and thumbnail retrieval still work.
- Admin upload remains admin-only.
- Normal users can still query ready shared-corpus documents.

---

## 6. Suggested PR Breakdown

Prefer smaller PRs instead of one large risky patch.

### PR 1 — Config: LightRAG is required

Scope:

- `app/core/config.py`
- `.env.example`
- config tests

Acceptance:

- App cannot start with `LIGHTRAG_ENABLED=false`.
- Error message clearly says local semantic retrieval is unsupported.

### PR 2 — Retrieval routing cleanup

Scope:

- `app/services/retrieval_service.py`
- `app/retrieval/*`
- retrieval tests

Acceptance:

- No `semantic_engine=self.navigation_engine`.
- Semantic mode routes to LightRAG only.
- Navigation mode remains local.

### PR 3 — Remove local semantic runtime paths

Scope:

- `app/indexing/semantic_index_builder.py`
- `app/storage/repositories/documents.py`
- `app/storage/tables.py`
- tests

Acceptance:

- No runtime call builds local semantic embeddings.
- No runtime path queries local semantic chunks.

### PR 4 — Ingestion hardening

Scope:

- `app/services/document_service.py`
- `app/services/lightrag_ingestion_service.py`
- `app/workers/tasks.py`
- ingestion tests

Acceptance:

- Upload cannot bypass LightRAG semantic ingestion.
- Structure failure behavior is explicit.

### PR 5 — Docs and cleanup

Scope:

- `README.md`
- `docs/*`
- dead-code removal
- migration notes

Acceptance:

- Docs match implementation.
- No docs describe local semantic fallback as supported.

---

## 7. Acceptance Checklist

Use this before merging.

### Architecture

- [ ] LightRAG is required for semantic retrieval.
- [ ] Local navigation is preserved.
- [ ] Hybrid means LightRAG + navigation.
- [ ] No local embedding/vector fallback remains in runtime.
- [ ] No fake local LightRAG adapter is used in runtime.

### Config

- [ ] `LIGHTRAG_ENABLED=true` is the default.
- [ ] `LIGHTRAG_ENABLED=false` fails clearly.
- [ ] Missing LightRAG config fails clearly.
- [ ] `.env.example` documents LightRAG as required.

### Retrieval

- [ ] `semantic` routes only to LightRAG.
- [ ] `hybrid` routes to LightRAG + navigation.
- [ ] `navigation` routes only to local navigation.
- [ ] `auto` routes LightRAG-first.
- [ ] LightRAG errors do not silently fall back to navigation.

### Ingestion

- [ ] Upload requires LightRAG domain/config.
- [ ] No local semantic indexing job is queued.
- [ ] Structure failure behavior is explicit and tested.
- [ ] Unknown LightRAG status does not silently become indexing.

### Tests

- [ ] Config tests updated.
- [ ] Retrieval routing tests updated.
- [ ] Upload/ingestion tests updated.
- [ ] Navigation endpoint tests still pass.
- [ ] Asset/thumbnail tests still pass.
- [ ] Full test suite passes.

### Documentation

- [ ] README updated.
- [ ] `.env.example` updated.
- [ ] Relevant docs updated.
- [ ] Deprecated local semantic docs removed or corrected.

---

## 8. Reviewer Notes

Reviewers should be strict about these points:

1. Do not accept PRs that replace one hidden fallback with another hidden fallback.
2. Do not accept ambiguous names where `semantic` means local navigation.
3. Do not accept local embeddings as a convenience path.
4. Do not accept swallowed LightRAG errors unless they are transformed into explicit user-visible service errors.
5. Do not remove navigation features while cleaning semantic fallback.
6. Do not let tests pass by mocking the wrong architectural boundary.

The correct boundary is:

```text
Context Engine test fake should fake the remote LightRAG HTTP adapter,
not re-create local semantic retrieval inside Context Engine.
```

---

## 9. Final Coding-Agent Instruction

When implementing this plan, optimize for clarity over cleverness.

The end state should be easy for a junior developer to explain:

```text
Context Engine stores and navigates documents locally.
LightRAG performs semantic retrieval remotely.
There is no local semantic fallback.
```
