# 08 — Patch Targets

## Backend files to add

```text
app/schemas/workspace_context.py
app/services/workspace_context_service.py
```

## Backend files to modify

```text
app/api/routes/workspace_tree.py
app/schemas/retrieval.py
app/retrieval/evidence_mapper.py
```

Possible supporting files to inspect:

```text
app/storage/repositories/document_processing.py
app/storage/repositories/documents.py
app/services/document_access_policy.py
app/services/lightrag_domain_registry.py
app/document_processing/models.py
```

## Backend tests to add or modify

```text
tests/services/test_workspace_context_service.py
tests/api/test_workspace_context.py
tests/retrieval/test_evidence_mapper.py
```

Use current test naming conventions if different.

## Frontend files to add

```text
client/src/api/workspace-context.ts
```

## Frontend files to modify

```text
client/src/types/chat.ts
client/src/api/workspace-tree.ts
client/src/lib/api/retrieve.ts
client/src/lib/retrieve-response-adapter.ts
client/src/stores/chat-session-store.ts
client/src/components/chat/SidePanel.tsx
client/src/components/chat/WorkspaceTree.tsx
client/src/components/chat/LightRagChatShell.tsx
```

## Optional future extraction

After first implementation works, consider extracting:

```text
client/src/components/chat/ContextStreamTab.tsx
client/src/components/chat/SourceNavigatorTab.tsx
client/src/components/chat/SourceBreadcrumb.tsx
client/src/components/chat/SourceAssetCard.tsx
```

Do not extract prematurely if it makes the first patch harder to review.

## Important current contracts

Workspace tree node IDs currently follow:

```text
domain:{domain_id}
document:{document_id}
section:{document_id}:{section_id}
page:{document_id}:{page_number}
chunk:{document_id}:{chunk_id}
asset:{document_id}:{asset_id}
```

The source-context endpoint should treat these IDs as opaque from the frontend perspective and parse them only on the backend.

## Files not to create

Avoid creating:

```text
client/src/components/chat/SecondSidePanel.tsx
app/api/routes/source_browser.py
app/services/source_browser_service.py
```

Reason: the workspace tree and side panel already exist. Extend them to avoid UI/API duplication.
