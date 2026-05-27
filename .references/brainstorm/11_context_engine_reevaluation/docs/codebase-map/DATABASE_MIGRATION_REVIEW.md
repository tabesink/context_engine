# Database and Migration Review

## Main Finding

The ORM appears ahead of the visible migration chain.

The code defines new AI settings and secret storage tables, but the visible migrations do not appear to create them.

## Tables/Columns to Verify

### AI Settings Tables

Required if backend uses ORM rows:

```text
ai_model_profiles
ai_model_settings
ai_provider_secrets
```

### Document Domain Fields

Verify migrations create:

```text
documents.lightrag_domain_id
```

Also verify the repository writes it during document creation.

### Optional Future Fields

Recommended for stronger provider/domain consistency:

```text
documents.embedding_profile_id
documents.embedding_fingerprint
documents.ingestion_status
lightrag_domains.provider_profile_id
lightrag_domains.embedding_profile_id
lightrag_domains.embedding_fingerprint
lightrag_domains.embedding_locked_at
```

If domains remain manifest-backed, these fields may live in the manifest instead of DB. But the source of truth must be explicit.

## Required Migration Plan

### Migration N: AI Settings Tables

Create:

```text
ai_model_profiles
ai_model_settings
ai_provider_secrets
```

Add uniqueness constraints:

```text
ai_model_profiles.id unique
ai_provider_secrets.secret_name unique
```

### Migration N+1: Document Domain Column

If missing:

```text
ALTER TABLE documents ADD COLUMN lightrag_domain_id TEXT NULL;
CREATE INDEX ix_documents_lightrag_domain_id ON documents(lightrag_domain_id);
```

Backfill from JSON metadata if possible.

### Migration N+2: Optional Embedding Fingerprint Fields

If needed:

```text
documents.embedding_fingerprint TEXT NULL
documents.embedding_profile_id TEXT NULL
```

## Migration Acceptance Criteria

- Fresh database can run all migrations.
- Existing database can migrate without data loss.
- `/admin/ai-settings` works after migration.
- Admin upload writes domain ID.
- Workspace tree can query ready documents by domain.
- Tests cover migration-created schema expectations.

## Runtime Smoke Tests

Run:

```bash
alembic upgrade head
pytest tests/test_ai_settings*.py
pytest tests/test_lightrag*.py
pytest tests/test_retrieve*.py
pytest tests/test_workspace_tree*.py
```

Then manually verify:

```text
GET /admin/ai-settings as admin
PUT /admin/ai-settings/provider-secrets/OPENAI_API_KEY
POST /admin/lightrag/domains
POST /admin/documents/upload
POST /retrieve
GET /lightrag/domains/{domain_id}/workspace-tree
```
