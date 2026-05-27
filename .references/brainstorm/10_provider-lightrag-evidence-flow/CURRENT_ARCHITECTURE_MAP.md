# Current Architecture Map

## Backend Routes Observed

The FastAPI app registers routes for:

```text
admin
auth
documents
health
jobs
lightrag
lightrag_admin
retrieve
workspace_tree
```

No provider/settings route was observed in the registered backend route list.

## Current Backend Flow

```text
Admin document upload
  → /admin/documents/upload
  → require_admin
  → DocumentService.upload(..., lightrag_domain_id)
  → validate LightRAG domain
  → store upload + document metadata
  → queue ingestion job
  → worker / LightRAG ingestion service
  → parse document into local structure/chunks/assets
  → send source chunks to LightRAG domain
```

```text
Authenticated user retrieval
  → POST /retrieve
  → get_current_user
  → RetrievalService.retrieve(...)
  → validate selected LightRAG domain
  → route retrieval strategy
  → remote LightRAG semantic evidence and/or local navigation evidence
  → map to EvidenceResponse / AssetResponse
```

```text
Authenticated user workspace tree
  → GET /lightrag/domains/{domain_id}/workspace-tree
  → get_current_user
  → WorkspaceTreeService.build_for_domain(...)
  → domain root
  → readable ready documents
  → sections/pages/chunks/assets
```

## Current LightRAG Provider Configuration Flow

The current provider-related pieces appear to be configuration driven:

```text
.env.lightrag-provider.example
  → app/core/config.py settings
  → app/lightrag_deploy/compose.py render_domain_env / _append_provider_env
  → generated LightRAG domain.env files
  → LightRAG domain service/container runtime
```

This is useful, but it is not the same as an admin-managed provider profile UI/API.

## Current Frontend Flow

```text
Next.js client
  → /chat page
  → LightRagChatShell
  → ChatComposer
  → RetrievalSettingsPopover
  → streamBackendMessage(...)
  → onContext / onMetadata / onProgress / onChunk callbacks
  → WorkspaceTree component from chat source tree
  → SidePanel context items
```

## Missing Target Links

```text
Settings Provider page
  → missing/unclear

Admin Provider API
  → missing/unclear

ProviderProfile persistence
  → missing/unclear

Domain provider_profile_id / embedding_model lock
  → missing/unclear

Frontend chat → backend /retrieve contract
  → mismatch/unclear

RetrieveResponse → ContextPanelItem adapter
  → missing/unclear

Workspace tree frontend → backend workspace-tree endpoint
  → missing/unclear
```
