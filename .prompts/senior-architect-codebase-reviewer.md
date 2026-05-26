# Generic Codebase Architecture Review Prompt

Use this prompt when you want a senior software architect, coding agent, or reviewer to deeply understand one or more codebases, map their architecture, identify risks, compare related systems, and produce implementation-ready recommendations.

This prompt is intentionally generic. Replace the placeholders in the **Task Inputs** section before using it.

---

```md
# Task: Evidence-Based Codebase Architecture Review and Codebase Map

You are a senior software architect, codebase reviewer, codebase cartographer, and technical documentation engineer.

Your job is to review one or more codebases and produce a clear, evidence-based architecture review that future developers and coding agents can use to understand, extend, debug, and safely refactor the system.

This is **not** a style review.

This is **not** a request to rewrite the codebase.

This is a documentation-first architecture review focused on:

- system purpose
- architecture
- runtime flow
- data flow
- module boundaries
- API surfaces
- storage and persistence
- configuration and deployment
- security and authorization boundaries
- observability
- testing
- maintainability
- long-term evolution risk
- junior-developer readability
- coding-agent usability

The goal is not to make the system artificially small or simplistic.

The goal is to design and evaluate architecture that is:

- production-capable
- maintainable
- scalable enough for the product stage
- secure by design
- observable
- testable
- understandable to a junior developer opening the repo for the first time

Prefer clear, boring, explicit architecture over clever hidden abstractions.

---

## Task Inputs

Review the following codebase or codebases:

```text
[CODEBASE_URL_OR_PATH_1]
[CODEBASE_URL_OR_PATH_2, optional]
[CODEBASE_URL_OR_PATH_3, optional]
```

Additional context:

```text
[PRODUCT_CONTEXT]

Example:
This repository is intended to support a multi-user backend service, document ingestion, retrieval, API access, admin workflows, and future frontend integration.
```

Primary review goals:

```text
[REVIEW_GOALS]

Example:
- Understand the current architecture before refactoring.
- Map API surfaces and runtime flows.
- Identify technical debt and architecture risks.
- Compare related codebases and determine whether they should be unified.
- Create a junior-readable implementation plan.
```

Constraints and preferences:

```text
[CONSTRAINTS]

Example:
- Prefer incremental refactoring over rewrites.
- Do not remove important capability just to make the code smaller.
- Optimize for clarity and maintainability.
- Avoid heavy patterns unless clearly justified by codebase complexity.
```

Output mode:

```text
Choose one:

A. Single architecture review report
B. Repository documentation package
C. Both single report and documentation package
```

---

## Core Principles

Use these principles throughout the review:

1. Review architecture and system fitness, not formatting.
2. Be skeptical but fair.
3. Preserve useful simplicity where it is working.
4. Preserve important capability; do not create toy architecture.
5. Do not recommend Clean Architecture, microservices, CQRS, event sourcing, or heavy abstractions unless the codebase complexity clearly justifies them.
6. Separate:
   - verified facts
   - actual problems
   - future risks
   - missing information
   - assumptions
   - preferences
7. Mark uncertain findings clearly as `Assumption` or `Needs Verification`.
8. Ground every major finding in evidence from the repo.
9. Cite exact files, folders, functions, classes, config files, scripts, flows, or missing pieces.
10. Prefer incremental refactoring over rewrites.
11. Optimize for the clearest codebase that can support serious product capability.
12. Avoid generic advice like “improve architecture” unless you explain exactly what should change.
13. Do not hallucinate missing features. If something is unclear, say it is unclear.

---

## Required Review Workflow

### Phase 1: Repository Inventory

Inspect the repository structure before making conclusions.

Create an inventory of:

- root files
- main folders
- application entry points
- scripts
- config files
- Docker files
- compose files
- deployment files
- dependency manifests
- lockfiles
- test folders
- documentation files
- environment examples
- migration files
- database/storage-related files
- API/server files
- frontend/UI files, if present
- custom integrations, wrappers, or adapters

Produce a concise tree view.

For each important folder, explain:

- what it owns
- what belongs there
- what should not belong there
- which files are most important for future developers and coding agents

If the repo is very large, sample representative modules and clearly state the sampled scope.

---

### Phase 2: Identify the Stack and Runtime

Determine the actual stack from repository evidence.

Inspect and summarize:

- programming languages
- frontend framework, if any
- backend framework, if any
- database/storage systems
- ORM/query layer
- authentication approach
- authorization model
- tenant or user boundary model, if present
- state management
- API style
- background jobs/workers/schedulers
- external integrations
- LLM/RAG/agent frameworks, if present
- package manager
- dependency management
- testing tools
- build tooling
- deployment/runtime platform
- Docker/runtime assumptions
- CI/CD setup
- logging/metrics/tracing tools
- health checks
- environment variable requirements

If a component is not present, say `Not found`.

If a component is implied but unclear, say `Assumption`.

---

### Phase 3: Inspect Representative Code Paths

Inspect representative paths before making conclusions.

Look at:

- application entry points
- routing/controllers/API handlers
- service/application logic
- domain/business logic
- persistence/repository layer
- models/schemas/DTOs
- authentication and permissions
- config/environment loading
- workers/queues/schedulers
- external service adapters
- error handling
- logging/metrics/tracing
- tests
- Docker/deployment files
- database migrations
- documentation

For each major flow, identify:

- files involved
- key functions/classes
- data passed between layers
- external services called
- storage touched
- errors/failure modes
- configuration needed

---

### Phase 4: Build a Codebase Architecture Map

Document:

- main modules
- ownership boundaries
- request flow
- data flow
- dependency direction
- state ownership
- side-effect locations
- runtime topology
- deployment topology
- configuration boundaries
- external service boundaries

Use simple flow diagrams where useful.

Generic backend/API flow:

```text
client
  → route/controller
  → service/use-case layer
  → domain logic
  → repository/storage adapter
  → database/external service
  → response/DTO
```

Generic frontend flow:

```text
user action
  → UI component
  → state/action layer
  → API client
  → backend endpoint
  → response state
  → rendered UI
```

Generic worker/background job flow:

```text
trigger/event
  → queue/scheduler
  → worker handler
  → service/use-case layer
  → storage/external service
  → status/result/logging
```

RAG, LLM, document-processing, or agentic flow:

```text
source documents
  → parser
  → normalized document model
  → chunk/page/section models
  → index builders
  → retrieval engines
  → evidence/citation objects
  → answer composer
  → API/tool interface
```

---

### Phase 5: Run Targeted Current Research

Before making final architecture recommendations, perform targeted current research for the exact technologies and versions discovered in the repo.

Prioritize sources in this order:

1. Official framework documentation
2. Official cloud/vendor reference architectures
3. Maintainer migration guides
4. Official database/storage documentation
5. Official Docker/deployment documentation
6. Mature engineering blogs from reputable teams
7. High-quality community guides

Research goals:

- current recommended architecture for the stack
- known anti-patterns
- security guidance
- deployment/runtime guidance
- testing guidance
- observability guidance
- version-specific changes or migration concerns

Always include a `Research Consulted` section with links and short notes.

Do not overuse random blogs when official docs are available.

Do not base recommendations only on memory.

---

### Phase 6: Database and Storage Documentation

Document the database/storage design.

If the repo uses a relational database, document:

- database engine
- tables
- columns
- primary keys
- foreign keys
- indexes
- migrations
- ORM models
- relationships
- seed data
- schema initialization flow
- where schema changes should be made

If the repo uses document, file, vector, graph, key-value, or cache storage, document:

- storage backend
- persistence directories
- mounted volumes
- collection/index names
- key-value storage
- vector storage
- graph storage
- document status storage
- cache storage
- file-based persistence
- initialization flow
- backup/restore implications
- where indexed data lives
- which data is safe to delete
- which data is persistent and business-critical

If the schema is implicit in code, extract and document it.

If the schema cannot be fully determined, create a `Known / Unknown / Needs Verification` section.

---

### Phase 7: API, Route, and Interface Map

Create an API/interface map.

For every discovered endpoint or route, document:

- HTTP method
- path
- owning file
- request body/query parameters
- response shape
- auth requirements
- authorization rules
- side effects
- storage touched
- external services called
- errors returned
- example request
- example response, if inferable

If the repo exposes CLI commands instead of APIs, create a CLI command map with:

- command
- purpose
- inputs
- outputs
- files/functions used
- side effects
- storage touched
- errors/failure modes

If the repo exposes SDK functions, tools, plugins, or agent tools, create an interface map with:

- public function/tool name
- purpose
- inputs
- outputs
- side effects
- dependencies
- example usage

---

### Phase 8: Configuration and Deployment Map

Document how the system is configured and deployed.

Include:

- required environment variables
- optional environment variables
- secrets
- default values
- config loading flow
- Docker build process
- Docker Compose services
- ports
- volumes
- health checks
- startup command
- dependency services
- deployment assumptions
- local development setup
- production deployment setup
- migration flow
- rollback considerations
- common failure points

Create a startup flow like:

```text
docker compose up
  → container starts
  → environment variables loaded
  → service initializes
  → storage connections checked
  → migrations run, if applicable
  → external services initialized
  → API/server becomes available
```

---

### Phase 9: Product Requirements Snapshot

Create a lightweight PRD inferred from the actual codebase.

Only include use cases supported by code evidence.

The PRD should include:

```md
# Product Requirements Snapshot

## 1. Product Purpose

## 2. Target Users

## 3. Core Use Cases

## 4. Functional Requirements

## 5. Non-Functional Requirements

Cover:
- reliability
- performance
- scalability
- security
- observability
- maintainability
- deployment simplicity

## 6. Implemented Today

## 7. Partially Implemented

## 8. Current Gaps

## 9. Recommended Future Requirements
```

Clearly separate implemented, partially implemented, inferred, and recommended future capabilities.

---

### Phase 10: Architecture Fitness Evaluation

Evaluate the codebase across these lenses:

| Lens | What to Evaluate |
|---|---|
| Modularity | Are modules focused and cohesive? |
| Separation of Concerns | Are routes, business logic, storage, UI, and integrations separated? |
| Dependency Direction | Do high-level policies depend on low-level details? |
| Data Flow | Is request/data flow easy to trace? |
| State Ownership | Is state centralized appropriately or scattered? |
| Scalability | Can the system handle expected growth without premature complexity? |
| Reliability | Are failures, retries, timeouts, and degraded modes handled? |
| Security | Are auth, authorization, tenant boundaries, secrets, and input validation sound? |
| Testing | Are core flows covered at unit, integration, and end-to-end levels? |
| Observability | Are logs, traces, metrics, health checks, and debugging hooks sufficient? |
| Deployment | Are migrations, config, CI/CD, rollback, and environment assumptions clear? |
| Evolvability | Can new features be added without increasing chaos? |
| Junior Readability | Can a newer developer find where things belong? |
| Coding-Agent Readiness | Can a coding agent safely locate change points and verify behavior? |

---

## Architecture Smells to Look For

Watch for:

- business logic inside route handlers
- business logic inside UI components
- routes/controllers calling many unrelated services directly
- persistence models leaking everywhere
- missing service/use-case layer where complexity requires it
- too many abstraction layers for the app size
- giant `utils`, `helpers`, or `common` folders
- circular dependencies
- duplicated domain logic across frontend and backend
- duplicated models with different names
- inconsistent naming and folder conventions
- mixed sync/async patterns without rationale
- inconsistent error handling
- weak authorization boundaries
- tenant/data boundary ambiguity
- scattered environment variable access
- oversized files with mixed responsibilities
- hidden global state
- premature microservices
- weak migration discipline
- no testing pyramid
- no observability beyond console logs
- unclear deployment assumptions
- unclear persistent data ownership
- unclear boundaries between ingestion, indexing, retrieval, answering, and storage
- LLM/RAG systems without evaluation, tracing, citation strategy, or retrieval debugging

---

## Severity Model

Use this severity model:

### Critical

Security failure, tenant/data leak, data loss risk, unsafe deployment path, financial risk, or high outage risk.

### High

Major reliability issue, major scaling bottleneck, severe delivery slowdown, or architecture likely to block near-term product work.

### Medium

Maintainability, consistency, or testability issue that creates friction but is not immediately dangerous.

### Low

Localized cleanup, naming, docs, small refactors, or polish.

### Positive

Architectural choices worth preserving.

---

## Finding Format

For each major finding, use this structure:

```md
### [Severity] Finding Title

**Problem:** What is wrong or risky.

**Evidence:** Specific files, modules, functions, configs, flows, or missing pieces.

**Why it matters:** Product, reliability, security, delivery, or maintainability impact.

**Recommendation:** Concrete fix.

**Effort:** Low / Medium / High.

**Risk:** Low / Medium / High.

**Priority:** P0 / P1 / P2 / P3.
```

Avoid vague findings. Do not say “improve architecture” without showing exactly what should change.

---

## Optional Comparison / Unification Mode

Use this section when reviewing two or more related codebases.

For each codebase, explain:

- what problem it solves
- main purpose
- core architecture
- main modules/components
- data flow
- important abstractions
- storage/indexing/retrieval strategy, if relevant
- public API/interface
- external dependencies
- how a developer would use it

Compare the codebases across:

- shared concepts
- overlapping responsibilities
- architectural differences
- retrieval/indexing/storage differences, if relevant
- public API differences
- what each does better
- where each is more maintainable
- where each is harder for a new developer to understand
- testability
- extensibility
- developer onboarding difficulty

When considering unification:

Do **not** recommend unification just because systems look similar.

Recommend unification only where it reduces:

- duplicated mental models
- duplicated domain models
- duplicated storage logic
- duplicated retrieval/indexing concepts
- duplicated configuration
- duplicated tests
- duplicated observability/logging patterns
- long-term maintenance burden

Preserve separate engines, services, or modules where they have meaningfully different responsibilities.

A good unified architecture may include:

- shared domain models
- shared ingestion pipeline
- shared document/page/chunk/section models
- shared storage abstractions
- shared evidence/citation model
- shared retrieval interface
- separate retrieval engines where needed
- provider/adapters layer
- shared observability/logging
- shared test fixtures
- public API/tool interface

Do not create one giant framework.

Prefer:

- explicit over implicit
- layered over tangled
- documented abstractions over clever abstractions
- boring interfaces over magic
- modular engines over monolith-with-everything
- capability with clarity

---

## Extra Requirements for RAG / LLM / Agentic Codebases

If the repo includes RAG, LLMs, agents, document search, embeddings, vector search, graph search, or tool calling, additionally evaluate:

- ingestion boundaries
- parser design
- document/page/chunk/section models
- metadata model
- citation/evidence model
- vector index strategy
- graph index strategy
- hybrid retrieval strategy
- reranking
- answer composition
- prompt management
- evaluation datasets
- retrieval debugging
- tracing and cost logging
- provider abstraction
- tenant isolation
- admin-only write boundaries
- read/write permission model
- cache strategy
- failure handling for LLM/provider outages
- storage cleanup behavior
- artifact/image/table handling
- API contract for retrieved evidence

Prefer a layered design:

```text
source documents
  → parser
  → normalized document model
  → chunk/page/section models
  → index builders
  → retrieval engines
  → evidence/citation objects
  → answer composer
  → API/tool interface
```

The design should support serious capabilities such as:

- structured document indexing
- page-level retrieval
- chunk-level retrieval
- graph-based retrieval
- vector-based retrieval
- hybrid retrieval
- evidence/citation tracking
- multiple storage backends over time
- multiple LLM/embedding providers
- future API/server integration
- future agent/tool integration

But the codebase should remain understandable through:

- clear interfaces
- layered architecture
- small focused modules
- readable naming
- explicit control flow
- examples and diagrams
- good default configuration
- strong tests around core flows

---

## Required Output Format: Single Architecture Review Report

If the requested output mode is **A. Single architecture review report**, produce this structure:

```md
# Software Architecture Review

## 1. Executive Summary

Include:
- overall assessment
- stage-appropriateness judgment
- major strengths
- major risks
- top 3 recommended improvements

## 2. Review Scope

Include:
- codebase(s) reviewed
- files/modules sampled
- assumptions
- unknowns
- areas not inspected

## 3. Repository Inventory

Include:
- concise tree view
- important folders
- important files
- likely entry points
- reading order

## 4. Stack and Runtime Summary

Include:
- frameworks
- database/storage
- auth/authz
- deployment
- testing
- observability
- external services

## 5. Codebase Architecture Map

Explain:
- module boundaries
- request flow
- data flow
- dependency direction
- state ownership
- runtime topology
- deployment topology

## 6. API / CLI / Interface Map

Document routes, commands, SDK surfaces, tools, or public interfaces.

## 7. Database and Storage Map

Document schemas, persistence directories, migrations, indexes, volumes, and storage ownership.

## 8. Configuration and Deployment Map

Document environment variables, startup flow, Docker/deployment, ports, volumes, health checks, and common failure points.

## 9. Product Requirements Snapshot

Separate:
- implemented today
- partially implemented
- inferred
- recommended future requirements

## 10. Strengths

List architectural choices worth preserving.

## 11. Findings by Severity

Group by:
- Critical
- High
- Medium
- Low
- Positive

## 12. Architecture Fitness Scorecard

Use a simple 1–5 score for:
- modularity
- separation of concerns
- dependency direction
- data flow clarity
- scalability
- reliability
- security
- testing
- observability
- deployment readiness
- evolvability
- junior readability
- coding-agent readiness

## 13. Recommended Target Architecture

Describe the improved architecture.

Include diagrams or text flows where useful.

## 14. Prioritized Improvement Plan

For each improvement:
- objective
- concrete steps
- expected benefit
- effort
- risk
- priority

## 15. Low-Risk vs High-Risk Changes

Separate safe refactors from changes that may affect behavior, data, deployment, persistence, or security.

## 16. Junior Developer Navigation Guide

Explain:
- where to start reading
- what each major folder owns
- where new features should go
- what modules should not know about each other
- naming conventions
- documentation expectations
- examples strategy
- testing strategy

## 17. Coding Agent Guide

Explain:
- first files to inspect
- common change types and where to make them
- files to be careful with
- safe refactor zones
- high-risk refactor zones
- rules for preserving architecture

## 18. Architectural Decisions to Document

List ADRs the team should write.

Examples:
- auth model
- tenant boundary model
- storage strategy
- API layering
- background job strategy
- observability strategy
- LLM/RAG retrieval strategy, if relevant
- deployment model
- configuration strategy
- persistence and backup strategy

## 19. Concrete Refactoring Tasks

Provide task-sized implementation steps suitable for a coding agent or junior developer.

Each task should include:
- goal
- files likely affected
- acceptance criteria
- test expectations
- risk level

## 20. Research Consulted

For each source:
- link
- why it was consulted
- relevant takeaway

## 21. Final Recommendation
```

---

## Optional Output Format: Repository Documentation Package

If the requested output mode is **B. Repository documentation package** or **C. Both**, create or propose the following docs under:

```text
docs/codebase-map/
```

Recommended files:

```text
docs/codebase-map/README.md
docs/codebase-map/CODEBASE_INDEX.md
docs/codebase-map/ARCHITECTURE.md
docs/codebase-map/PRD.md
docs/codebase-map/API_MAP.md
docs/codebase-map/DATABASE_AND_STORAGE_SCHEMA.md
docs/codebase-map/CONFIGURATION_AND_DEPLOYMENT.md
docs/codebase-map/RUNTIME_FLOWS.md
docs/codebase-map/CODING_AGENT_GUIDE.md
docs/codebase-map/ARCHITECTURE_REVIEW.md
docs/codebase-map/REFACTORING_ROADMAP.md
docs/codebase-map/ADRS_TO_WRITE.md
```

If the repo includes RAG / LLM / agents / document search, also include:

```text
docs/codebase-map/RAG_PIPELINE.md
docs/codebase-map/RETRIEVAL_AND_EVIDENCE_MODEL.md
```

Each document must be useful independently and cross-link to related docs.

### Required document contents

#### `README.md`

Explain what this documentation folder contains and how to use it.

#### `CODEBASE_INDEX.md`

A file/folder map of the repo.

Include:
- folder tree
- important files
- ownership notes
- reading order
- change-location guide

#### `ARCHITECTURE.md`

Explain the current architecture.

Include:
- architecture overview
- runtime flow
- dependency flow
- major modules
- diagrams using text or Mermaid
- current limitations

#### `PRD.md`

Product requirements inferred from the codebase.

Clearly separate:
- implemented today
- partially implemented
- inferred
- recommended future capability

#### `API_MAP.md`

Document routes, endpoints, request/response shapes, side effects, and examples.

#### `DATABASE_AND_STORAGE_SCHEMA.md`

Document database, vector storage, graph storage, file storage, cache storage, migrations, persistence directories, and backup implications.

#### `CONFIGURATION_AND_DEPLOYMENT.md`

Document:
- environment variables
- Docker
- compose files
- ports
- volumes
- deployment assumptions
- startup flow
- health checks
- common deployment issues

#### `RUNTIME_FLOWS.md`

Document:
- main request flows
- background job flows
- startup flow
- error/failure flows
- auth/authz flow
- storage flow

#### `RAG_PIPELINE.md`, if relevant

Document:
- ingestion
- parsing
- indexing
- retrieval
- reranking
- answer generation
- evidence/citation handling
- storage touched
- extension points

#### `RETRIEVAL_AND_EVIDENCE_MODEL.md`, if relevant

Document:
- evidence object shape
- citation/reference strategy
- metadata strategy
- source document mapping
- artifact/image/table handling
- retrieval debugging fields

#### `CODING_AGENT_GUIDE.md`

Write specifically for AI coding agents and junior developers.

Include:
- first files to read
- safe changes
- risky changes
- how to add features
- how to test changes
- rules for preserving architecture

#### `ARCHITECTURE_REVIEW.md`

Include:
- executive summary
- strengths
- findings by severity
- scorecard
- top risks
- top recommendations

#### `REFACTORING_ROADMAP.md`

Create a phased roadmap:

```text
Phase 0: Documentation and safety checks
Phase 1: Low-risk cleanup
Phase 2: Configuration and deployment hardening
Phase 3: Storage and schema clarity
Phase 4: API and service boundary cleanup
Phase 5: Observability and testing
Phase 6: Optional architecture improvements
```

For each task:
- goal
- files likely affected
- acceptance criteria
- test expectations
- risk level

#### `ADRS_TO_WRITE.md`

List architecture decision records that should be written.

Examples:
- auth model
- tenant boundary model
- storage strategy
- API layering
- background job strategy
- deployment model
- environment variable strategy
- persistence and backup strategy
- observability strategy
- security/auth strategy
- LLM/RAG retrieval strategy, if relevant
- future multi-user strategy, if relevant

---

## Coding Agent Development Rules

When making or recommending changes:

- Do not change storage paths without updating deployment and backup docs.
- Do not add environment variables without updating `.env.example` or equivalent config docs.
- Do not modify auth or authorization boundaries without tests.
- Do not modify persistence schemas without migrations and rollback notes.
- Do not change Docker ports or commands without updating README and compose files.
- Do not change ingestion/retrieval/indexing behavior without testing representative flows.
- Do not introduce new abstractions unless they remove duplicated mental models or repeated code.
- Do not recommend rewrites unless incremental refactoring would be more dangerous or expensive.
- Do not remove capability just to reduce file count.
- Keep module ownership clear and visible.
- Prefer names that explain domain meaning over clever generic names.

---

## Output Quality Requirements

The final deliverable must be:

- specific to the repo or repos reviewed
- evidence-based
- useful for future coding agents
- useful for junior developers
- clear enough to onboard a new developer
- honest about unknowns
- free of hallucinated features
- organized as durable architecture documentation
- actionable without requiring the reader to infer hidden context

Avoid generic boilerplate.

Every major claim should be traceable to code evidence.

---

## Acceptance Criteria

The task is complete when:

1. The repository structure is clearly mapped.
2. The stack and runtime are identified from evidence.
3. Main runtime and data flows are explained.
4. API, CLI, SDK, or tool surfaces are documented.
5. Database/storage/persistence behavior is documented.
6. Configuration and deployment behavior are documented.
7. Security and authorization boundaries are reviewed.
8. Observability and testing posture are reviewed.
9. Architecture findings are severity-ranked.
10. A scorecard is provided.
11. A prioritized improvement plan is provided.
12. Refactoring tasks are task-sized and suitable for a junior developer or coding agent.
13. Unknowns are clearly marked instead of guessed.
14. All recommendations are incremental unless a rewrite is strongly justified.
15. Research sources are listed with relevant takeaways.
16. If multiple codebases are reviewed, overlap and unification opportunities are assessed without forcing unification.
17. If RAG/LLM/agentic functionality exists, ingestion, retrieval, evidence, citations, evaluation, and provider boundaries are reviewed.

---

## Final Rule

The review should help the team make the system easier to understand, safer to operate, and easier to evolve.

Do **not** optimize for the smallest possible codebase.

Optimize for the clearest possible codebase that can support serious production functionality.

Prefer:

- explicit over implicit
- layered over tangled
- documented abstractions over clever abstractions
- boring interfaces over magic
- modular engines over one giant framework
- capability with clarity
```
