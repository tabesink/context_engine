# Reference Reuse Plan

The `.references/` directory is source material. V1 adapts capabilities behind local interfaces instead of copying whole repositories.

## LightRAG

Reference location: `.references/lightrag/`

Reuse ideas:

- Query API shape and FastAPI organization from `.references/lightrag/api/`.
- JWT/auth examples from `.references/lightrag/api/auth.py` and password helpers from `.references/lightrag/api/passwords.py`.
- Semantic retrieval concepts from `.references/lightrag/lightrag.py`, `base.py`, `operate.py`, and `rerank.py`.
- Storage backend patterns from `.references/lightrag/kg/`.

Adaptation:

- Wrap semantic behavior in `app/integrations/lightrag_adapter.py`.
- Convert raw semantic matches into the local `Evidence` model.
- Use PostgreSQL + pgvector as the V1 vector persistence path.
- Keep graph expansion optional in the adapter; do not expose LightRAG internals to API routes or services.

Do not copy:

- The full server bootstrap.
- All storage backends.
- UI or visualizer tooling.
- Repository-wide configuration that does not match this app.

## PageIndex

Reference location: `.references/pageindex/`

Reuse ideas:

- Page-range and PDF page retrieval concepts from `.references/pageindex/retrieve.py`.
- Page tree/index concepts from `.references/pageindex/page_index.py` and `page_index_md.py`.
- Utility conventions from `.references/pageindex/utils.py`.

Adaptation:

- Wrap navigation behavior in `app/integrations/pageindex_adapter.py`.
- Build indexes from `ParsedDocument`, not directly from raw files.
- Store navigation trees in PostgreSQL JSON fields for V1.
- Return local `Evidence` with page and section references.

Do not copy:

- Direct filesystem/PDF assumptions into retrieval engines.
- Any API client shape that bypasses the local service layer.

## Local Interfaces

The app owns these interfaces:

- `RetrievalEngine`
- `Evidence`
- `ParsedDocument`
- `NavigationIndexBuilder`
- `SemanticIndexBuilder`
- `AnswerComposer`

Adapters may change internally as reference code changes. The rest of the app should not.

