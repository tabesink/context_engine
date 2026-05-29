# Phase 0 — Impact Scan

## Goal

Before editing, find every call site and test dependency for removed operations and retrieval defaults.

## Search terms

```bash
rg "repair" .
rg "recreate" .
rg "regenerate" .
rg "purge" .
rg "purgePreview" .
rg "top_k|chunk_top_k|chunk_rerank_top_k|max_token_for" .
rg "retrieval_defaults|retrievalDefaults" .
rg "start: true|start=true|request.start" .
```

## Output required before coding

Create an impact note with:

```text
frontend files affected
backend routes affected
service methods affected
models/types affected
tests affected
docs affected
migration risk
```

## Acceptance criteria

- All removed lifecycle operations have known call sites.
- All retrieval-default UI/API fields have known call sites.
- You know whether existing tests expect Create to auto-start.
- You know whether other services read manifest `retrieval_defaults`.
