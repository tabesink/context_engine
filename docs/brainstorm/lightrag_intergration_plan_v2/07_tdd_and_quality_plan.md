# 7. TDD and Quality Plan

## 7.1 Testing Principle

Test public behavior, not implementation details.

Do not require live Docker or live LightRAG for ordinary tests.

Use:

- temp directories for `.data`
- fake manifest paths
- fake Docker runner
- mocked HTTP health checks
- API TestClient for route behavior
- fake ApiClient for TUI service tests

## 7.2 Test Slices

### Slice 1: Settings and paths

Tests:

- `.env.example` contains all runtime and deployment LightRAG settings.
- Settings parse deployment fields.
- Path resolver creates domain paths under `.data/lightrag/domains/<domain>`.
- Invalid domain IDs fail.

Files:

```text
tests/test_lightrag_deploy_settings.py
tests/test_lightrag_deploy_paths.py
```

### Slice 2: Manifest read/write

Tests:

- Missing manifest returns empty domain list.
- Create domain writes deterministic manifest.
- Duplicate domain ID fails.
- Duplicate port fails.
- Manifest writes atomically.

File:

```text
tests/test_lightrag_deploy_manifest.py
```

### Slice 3: Domain storage creation

Tests:

- Create domain creates `inputs`, `rag_storage`, `artifacts`, `logs`.
- Generated `domain.env` includes header warning.
- Generated env is deterministic.

File:

```text
tests/test_lightrag_deploy_domain_files.py
```

### Slice 4: Compose generation

Tests:

- Compose file includes one service per domain.
- Compose output is deterministic.
- Compose includes correct ports and volumes.
- Compose header says generated/do-not-edit.

File:

```text
tests/test_lightrag_deploy_compose.py
```

### Slice 5: Domain service create/list/show/remove

Tests:

- `create_domain()` returns expected model.
- `list_domains()` returns configured domains.
- `remove(permanent=False)` archives domain directory.
- `remove(permanent=True)` fails unless config allows it.
- Archive path includes timestamp.

File:

```text
tests/test_lightrag_deploy_service.py
```

### Slice 6: Docker operations with fake runner

Tests:

- `up()` calls fake runner with correct service name.
- `down()` calls fake runner.
- `recreate()` calls fake runner.
- Docker error maps to typed service error.
- Health polling can be mocked.

File:

```text
tests/test_lightrag_deploy_docker_runner.py
```

### Slice 7: Admin API routes

Tests:

- Normal user cannot create/up/down/remove domains.
- Admin can create domain.
- Admin can list domains.
- Deployment disabled returns stable error.
- Permanent delete requires explicit config.

File:

```text
tests/test_lightrag_deploy_api.py
```

### Slice 8: User-safe domain list

Tests:

- Authenticated users can list domain choices.
- Response does not expose secrets or host filesystem paths.
- Unauthenticated user gets auth error.

File:

```text
tests/test_lightrag_domains_user_api.py
```

### Slice 9: Upload domain ownership

Tests:

- Admin upload with `lightrag_domain_id` stores local document mirror with domain metadata.
- Upload to missing domain fails.
- Upload to unhealthy/stopped domain fails clearly.
- If document IDs are filtered during query, selected documents must belong to selected domain.

File:

```text
tests/test_lightrag_domain_document_ownership.py
```

### Slice 10: TUI service and screens

Tests:

- `cli/services/lightrag_domains.py` calls correct API paths.
- Admin domain list screen renders fake domain table.
- User query domain selector renders only safe fields.
- TUI does not import Docker runner or deployment service.

Files:

```text
tests/test_cli_services_lightrag_domains.py
tests/test_cli_tui_lightrag_domains.py
```

## 7.3 No-Live-Dependency Rule

Default test suite must not require:

- Docker daemon
- live LightRAG service
- Neo4j
- real Redis unless existing test mode already requires it
- external network

Add optional integration tests later under a marker:

```bash
pytest -m lightrag_live
pytest -m docker_integration
```

## 7.4 Regression Behaviors to Preserve

Preserve existing behavior:

- `LIGHTRAG_ENABLED=false` keeps local upload/query path active.
- Normal users cannot upload.
- Existing graph proxy routes still work.
- Runtime adapter still normalizes evidence.
- Local navigation stays local even when LightRAG is enabled, unless a deliberate later change is made.
- CLI/TUI never calls LightRAG directly.

## 7.5 Quality Gates

Before merge:

```bash
pytest
python -m compileall app cli
```

If using generated compose tests:

```bash
docker compose -f .data/lightrag/docker-compose.lightrag-domains.yml config
```

Run the compose validation manually or in an optional integration job, not in default unit tests.

## 7.6 Code Review Checklist

- Is there one owner for each responsibility?
- Are all settings in root `.env.example`?
- Are generated files clearly marked generated?
- Does the TUI call only `cli/services/`?
- Does `cli/services/` call only Context Engine API?
- Are Docker calls hidden behind `docker_runner.py`?
- Are runtime LightRAG HTTP calls still behind `LightRAGRemoteAdapter`?
- Can Context Engine start with `LIGHTRAG_DEPLOY_ENABLED=false`?
- Can tests run without Docker/LightRAG?
- Is archive the default removal behavior?
