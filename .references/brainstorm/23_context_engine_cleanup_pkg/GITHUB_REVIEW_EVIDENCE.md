# GitHub Review Evidence

This file records the evidence used for the cleanup review. Verify against the current branch before editing.

## Repository identity and runtime

- Repository: `tabesink/context_engine`.
- README describes the project as a backend-only multi-user hybrid RAG application.
- README says semantic retrieval is mandatory through remote LightRAG while local navigation retrieval remains available.
- README prerequisites include Python 3.11+, PostgreSQL, Redis, and `DATABASE_URL`; SQLite is reserved for isolated tests.
- README canonical startup says Docker Compose runs PostgreSQL, Redis, API, worker, and LightRAG status poller.
- README documents `/health` and background execution with `INDEX_JOBS_INLINE=false`.

## Root-level inventory observed

Important folders/files observed in the repository root:

```text
.cursor-plugin/
.cursor/
.data/uploads/
.prompts/
.references/
.understand-anything/
.vs/
app/
cli/
client/
context_engine.egg-info/
docker/
docs/
external/lightrag/
migrations/
scripts/
tests/
.env.example
.env.lightrag-deploy.example
.env.lightrag-provider.example
```

Cleanup note: `.vs/`, `.data/uploads/`, `context_engine.egg-info/`, Python `__pycache__` folders, and `client/tsconfig.tsbuildinfo` should be verified as committed artifacts. If committed, they are likely safe cleanup candidates after `.gitignore` is corrected.

## Backend inventory observed

`app/` contains:

```text
api/
core/
document_processing/
domain/
indexing/__pycache__/
integrations/
lightrag_deploy/
retrieval/
schemas/
services/
storage/
workers/
main.py
```

## API route inventory observed

`app/api/routes/` contains:

```text
admin.py
ai_settings.py
auth.py
documents.py
health.py
jobs.py
lightrag.py
lightrag_admin.py
retrieve.py
users.py
workspace_tree.py
```

## Service inventory observed

`app/services/` contains:

```text
ai_model_settings_service.py
asset_urls.py
document_access_policy.py
document_asset_service.py
document_service.py
domain_purge_service.py
file_storage.py
job_service.py
lightrag_domain_lifecycle_service.py
lightrag_domain_registry.py
lightrag_failure_normalizer.py
lightrag_ingestion_service.py
lightrag_reachability_service.py
model_profile_resolver.py
processing_status_cache.py
processing_status_service.py
readiness_service.py
retrieval_asset_resolver.py
retrieval_service.py
secret_crypto.py
workspace_context_service.py
workspace_tree_service.py
```

## LightRAG deploy inventory observed

`app/lightrag_deploy/` contains:

```text
compose.py
docker_runner.py
errors.py
manifest.py
models.py
paths.py
service.py
settings.py
```

`app/lightrag_deploy/service.py` was observed as a large `LightRAGDomainService` file around 539 lines. It imports/coordinates settings, paths, manifest, compose generation, Docker runner, Postgres provisioning, model profile resolution, reachability probing, and domain models. This is the highest-value cleanup target.

## Worker inventory observed

`app/workers/` contains:

```text
status_poller.py
tasks.py
worker.py
```

## Frontend inventory observed

`client/src/` contains:

```text
api/
app/
components/
features/graph/
hooks/
lib/
stores/
types/
utils/
```

## Tests observed

The repository has broad tests covering auth, CLI, document processing, evidence mapping, LightRAG deploy/service/settings/docker runner/domain embedding/failure/graph/ingestion/Postgres/remote adapter, migrations, processing status routes/service, retrieval, rich navigation, and workspace context. Treat this as a strength and use tests as cleanup guardrails.
