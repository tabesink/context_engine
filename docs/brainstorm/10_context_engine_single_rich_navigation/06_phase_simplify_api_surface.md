# 06 — Phase: Simplify API Surface

## Goal

Remove duplicate API routes and old optional switches.

## Upload API

## Current Problem

Upload may still expose:

```text
semantic_engine
lightrag_domain_id
process_navigation
enable_toc_refinement
```

But the intended system has only one ingestion path.

## Target Upload API

```text
POST /admin/documents/upload

Required:
  file
  lightrag_domain_id
```

Remove:

```text
semantic_engine
process_navigation
enable_toc_refinement
```

Target behavior:

```text
Upload always:
  1. saves file
  2. creates document row
  3. enqueues document_ingest
```

---

# Admin Document Actions

## Current Problem

Overlapping routes may include:

```text
POST /admin/documents/{id}/index
POST /admin/documents/{id}/reindex
POST /admin/documents/{id}/rebuild-structure
POST /admin/documents/{id}/reingest-lightrag
POST /admin/documents/{id}/refresh-lightrag-status
```

## Target

```text
POST /admin/documents/{id}/reingest
POST /admin/documents/{id}/refresh-status
DELETE /admin/documents/{id}
```

Definition:

```text
reingest =
  parse source file
  rebuild rich DocumentStructure
  persist local navigation
  send source chunks to LightRAG
```

---

# Query API

## Current Problem

Overlapping routes may include:

```text
POST /query/retrieve
POST /query/answer
POST /query
```

## Target

Keep only:

```text
POST /query/retrieve
```

Optional future rename:

```text
POST /retrieve
```

Remove/deprecate:

```text
POST /query
POST /query/answer
AnswerComposer
```

Rationale:

```text
Context Engine returns evidence.
It should not pretend to be an answer/chat engine unless true answer generation is a first-class feature.
```

## Tests

```text
[ ] Upload no longer accepts removed flags.
[ ] Reingest route replaces old admin document actions.
[ ] Query retrieve remains stable.
[ ] Removed routes return 404 or compatibility deprecation response during transition.
```

## Acceptance Criteria

```text
[ ] One upload behavior.
[ ] One reingest behavior.
[ ] One retrieve behavior.
```
