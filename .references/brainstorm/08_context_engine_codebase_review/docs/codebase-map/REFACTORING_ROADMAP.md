# Refactoring Roadmap

## Phase 0: Documentation and Safety Checks

### Task 0.1: Add Shared-Corpus ADR

**Goal:** Document current multi-user access behavior.

**Files likely affected:**

```text
docs/adr/ADR-001-shared-corpus-access-model.md
README.md
tests/
```

**Acceptance criteria:**

- ADR says all authenticated users can read all READY shared-corpus documents.
- ADR says only admins can write.
- ADR says no per-user private corpus exists in V1.
- Tests verify admin write boundary and regular-user read boundary.

**Risk:** Low

### Task 0.2: Resolve CLI/TUI Documentation Conflict

**Goal:** Clarify whether CLI/TUI is supported.

**Files likely affected:**

```text
README.md
AGENTS.md
docs/
tests/cli/
```

**Acceptance criteria:**

- README and AGENTS.md agree.
- If TUI retained, it is documented as developer-only harness.
- If deprecated, tests/docs are marked deprecated or removed.

**Risk:** Low

## Phase 1: Low-Risk Cleanup

### Task 1.1: Normalize Evidence Response Documentation

**Goal:** Make frontend contract explicit.

**Files likely affected:**

```text
docs/
app/api/schemas/
tests/test_retrieve*.py
```

**Acceptance criteria:**

- Evidence fields documented.
- Tests assert stable fields:
  - `reference_id`
  - `document_id`
  - `document_title`
  - `source_path`
  - `chunk_id`
  - `page_number`
  - `assets`

**Risk:** Low

### Task 1.2: Add Retrieval Smoke Tests

**Goal:** Prevent accidental `/retrieve` regression.

**Files likely affected:**

```text
tests/test_retrieve*.py
```

**Acceptance criteria:**

- test unauthenticated request rejected
- test regular user can retrieve from shared ready corpus
- test admin can retrieve
- test invalid domain fails clearly
- test document filter outside domain fails clearly

**Risk:** Low

## Phase 2: Configuration and Deployment Hardening

### Task 2.1: Reject LightRAG `latest` in Production

**Goal:** Prevent deployment drift.

**Files likely affected:**

```text
app/core/config.py
.env.example
tests/test_config*.py
docs/codebase-map/CONFIGURATION_AND_DEPLOYMENT.md
```

**Acceptance criteria:**

- production/staging config rejects `LIGHTRAG_IMAGE` ending in `:latest`
- local/dev may still use latest if desired
- docs explain how to pin and upgrade

**Risk:** Low

### Task 2.2: Group Settings by Concern

**Goal:** Reduce config entropy.

**Files likely affected:**

```text
app/core/config.py
tests/test_config*.py
```

**Acceptance criteria:**

- public `get_settings()` remains stable
- settings grouped by concern internally
- existing env vars still load
- production validation tests still pass

**Risk:** Medium

## Phase 3: Storage and Schema Clarity

### Task 3.1: Document Archive/Delete Behavior

**Goal:** Define what happens to uploaded files and assets.

**Files likely affected:**

```text
docs/adr/
app/services/document_service.py
tests/test_document_delete*.py
```

**Acceptance criteria:**

- archive behavior documented
- hard-delete behavior documented
- assets/images/tables behavior documented
- tests prove expected file/storage side effects

**Risk:** Medium

### Task 3.2: Add Domain Registry Consistency Check

**Goal:** Detect DB/manifest/domain storage mismatch.

**Files likely affected:**

```text
app/services/lightrag_domain_registry.py
app/api/routes/health.py
tests/test_lightrag_domain_registry*.py
```

**Acceptance criteria:**

- health/readiness can surface domain registry mismatch
- admin can identify orphaned domain storage
- no automatic destructive cleanup without explicit admin action

**Risk:** Medium

## Phase 4: API and Service Boundary Cleanup

### Task 4.1: Add RetrievalAccessPolicy

**Goal:** Centralize retrieval authorization and document scope resolution.

**Files likely affected:**

```text
app/services/retrieval_access_policy.py
app/services/retrieval_service.py
tests/test_retrieval_access_policy.py
```

**Acceptance criteria:**

- service resolves allowed document IDs before calling engines
- V1 shared-corpus behavior preserved
- future tenant/domain ACL logic has one place to go

**Risk:** Medium

### Task 4.2: Add Retrieval Service Factory

**Goal:** Avoid concrete dependency sprawl.

**Files likely affected:**

```text
app/api/deps.py or app/core/deps.py
app/services/retrieval_service.py
tests/
```

**Acceptance criteria:**

- route obtains RetrievalService through dependency/factory
- tests can inject mock engines/adapters
- behavior unchanged

**Risk:** Medium

## Phase 5: Observability and Testing

### Task 5.1: Add Retrieval Trace Metadata

**Goal:** Make retrieval debugging easier.

**Files likely affected:**

```text
app/services/retrieval_service.py
app/retrieval/
app/storage/repositories/log_repository.py
tests/
```

**Acceptance criteria:**

- retrieval logs mode/strategy/domain/duration
- raw query text remains disabled by default
- logs help debug LightRAG vs navigation behavior

**Risk:** Low/Medium

### Task 5.2: Add Provider/LightRAG Failure Tests

**Goal:** Ensure clean failure when LightRAG is down.

**Files likely affected:**

```text
tests/test_lightrag_remote_engine.py
tests/test_retrieve*.py
```

**Acceptance criteria:**

- timeout returns clear error
- unavailable domain returns clear error
- provider failure does not crash worker/API unexpectedly

**Risk:** Low

## Phase 6: Optional Architecture Improvements

### Task 6.1: PostgreSQL Full-Text Search for Navigation

**Goal:** Improve local navigation retrieval if corpus grows.

**Files likely affected:**

```text
app/storage/tables.py
alembic/versions/
app/retrieval/rich_navigation_engine.py
tests/
```

**Acceptance criteria:**

- only implemented if brute-force lookup becomes slow
- query results remain stable
- migration is reversible or safe
- performance improvement measured

**Risk:** Medium/High

### Task 6.2: Provider Profiles

**Goal:** Support OpenAI, OpenAI-compatible Bedrock, and other providers cleanly.

**Files likely affected:**

```text
app/core/config.py
app/services/lightrag_domain_service.py
app/integrations/providers/
docs/
tests/
```

**Acceptance criteria:**

- provider config centralized
- LightRAG domain env generation can select provider profile
- secrets are not leaked
- docs cover OpenAI and Bedrock-compatible setup

**Risk:** Medium
