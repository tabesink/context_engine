# Review Checklist Before WebUI Wiring

Use this after implementation and before wiring the lifted WebUI.

## Backend route

- [ ] `GET /lightrag/domains/{domain_id}/workspace-tree` exists.
- [ ] Route requires authenticated user.
- [ ] Route validates domain ID.
- [ ] Route returns 404 for unknown domain.
- [ ] Route returns empty root for valid domain with no ready documents.
- [ ] Route is registered in `app/main.py`.

## Response shape

- [ ] Top-level response includes `domain_id`.
- [ ] Top-level response includes `display_name`.
- [ ] Top-level response includes `document_count`.
- [ ] Top-level response includes `root`.
- [ ] Root node kind is `domain`.
- [ ] Document nodes have `document_id`.
- [ ] Section nodes have `section_id`.
- [ ] Page nodes have `page_number`.
- [ ] Chunk nodes have `chunk_id`.
- [ ] Asset nodes have `asset_id`.
- [ ] Asset nodes use URLs, not inline binary data.
- [ ] Full chunk text is not returned in the tree response.
- [ ] Full page text is not returned in the tree response.

## Domain/document filtering

- [ ] Documents are filtered by `metadata.lightrag.domain_id`.
- [ ] Fallback `metadata.lightrag.domain` is supported if needed.
- [ ] Wrong-domain documents are excluded.
- [ ] Not-ready documents are excluded.
- [ ] Deleted/failed/indexing documents are excluded from user workspace tree.
- [ ] No host ports or container details are used to identify domains.

## Local navigation

- [ ] Tree uses `DocumentProcessingRepository.get_structure()`.
- [ ] Sections are nested by `parent_section_id`.
- [ ] Pages are sorted by page number.
- [ ] Chunks are represented by references.
- [ ] Assets are represented by references and thumbnail URLs.
- [ ] Missing structure for one document does not break the entire tree.
- [ ] Documents with no structure include `metadata.structure_available = false`.

## Low-entropy architecture

- [ ] No Easy Deploy `source_tree_snapshots` copied.
- [ ] No `/api/v1/*` compatibility routes added.
- [ ] No port-based domain routing added.
- [ ] No new database table added.
- [ ] No migration added for first pass.
- [ ] No WebUI code changed in this task.
- [ ] No full page text or full chunk text is returned by the workspace tree.
- [ ] Any future flat `SourceTreeSnapshot` conversion is left to a WebUI adapter.

## Known first-pass choke points

- [ ] Python metadata filtering is accepted for the current scale and documented as the future indexing point.
- [ ] One `get_structure()` call per domain document is accepted for V1 and not hidden behind premature batching.
- [ ] Tree-building logic lives in one backend service so route handlers stay thin.

## Tests

- [ ] Service tests added.
- [ ] API tests added.
- [ ] Auth failure tested.
- [ ] Missing domain tested.
- [ ] Empty domain tested.
- [ ] Domain filtering tested.
- [ ] Structure node creation tested.
- [ ] Existing test suite still passes.

## Ready for WebUI wiring

Only wire the WebUI after this checklist passes.

The WebUI should then call:

```http
GET /lightrag/domains
GET /lightrag/domains/{domain_id}/workspace-tree
```

and use existing document detail routes when users click tree nodes:

```http
GET /documents/{document_id}
GET /documents/{document_id}/sections/{section_id}
GET /documents/{document_id}/pages/{page_number}
GET /documents/{document_id}/chunks/{chunk_id}
GET /documents/{document_id}/assets/{asset_id}
GET /documents/{document_id}/assets/{asset_id}/thumbnail
```
