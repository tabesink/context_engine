# Full Codebase Review and Functional/API Surface Map Prompt for `context_engine`

Use this prompt with a coding agent, junior developer, or code-review assistant to deeply understand the `context_engine` repository before making changes.

---

# Task: Full Codebase Review and Functional/API Surface Map for `context_engine`

You are a senior software architect, backend engineer, and technical documentation lead.

Review the full codebase at:

```text
https://github.com/tabesink/context_engine.git
```

Your job is to deeply understand what this application currently does, how it is structured, what API surfaces it exposes, and how the major functional flows work.

Do **not** refactor yet.  
Do **not** propose large architectural rewrites yet.  
Do **not** assume intended behavior unless the code proves it.

First, produce a clear, evidence-based codebase understanding document that a junior developer or future coding agent can safely follow.

---

## 0. Review Philosophy

Work from the repository itself.

For every major finding, cite:

- Exact file path
- Relevant function, class, route, module, or config name
- Important environment variable names
- Important database table/model names
- Important CLI command names
- Any test file that confirms behavior

Use this evidence style:

```text
Evidence:
- app/api/routes/documents.py -> upload_document()
- app/services/indexing_service.py -> enqueue_indexing_job()
- app/models/document.py -> Document
```

If something is unclear, mark it as:

```text
Unclear / needs verification:
- ...
```

Do not invent behavior.

---

# Project Context

This repository appears to be a backend-only, multi-user hybrid RAG application.

It may include:

- FastAPI-style backend application code
- API route modules
- Authentication and user/session handling
- Admin-only functionality
- Document upload and document management
- Indexing and retrieval pipelines
- PostgreSQL persistence
- Redis or background job processing
- CLI/TUI tooling
- Docker Compose setup
- Admin user seeding
- Tests
- Documentation, prompts, and reference folders
- Possible LightRAG or external RAG integration points

The review should focus on understanding the **existing implementation**, not redesigning it yet.

---

# Primary Objectives

Produce a complete codebase understanding report that answers:

1. What does this application do?
2. What are the main runtime components?
3. What API surfaces exist?
4. What does each route do?
5. Which routes are user-facing, admin-only, internal, or health/debug routes?
6. How does authentication work?
7. How are users, roles, sessions, and permissions represented?
8. How does document upload work?
9. How does document parsing/indexing work?
10. How does retrieval/query/chat work?
11. How do background jobs work?
12. How are PostgreSQL and Redis used?
13. What data models and database tables exist?
14. What configuration and environment variables are required?
15. How is the app started locally and in Docker?
16. How does the CLI interact with the API?
17. What tests exist and what behavior do they protect?
18. Where do docs differ from the actual implementation?
19. What are the main technical tensions, duplication points, or risky areas?
20. What should a future coding agent know before safely modifying the code?

---

# Required Review Order

Follow this order strictly.

---

## 1. Repository Entry Points

Read first:

- `README.md`
- `.env.example`
- `pyproject.toml`
- `requirements.txt` or dependency files if present
- `docker-compose.yml`
- `Dockerfile`
- Any `Makefile`
- Any startup scripts
- Any deployment scripts

Document:

- How the project is intended to run
- Main Python package/module layout
- Main service dependencies
- Required environment variables
- Expected local development workflow
- Docker/Docker Compose assumptions

---

## 2. Folder Structure Map

Create a folder tree summary.

For each major folder, explain its purpose.

Example:

```text
app/
  api/              API route definitions
  core/             config, security, app wiring
  models/           database models
  schemas/          request/response DTOs
  services/         business logic
  repositories/     database access layer
  indexing/         document parsing/indexing logic
  cli/              command-line tooling
  tests/            test suite
```

Only include folders that actually exist.

---

## 3. Application Startup and Dependency Wiring

Review:

- App factory / FastAPI app creation
- Router registration
- Middleware
- CORS setup
- Dependency injection
- Database initialization
- Redis initialization
- Background worker startup
- Health/readiness logic
- Logging setup

Answer:

- What file starts the API?
- How are routes included?
- How are settings loaded?
- How are database sessions created?
- How are services injected?
- What happens on startup and shutdown?

---

## 4. API Surface Map

Find every API route.

Create a complete route table:

| Method | Path | Handler | Auth Required | Role Required | Request Model | Response Model | Tables Read | Tables Written | Purpose |
|---|---|---|---|---|---|---|---|---|---|

For every route, explain:

- What it does
- Who can call it
- What input it expects
- What it returns
- Which service layer it calls
- Which database tables/models it touches
- Whether it is used by the CLI
- Whether it appears redundant with another route

Group routes by surface:

### Health / System Routes

Examples:

- `/health`
- `/health/readiness`

### Auth Routes

Examples:

- `/auth/login`
- `/auth/me`
- `/auth/logout`

### User Routes

Examples:

- User profile
- Session
- Query routes

### Document Routes

Examples:

- Upload
- List
- Get document
- Get document structure
- Get page
- Delete document
- Reindex document

### Retrieval / Query / Chat Routes

Examples:

- Search
- Ask
- Retrieve context
- Chat/query endpoints

### Admin Routes

Examples:

- User management
- Domain management
- System management
- Document administration

### Background Job Routes

Examples:

- Indexing job status
- Retry job
- Queue inspection

### LightRAG / External RAG Routes, If Present

Examples:

- Domain CRUD
- Graph retrieval
- Semantic query proxy
- Ingestion forwarding

Do not invent route groups. Use the actual repo.

---

## 5. Auth, Roles, and Permission Boundaries

Review:

- User model
- Role model or role fields
- Password hashing
- Token creation
- JWT/session handling
- Current-user dependencies
- Admin-required dependencies
- Permission checks in routes and services

Answer:

- How does login work?
- What credentials are required?
- How is the authenticated user resolved?
- How is admin access enforced?
- What can a normal user do?
- What can an admin do?
- Are there any endpoints missing permission checks?
- Is role enforcement centralized or scattered?

Create a permissions matrix:

| Capability | Normal User | Admin | Evidence |
|---|---:|---:|---|
| Login | Yes | Yes | ... |
| Upload documents | ? | ? | ... |
| Query documents | ? | ? | ... |
| Manage users | ? | ? | ... |
| Manage domains | ? | ? | ... |
| Reindex documents | ? | ? | ... |

---

## 6. Data Model and Persistence Layer

Review:

- SQLAlchemy models or ORM models
- Pydantic schemas
- Repositories
- Database session handling
- Migrations, if present
- Seed scripts
- Admin creation scripts

Create a data model table:

| Model/Table | File | Key Fields | Relationships | Used By | Purpose |
|---|---|---|---|---|---|

Also answer:

- What tables exist?
- What are the primary relationships?
- How are users related to documents?
- How are documents related to indexing jobs?
- Is there a domain/project/workspace concept?
- Where are uploaded files stored?
- Where is parsed document structure stored?
- Where are embeddings or retrieval indexes stored, if present?
- Does the backend store semantic chunks locally?
- Does an external service own semantic retrieval?

---

## 7. Document Upload and Ingestion Flow

Trace the complete flow from request to persisted state.

Include:

1. User/admin calls upload endpoint
2. API validates request
3. File is saved
4. Document row is created
5. Parsing starts or job is queued
6. Background job processes the document
7. Parsed output is stored
8. Indexing occurs
9. Document becomes queryable

Create an end-to-end sequence diagram in ASCII:

```text
Admin/User
   |
   | POST /documents/upload
   v
API Route
   |
   v
Document Service
   |
   +--> Save file to storage
   |
   +--> Create document DB row
   |
   +--> Enqueue indexing job
             |
             v
        Worker / Indexing Service
             |
             +--> Parse document
             +--> Build navigation index
             +--> Build semantic index or forward to external retriever
             +--> Update job status
```

Then document the actual implementation with file/function evidence.

---

## 8. Indexing and Background Job Flow

Review all indexing-related code.

Answer:

- What starts indexing?
- Is indexing synchronous or asynchronous?
- Is Redis used?
- Is there a queue?
- What worker process exists?
- How are jobs represented in the database?
- What job states exist?
- How are failures handled?
- Can indexing be retried?
- Can users query while indexing is running?
- Is concurrency controlled?
- What happens if upload/indexing fails halfway?

Create a job lifecycle table:

| State | Meaning | Set By | Next State | Evidence |
|---|---|---|---|---|

---

## 9. Retrieval, Query, and RAG Flow

Trace the complete retrieval flow.

Answer:

- What endpoint receives a query?
- What request model is used?
- How is the user authenticated?
- How is the document/domain/search scope selected?
- What retriever is called?
- Is retrieval local, external, or hybrid?
- Is there reranking?
- Is there graph retrieval?
- Is there structured document navigation?
- Is there page/image/table retrieval?
- What response is returned to the user?
- Are sources/citations returned?
- Are retrieved chunks persisted or only transient?
- What happens if the retrieval engine is unavailable?

Create a sequence diagram:

```text
User
 |
 | POST /query
 v
API Route
 |
 v
Query Service
 |
 +--> Validate user access
 |
 +--> Select document/domain scope
 |
 +--> Retrieve semantic matches
 |
 +--> Retrieve structural/navigation context
 |
 +--> Merge/rank context
 |
 +--> Return answer/context/sources
```

Use actual names from the repo.

---

## 10. CLI / TUI Surface

Review all CLI-related code.

Answer:

- What CLI commands exist?
- How are they registered?
- Do they call the API or directly call services?
- Do they require login?
- Where is the API base URL configured?
- Which API endpoints are mirrored by the CLI?
- Which API routes have no CLI equivalent?
- Which CLI commands have no API equivalent?

Create a CLI table:

| Command | File | Calls API? | API Endpoint | Purpose | Auth Needed |
|---|---|---:|---|---|---|

Also identify whether the CLI is:

- A developer testing tool
- An admin tool
- A user-facing query tool
- A partial frontend substitute
- Some combination

---

## 11. Configuration and Environment Variables

Review all settings/config files.

Create an environment variable table:

| Variable | Default | Required? | Used In | Purpose | Risk If Missing |
|---|---|---:|---|---|---|

Include:

- Database settings
- Redis settings
- JWT/security settings
- Admin seed settings
- File storage settings
- Indexing settings
- External API keys
- LightRAG or retriever settings, if present
- CORS/frontend settings
- Logging settings

Also answer:

- Is `.env.example` complete?
- Are variables duplicated across config files?
- Are there hardcoded defaults that are unsafe?
- Are there deployment assumptions not documented?

---

## 12. Deployment and Runtime Topology

Review:

- Dockerfile
- docker-compose.yml
- Scripts
- Deploy configs
- Service dependencies
- Ports
- Volumes
- Database/Redis containers
- Worker containers, if any

Create a runtime topology diagram:

```text
docker-compose
 ├── api
 │    └── FastAPI app
 ├── worker
 │    └── indexing/background jobs
 ├── postgres
 │    └── app metadata
 ├── redis
 │    └── queue/cache
 └── optional external services
```

Answer:

- What containers run?
- Which services depend on which?
- Are volumes used?
- Where do uploaded documents persist?
- Is the worker separate from the API?
- Are migrations run automatically?
- How is the admin user seeded?
- What is required for local dev?
- What is required for production-like deployment?

---

## 13. Tests and Protected Behavior

Review the test suite.

Create a test map:

| Test File | What It Tests | Routes/Services Covered | Gaps |
|---|---|---|---|

Answer:

- What behavior is currently protected?
- Are auth routes tested?
- Are admin permissions tested?
- Are document uploads tested?
- Are indexing jobs tested?
- Are retrieval flows tested?
- Are failure cases tested?
- Are database migrations tested?
- Are CLI commands tested?
- What important behavior is untested?

Do not propose implementation yet. Just identify coverage and gaps.

---

## 14. Documentation vs Implementation

Review documentation only after reviewing the code.

Compare:

- README
- docs folder
- prompt/reference folders
- Architecture notes
- Comments
- Example commands

Create a mismatch table:

| Documentation Claim | Actual Implementation | Evidence | Severity |
|---|---|---|---|

Severity options:

- Low: wording issue
- Medium: confusing or incomplete
- High: docs describe behavior that does not exist
- Critical: docs would cause incorrect deployment or unsafe usage

---

## 15. API Redundancy and Surface Cleanup Candidates

Identify possible duplicate or overlapping routes.

Do **not** refactor.  
Do **not** remove anything yet.

Create a table:

| Route A | Route B | Overlap | Difference | Recommendation Later |
|---|---|---|---|---|

Also identify:

- Routes that appear unused
- Routes only used by CLI
- Routes that duplicate admin/user behavior
- Routes that mix too many responsibilities
- Routes that should maybe be split later
- Routes that should maybe be merged later

Keep this section descriptive, not prescriptive.

---

## 16. Technical Tensions and Risk Areas

Identify current implementation tensions.

Examples:

- Local retrieval vs external retrieval overlap
- Duplicate indexing paths
- Multiple sources of truth for config
- API routes bypassing service layer
- Auth checks scattered across handlers
- CLI calling services directly instead of API
- Redis required but not clearly documented
- Background jobs not concurrency-safe
- Upload and retrieval race conditions
- Tests not covering critical behavior
- Docs out of sync with code

Create a table:

| Area | Tension / Risk | Evidence | Impact | Should Investigate Later |
|---|---|---|---|---|

Do not solve yet. This is an understanding report.

---

## 17. End-to-End Workflow Maps

Document the actual implemented workflows.

At minimum include:

### Workflow A: Admin Login

```text
Admin submits credentials
 -> auth route
 -> user lookup
 -> password verification
 -> token/session returned
```

### Workflow B: Normal User Login

Same as above, noting any role differences.

### Workflow C: Admin Uploads Document

Full upload to indexing flow.

### Workflow D: User Lists Documents or Domains

Show permission and filtering behavior.

### Workflow E: User Queries / Retrieves Context

Full retrieval path.

### Workflow F: Admin Reindexes or Deletes Document

If implemented.

### Workflow G: CLI Login and API Call

If implemented.

For each workflow, include:

- Entry route or command
- Main files/functions/classes
- Database interactions
- External services
- Success path
- Failure paths

---

## 18. Codebase Map for Future Coding Agents

Produce a concise “where to go for what” section.

Example:

| Task | Start Here | Then Check | Notes |
|---|---|---|---|
| Add a new API route | app/api/... | app/schemas/... | Follow existing dependency style |
| Change auth behavior | app/core/security.py | app/api/deps.py | Check tests |
| Modify document upload | ... | ... | ... |
| Modify indexing | ... | ... | ... |
| Modify retrieval | ... | ... | ... |
| Add CLI command | ... | ... | ... |
| Add env var | ... | ... | ... |

This section should help a junior developer avoid randomly editing files.

---

# Final Deliverable Format

Create a single markdown report named:

```text
CODEBASE_UNDERSTANDING_REPORT.md
```

The report must contain:

1. Executive Summary
2. Architecture Map
3. Folder Structure
4. Startup and Dependency Wiring
5. API Surface Map
6. Auth and Permissions
7. Data Model and Persistence Layer
8. Document Upload/Ingestion Flow
9. Indexing and Background Jobs
10. Retrieval / Query / RAG Flow
11. CLI / TUI Surface
12. Configuration and Environment Variables
13. Deployment and Runtime Topology
14. Tests and Coverage
15. Documentation vs Implementation
16. API Redundancy and Cleanup Candidates
17. Technical Tensions and Risk Areas
18. End-to-End Workflow Maps
19. Codebase Map for Future Coding Agents
20. Open Questions / Unknowns

---

# Quality Bar

The report must be:

- Evidence-based
- File-path cited
- Clear enough for a junior developer
- Useful for a future coding agent
- Honest about unknowns
- Separate between “what exists now” and “what may be intended”
- Focused on understanding before refactoring

Avoid vague phrases like:

```text
The system probably...
It seems like...
This might...
```

Unless followed by evidence and marked as uncertain.

---

# Strict Non-Goals

Do not:

- Refactor code
- Delete code
- Rewrite architecture
- Add new features
- Change APIs
- Make assumptions without evidence
- Treat documentation as truth if implementation differs
- Over-focus on style or formatting issues
- Produce generic advice not grounded in this repository

---

# Optional Follow-Up After Report

After completing `CODEBASE_UNDERSTANDING_REPORT.md`, create a short second file:

```text
NEXT_REVIEW_PROMPTS.md
```

Include 3–5 recommended next prompts for future work, such as:

1. Reduce API surface redundancy
2. Simplify LightRAG integration
3. Remove fallback/local retrieval paths
4. Harden admin/user permission boundaries
5. Improve tests around upload/index/retrieval flows

Do not implement those changes yet.
