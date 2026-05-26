# Product Requirements Document

## 1. Product Purpose

`context_engine` is a backend service for a multi-user hybrid RAG application.

Its purpose is to let authenticated users query a shared knowledge corpus while admins manage document ingestion, document lifecycle, and LightRAG domain lifecycle.

## 2. Target Users

### Admin Users

Admins can:

- upload documents
- reingest documents
- delete/archive documents
- manage LightRAG domains
- start/stop/recreate domain services
- view indexing/job status
- configure or operate backend infrastructure

### Regular Users

Regular authenticated users can:

- list available retrieval domains
- submit retrieval requests
- receive evidence/citation results
- navigate the shared workspace tree
- inspect document/page/section-level evidence if exposed by frontend

### Developers / Coding Agents

Developers need:

- clear API map
- clear service boundaries
- predictable folder structure
- safe refactoring guidance
- documentation for retrieval and storage behavior

## 3. Core Use Cases

### UC1: Admin uploads a document

An admin uploads a document into a selected LightRAG domain. The system stores the file, tracks processing state, indexes structured document information locally, and sends the relevant content to LightRAG.

### UC2: User retrieves evidence

A user selects or defaults to a LightRAG domain and asks a plain-language question. The backend returns evidence from remote LightRAG and/or local navigation retrieval.

### UC3: User browses workspace tree

A user opens a workspace tree showing documents and document structure aligned with the selected domain.

### UC4: Admin manages LightRAG domain lifecycle

An admin creates, starts, stops, deletes, recreates, or regenerates a LightRAG domain deployment.

### UC5: Developer validates API flows

A developer or coding agent uses tests, API routes, and possibly the TUI/CLI harness to validate backend behavior before frontend integration.

## 4. Functional Requirements Implemented or Expected

| Requirement | Status | Notes |
|---|---|---|
| User authentication | Implemented | JWT/bearer-token style auth |
| Admin authorization | Implemented | Admin-only dependencies/routes |
| Document upload | Implemented | Admin route |
| Document listing | Implemented | User-readable metadata |
| Document structure retrieval | Implemented | Pages/sections/chunks/assets |
| Remote LightRAG retrieval | Implemented | Mandatory semantic backend |
| Local navigation retrieval | Implemented | Structured lookup |
| Single retrieve API | Implemented | `/retrieve` should remain canonical |
| LightRAG domain list | Implemented | User-readable domain summaries |
| LightRAG lifecycle management | Implemented/partial | Admin routes |
| Background processing | Implemented | Redis/RQ pattern |
| Workspace tree | Implemented/partial | Exposed for frontend integration |
| Query/audit logging | Implemented/partial | Privacy-oriented config exists |

## 5. Non-Functional Requirements

### Reliability

- Avoid silent fallback to local semantic retrieval.
- Surface LightRAG domain health clearly.
- Ensure indexing jobs are retryable or recoverable.
- Avoid losing uploaded files or domain state during delete/archive operations.

### Security

- Admin-only write operations.
- Regular users are read-only for shared corpus.
- Production weak secrets should be rejected.
- Wildcard CORS should not be allowed in production.
- Document shared-corpus behavior explicitly.

### Maintainability

- Keep route handlers thin.
- Keep retrieval engines modular.
- Keep LightRAG behind an adapter.
- Avoid duplicate query APIs.
- Keep settings readable and grouped.

### Observability

- Track job status.
- Track LightRAG health.
- Track retrieval route/mode.
- Log query metadata without storing raw text by default.
- Add cost/provider tracing later if LLM provider costs matter.

### Scalability

Designed scale appears to be small-team internal use, roughly 5–10 users. Current architecture is appropriate for this scale. If corpus size grows substantially, local navigation retrieval may need PostgreSQL full-text search or a precomputed search index.

## 6. Current Product Clarifications Needed

1. Is the corpus intentionally shared across all authenticated users?
2. Is CLI/TUI supported or deprecated?
3. Are LightRAG domains user-selectable by all users?
4. Should archived domain documents and associated assets be hard-deleted or retained?
5. Is production deployment expected to manage LightRAG containers locally or connect to externally managed LightRAG services?

## 7. Future Requirements

Potential future capabilities:

- per-domain access grants
- per-document visibility scopes
- provider profile management
- Bedrock OpenAI-compatible provider config
- frontend evidence panel with image/table cards
- retrieval evaluation datasets
- Langfuse or similar observability integration
- PostgreSQL full-text navigation search
- structured backup/restore tooling
