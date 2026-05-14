# Reference Reuse Plan

Reference repositories and vendored external code are source material. `context_engine` adapts useful behavior behind local interfaces instead of copying whole repositories or exposing external internals through the API.

## LightRAG

Reference locations:

- `.references/lightrag/`
- `external/lightrag/`

Reuse ideas:

- Query and graph API concepts from LightRAG.
- Semantic retrieval concepts from LightRAG core modules.
- Document ingestion/status concepts from LightRAG's HTTP server.
- Storage and graph vocabulary as inspiration, not as direct app models.

Current adaptation:

- Keep retrieval and graph communication HTTP-only in `app/integrations/lightrag_remote_adapter.py`.
- Resolve optional domain-specific base URLs/API keys in `app/integrations/lightrag_domains.py`.
- Convert remote chunks/references into the local `Evidence` model.
- Forward admin uploads to `/documents/upload` when `LIGHTRAG_ENABLED=true`.
- Proxy read-only graph routes through `/graphs` and `/graph/label/...`.
- Keep local semantic/navigation retrieval available when LightRAG is disabled.

Do not copy:

- The full LightRAG server bootstrap.
- LightRAG storage backends into `app/storage`.
- UI or visualizer tooling.
- Repository-wide configuration that does not match this app.
- Retrieval internals that would bypass the remote adapter boundary.

## Local Semantic Retrieval

The local fallback path uses the app's own parser, chunking, and deterministic hashed embeddings. This keeps development and tests credential-free.

The Compose database image supports pgvector, but real pgvector column/type usage is a future hardening item. Documentation should not imply pgvector is required for every local run.

## PageIndex

Reference location: `.references/pageindex/`

Reuse ideas:

- Page-range and PDF page retrieval concepts from `.references/pageindex/retrieve.py`.
- Page tree/index concepts from `.references/pageindex/page_index.py` and `page_index_md.py`.
- Utility conventions from `.references/pageindex/utils.py`.

Adaptation:

- Wrap navigation behavior in `app/integrations/pageindex_adapter.py`.
- Build indexes from `ParsedDocument`, not directly from raw files.
- Store navigation trees in application database JSON fields.
- Return local `Evidence` with page and section references.

Do not copy:

- Direct filesystem/PDF assumptions into retrieval engines.
- Any API client shape that bypasses the local service layer.

## Local Interfaces

The app owns these interfaces and models:

- `RetrievalEngine`
- `Evidence`
- `ParsedDocument`
- `NavigationIndexBuilder`
- `SemanticIndexBuilder`
- `AnswerComposer`
- `LightRAGRemoteAdapter`

Adapters may change internally as reference code changes. Routes, services, and CLI commands should continue depending on the local API and schema contracts.

