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
- Queue admin uploads for LightRAG ingestion when `LIGHTRAG_BASE_URL=http://localhost:9621`.
- Proxy read-only graph routes through `/graphs` and `/graph/label/...`.
- Keep local navigation retrieval available for page/tree browsing and hybrid enrichment.
- Manage optional domain deployment through local Context Engine code under `app/lightrag_deploy/`, using generated `.data/lightrag` manifest/env/compose files rather than importing LightRAG internals.

Do not copy:

- The full LightRAG server bootstrap.
- LightRAG storage backends into `app/storage`.
- UI or visualizer tooling.
- Repository-wide configuration that does not match this app.
- Retrieval internals that would bypass the remote adapter boundary.
- Docker/deployment code into TUI screens or CLI service wrappers.

## Semantic Retrieval Boundary

LightRAG is the semantic retrieval plane. Context Engine no longer owns semantic chunks, embeddings, vector indexes, or graph internals.

Tests should fake the HTTP adapter boundary when they need deterministic behavior; they should not recreate a local semantic fallback.

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

## Terminal Client

The maintained operator interface is under `cli/`: launcher, credential store, and `ApiClient`, with HTTP helpers in `cli/services/`. The Rich TUI (`cli/tui/`) composes reusable ASCII layout modules from `cli/screens/` and `cli/renderers/` and optional multi-step flows under `cli/flows/`. Older Typer/`ragcli`-style notebooks under `.references/cli/` and `docs/cli_docs/` describe historical command shapes; they are not wired as entry points in `pyproject.toml` (only `cli.launcher:main`).

Do not:

- Bypass `ApiClient` with ad-hoc `httpx`/`urllib` calls scattered across unrelated packages.
- Reintroduce a parallel Typer CLI that duplicates flows without behavioral tests.

## Local Interfaces

The app owns these interfaces and models:

- `RetrievalEngine`
- `Evidence`
- `ParsedDocument`
- `NavigationIndexBuilder`
- `LightRAGRemoteAdapter`
- `LightRAGDomainService`

Adapters may change internally as reference code changes. Routes, services, and the terminal client should continue depending on the local API and schema contracts.

