# Review Checklist: Entropy Cleanup PRs

Use this checklist for each PR.

## Architecture boundary

- [ ] Remote LightRAG is the only semantic retrieval backend.
- [ ] Local navigation retrieval remains available.
- [ ] Hybrid retrieval means LightRAG + navigation.
- [ ] No local embeddings are added.
- [ ] No local vector DB is added.

## Config

- [ ] `LIGHTRAG_ENABLED=false` fails clearly.
- [ ] Missing required LightRAG config fails clearly.
- [ ] `.env.example` documents LightRAG as required.
- [ ] Error messages are clear enough for a junior developer to debug.

## Retrieval

- [ ] `semantic` mode uses remote LightRAG only.
- [ ] `hybrid` mode uses LightRAG and navigation.
- [ ] `navigation` mode uses navigation only.
- [ ] `auto` mode is LightRAG-first.
- [ ] LightRAG failure does not silently fall back to navigation.
- [ ] No code says `semantic_engine=self.navigation_engine`.

## Ingestion

- [ ] Upload cannot bypass LightRAG semantic ingestion.
- [ ] Local structure/navigation extraction remains intact.
- [ ] Structure parsing failure behavior is explicit.
- [ ] Unknown LightRAG statuses are not silently treated as indexing.

## Persistence

- [ ] Runtime code does not write local semantic chunks.
- [ ] Runtime code does not read local semantic chunks.
- [ ] Dropping `semantic_chunks` is staged and reviewed separately if needed.
- [ ] Source chunks/assets/navigation tables are preserved.

## Tests

- [ ] Config tests cover mandatory LightRAG.
- [ ] Retrieval tests cover all modes.
- [ ] Upload/ingestion tests cover LightRAG-only path.
- [ ] Regression tests prove navigation/document APIs still work.
- [ ] Full test suite passes.

## Docs

- [ ] README updated.
- [ ] `.env.example` updated.
- [ ] Relevant docs updated.
- [ ] Old local semantic fallback references removed or corrected.
