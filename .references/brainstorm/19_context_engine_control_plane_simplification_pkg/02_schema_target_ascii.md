# Target Control-Plane Schema ASCII Diagrams

## Current simplified view

```text
┌────────────┐
│ users      │
└─────┬──────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│ documents                                           │
│ owner_id -> users.id                                │
│ lightrag_domain_id = plain string                   │
│ status = document availability                      │
└──────────────┬──────────────────────────────────────┘
               │
               ├── document_pages
               ├── document_sections
               ├── document_blocks
               ├── document_source_chunks
               └── document_assets

┌──────────────────────────────┐
│ lightrag_domain_lifecycle    │
│ domain_id                    │
│ state                        │
│ metadata                     │
└──────────────────────────────┘

┌──────────────────────────────┐
│ jobs                         │
│ kind                         │
│ status                       │
│ document_id only             │
└──────────────────────────────┘
```

## Target mental model

```text
┌────────────┐
│ users      │
└─────┬──────┘
      │
      ├───────────────────────────────┐
      │                               │
      ▼                               ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│ documents               │    │ operations              │
│ stable registry         │    │ all long-running work   │
│ current doc status      │◄───│ resource_type/id        │
└───────────┬─────────────┘    │ progress/status         │
            │                  └───────────▲─────────────┘
            │                              │
            ▼                              │
┌─────────────────────────┐                │
│ document read model     │                │
│ pages                   │                │
│ sections                │                │
│ blocks                  │                │
│ source_chunks           │                │
│ assets                  │                │
└─────────────────────────┘                │
                                           │
┌─────────────────────────┐                │
│ lightrag_domains        │────────────────┘
│ first-class domain row  │
│ state + health + config │
└─────────────────────────┘
```

## Target runtime state contract

```text
┌──────────────────────────────┐
│ documents.status             │
├──────────────────────────────┤
│ uploaded                     │
│ indexing                     │
│ ready                        │
│ failed                       │
│ deleted                      │
└──────────────────────────────┘
            │
            │ rollup/current availability
            ▼
┌──────────────────────────────┐
│ operations.status            │
├──────────────────────────────┤
│ queued                       │
│ running                      │
│ succeeded                    │
│ failed                       │
│ canceled                     │
└──────────────────────────────┘
            ▲
            │ source of truth for active work
            │
┌──────────────────────────────┐
│ lightrag_domains.state       │
├──────────────────────────────┤
│ creating                     │
│ stopped                      │
│ starting                     │
│ running                      │
│ stopping                     │
│ failed                       │
│ deleted                      │
└──────────────────────────────┘
```

## Duplicate relationship cleanup

Before:

```text
sections.block_ids JSON  ───────────────┐
                                         ├── duplicate relationship
blocks.section_id scalar ───────────────┘

blocks.asset_ids JSON ──────────────────┐
                                         ├── duplicate relationship
assets.block_id scalar ─────────────────┘
```

After:

```text
sections.parent_section_id   canonical section tree relation
blocks.section_id            canonical section -> block relation
assets.block_id              canonical block -> asset relation
assets.chunk_id              canonical chunk -> asset relation
```

Derived API response shape can still include arrays if the UI needs them.
