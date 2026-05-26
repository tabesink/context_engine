# Database and Storage Schema

## Storage Overview

The system uses several categories of storage:

```text
PostgreSQL
  → app metadata and relational document structure

Redis
  → background job queue / worker coordination

File storage
  → uploaded source files
  → extracted assets such as images/tables/thumbnails

LightRAG domain storage
  → semantic/vector/graph/index data owned by LightRAG

Logs/audit/query metadata
  → operational/debugging records
```

## PostgreSQL Responsibilities

PostgreSQL should own application state, not LightRAG internals.

Expected persisted concepts:

- users
- roles/admin flags
- documents
- document processing status
- pages
- sections
- blocks
- chunks
- assets
- jobs
- LightRAG domain metadata/manifest entries
- audit/query logs

## Recommended Conceptual Schema

### Users

```text
users
  id
  email
  hashed_password
  is_active
  is_admin
  created_at
  updated_at
```

### Documents

```text
documents
  id
  title
  source_path
  original_filename
  lightrag_domain_id
  status
  uploaded_by_user_id
  created_at
  updated_at
  archived_at
  deleted_at
```

Important rule:

Each document should belong to exactly one LightRAG domain.

### Document Pages

```text
document_pages
  id
  document_id
  page_number
  text
  width
  height
  metadata
```

### Document Sections

```text
document_sections
  id
  document_id
  parent_section_id
  title
  level
  page_start
  page_end
  order_index
  metadata
```

### Document Chunks

```text
document_chunks
  id
  document_id
  section_id
  page_number
  text
  token_count
  order_index
  metadata
```

### Document Assets

```text
document_assets
  id
  document_id
  page_number
  chunk_id
  asset_type
  storage_path
  thumbnail_path
  caption
  metadata
```

Asset types may include:

- image
- table
- chart
- figure
- thumbnail

### Processing Jobs

```text
processing_jobs
  id
  document_id
  job_type
  status
  error_message
  attempts
  created_at
  started_at
  completed_at
```

### LightRAG Domains

```text
lightrag_domains
  id
  name
  status
  base_url
  storage_path
  container_name
  created_at
  updated_at
  last_health_check_at
```

Actual implementation may use a manifest-backed registry instead of only relational rows. The important architectural point is that domain metadata must have a single source of truth.

## File Storage Responsibilities

File storage should contain:

```text
.data/
  uploads/
  assets/
  thumbnails/
  lightrag/
    domains/
```

Recommended separation:

```text
uploaded source document
  → immutable original file

parsed assets
  → generated from original file

LightRAG domain data
  → managed by LightRAG lifecycle operations
```

## Delete vs Archive Policy

Important unresolved product decision:

When an admin archives or deletes a document/domain, what happens to associated files?

Need to define behavior for:

- uploaded source file
- extracted images
- extracted tables
- thumbnails
- local structured rows
- LightRAG indexed chunks
- LightRAG graph/vector data
- audit/query logs referencing the document

Recommended V1 policy:

```text
Archive:
  - hide from normal retrieval
  - keep source files and assets
  - keep audit/query records
  - retain recovery path

Hard delete:
  - admin-only destructive operation
  - remove local rows
  - remove uploaded files and generated assets
  - remove or rebuild LightRAG domain index
  - write audit record
```

For multi-user shared corpus, hard delete should be very explicit because it affects all users.

## Redis Responsibilities

Redis should be treated as operational infrastructure.

Owns:

- queued jobs
- worker coordination
- transient job state if RQ uses Redis state
- possibly status polling coordination

Redis should not be the only durable source for business-critical metadata.

## LightRAG Storage Responsibilities

LightRAG owns semantic retrieval internals.

This may include:

- vector index
- graph index
- key-value/index metadata
- document status storage
- cache storage
- provider-specific artifacts

Important rule:

Do not make the main app depend on LightRAG internal storage schema. Communicate through LightRAG API/adapter boundaries.

## Backup and Restore Considerations

Production backup should include:

- PostgreSQL database
- uploaded files
- generated assets if expensive to regenerate
- LightRAG domain storage directories
- domain manifest/registry
- `.env` or deployment secrets through secure secret manager

Do not rely on database backup alone if uploaded files and LightRAG domain data live on mounted volumes.

## Storage Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Uploaded files retained after domain deletion unintentionally | Medium/High | Define archive/delete policy |
| LightRAG data deleted without local metadata update | High | Lifecycle operations should be transactional or compensating |
| Domain manifest and DB disagree | High | Use one source of truth or reconciliation job |
| Asset paths break after moving storage root | Medium | Store relative paths and centralize storage config |
