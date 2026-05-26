# Mandatory LightRAG Cleanup Rollout

This document summarizes the completed entropy cleanup that makes remote LightRAG the only semantic retrieval backend. Use it as a PR review guide and commit split reference.

## Target Architecture

```text
Context Engine owns:
- API, auth, document metadata, local navigation, jobs, LightRAG domain management

LightRAG owns:
- semantic indexing, vector retrieval, graph retrieval, semantic query execution

Semantic retrieval = remote LightRAG only
Navigation retrieval = local Context Engine only
Hybrid retrieval = remote LightRAG semantic evidence + local navigation enrichment
```

## What Changed (By Slice)

### Slice 1 — Config hard requirement

- Remote LightRAG runtime resolution uses the single `LIGHTRAG_DOMAIN_REGISTRY` path.
- There is no runtime fallback to `LIGHTRAG_BASE_URL` or `LIGHTRAG_DOMAIN`.
- Tests cover registry-backed behavior and required `lightrag_domain_id` validation.

**Primary files:** `app/core/config.py`, `.env.example`, `tests/test_api.py`

### Slice 2 — Retrieval routing cleanup

- Removed misleading `semantic_engine=self.navigation_engine` wiring.
- `LocalRetrievalStrategy` is navigation-only.
- `auto|semantic|hybrid` route through `LightRAGRetrievalStrategy`; `navigation` stays local.

**Primary files:** `app/services/retrieval_service.py`, `app/retrieval/strategies.py`, `tests/test_retrieval_routing_policy.py`

### Slice 3 — Local semantic runtime removal

- Verified no runtime references remain for local semantic chunk builders/repositories.
- Local navigation, pages, sections, assets, and source chunks remain intact.

**Primary files:** runtime verification only; no new local semantic paths introduced

### Slice 4 — Ingestion hardening (fail-hard structure policy)

- Removed raw LightRAG upload fallback from ingestion.
- Structure parse/build failures mark documents failed with explicit LightRAG metadata errors.
- Admin uploads require a readable LightRAG domain manifest.

**Primary files:** `app/services/lightrag_ingestion_service.py`, `app/services/document_service.py`, ingestion/upload tests

### Slice 5 — Status mapping + retrieve-only API cleanup

- Unknown LightRAG upload/track statuses raise integration errors instead of silently becoming `indexing`.
- Removed `allow_general_fallback` and `QueryResponse` from API schema and CLI payload builders.
- Removed answer-generation route/service surface and kept evidence-only retrieval at `POST /retrieve`.

**Primary files:** `app/integrations/lightrag_remote_adapter.py`, `app/schemas/retrieval.py`, `app/services/retrieval_service.py`, CLI retrieve helpers/tests

### Slice 6 — Documentation alignment

- Updated canonical docs to match enforced behavior:
  - `README.md`
  - `docs/architecture.md`
  - `docs/deployment.md`
  - `docs/junior_dev_start_here.md`
  - `docs/implementation-plan.md`
  - `docs/implementation-status.md`
  - `docs/cli_docs/*`

## Suggested Commit Split

Use six small commits (or six PRs) in dependency order:

1. **Config: require LightRAG at startup**
   - `app/core/config.py`, `.env.example`, config tests

2. **Retrieval: explicit mode routing**
   - `app/services/retrieval_service.py`, `app/retrieval/strategies.py`, routing tests

3. **Ingestion: fail-hard structure processing**
   - `app/services/lightrag_ingestion_service.py`, `app/services/document_service.py`, ingestion tests

4. **LightRAG status hardening**
   - `app/integrations/lightrag_remote_adapter.py`, status refresh behavior, adapter/API tests

5. **API simplification: retrieve-only contract**
   - `app/schemas/retrieval.py`, `app/services/retrieval_service.py`, CLI retrieve payload/services/screens

6. **Docs: canonical architecture alignment**
   - README + docs listed above, including this rollout note

## Verification Checklist

- [x] `uv run pytest -q` passes (219 tests at rollout time)
- [x] No runtime hits in `app/` for:
  - `semantic_engine=self.navigation_engine`
  - `allow_general_fallback`
  - `replace_semantic_chunks` / `list_semantic_chunks` / `SemanticIndexBuilder`
- [x] Canonical docs no longer describe local semantic fallback or raw upload fallback as supported runtime behavior

## Reviewer Focus

1. Do not accept hidden semantic fallbacks (navigation pretending to be semantic, silent status normalization, raw upload bypass).
2. Preserve local navigation endpoints and hybrid enrichment behavior.
3. Tests should fake the remote LightRAG HTTP adapter boundary, not recreate local semantic retrieval inside Context Engine.
