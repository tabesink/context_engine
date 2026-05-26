# Junior Dev Implementation Plan

## Goal

Stabilize the workspace-tree endpoint as a lightweight frontend navigation contract while keeping detailed document content behind existing lazy-load document APIs.

## Expected Contract

- `GET /lightrag/domains/{domain_id}/workspace-tree` remains authenticated and backward-compatible.
- `GET /lightrag/domains/{domain_id}/workspace-tree?depth=2&include_assets=true` is the recommended first WebUI navigation request.
- `depth` is optional. When omitted, the endpoint returns the existing full reference tree.
- `include_assets` is optional and defaults to `true` to preserve current behavior.
- Workspace-tree nodes remain limited to:
  - `domain`
  - `document`
  - `section`
  - `page`
  - `chunk`
  - `asset`
- The tree must not expose full page text or full chunk text.
- Detailed content is loaded from existing document endpoints:
  - `GET /documents/{document_id}/structure`
  - `GET /documents/{document_id}/sections/{section_id}`
  - `GET /documents/{document_id}/pages/{page_number}`
  - `GET /documents/{document_id}/chunks/{chunk_id}`

## Implementation Slices

1. Add workspace-tree query parameters.
   - Add `depth: int | None` with `ge=1`.
   - Add `include_assets: bool = true`.
   - Pass both values from the route into `WorkspaceTreeService`.

2. Preserve existing default behavior.
   - If `depth` is omitted, return the same full tree shape as before.
   - If `include_assets` is omitted, keep asset nodes in the response.

3. Apply depth during tree building.
   - Treat the root domain node as depth `0`.
   - Documents are depth `1`.
   - A `depth=2` response includes domain, documents, and direct document children only.
   - Do not attach children to nodes at the requested max depth.

4. Gate asset nodes.
   - When `include_assets=false`, omit all `asset` nodes.
   - Keep chunk metadata stable even when linked assets are not rendered as nodes.

5. Move domain filtering into the repository query.
   - `list_ready_by_lightrag_domain()` should filter `READY` status and LightRAG domain metadata in SQL.
   - Preserve support for both `metadata.lightrag.domain_id` and legacy `metadata.lightrag.domain`.

6. Keep lazy content loading unchanged.
   - Do not change existing document detail endpoints.
   - Document them as the source for page/chunk/section detail payloads.

## Verification

Run:

```bash
uv run pytest tests/test_api.py -k workspace_tree -q
```

Then run:

```bash
uv run pytest tests/test_api.py -k "structure or sections or pages or chunks" -q
```
