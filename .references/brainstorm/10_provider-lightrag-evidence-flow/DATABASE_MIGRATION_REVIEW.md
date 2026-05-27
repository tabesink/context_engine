# Database and Migration Review

## Current Schema Readiness

The inspected table definitions include users, documents, document structure, source chunks, assets, jobs, audit logs, and query logs.

A provider profile table was not found in the inspected schema.

The inspected LightRAG domain models also do not appear to contain provider profile or embedding-lock metadata.

## Required Schema Additions

Recommended minimal schema:

```text
provider_profiles
  id
  name
  provider_type
  base_url
  api_key_encrypted or api_key_secret_ref
  api_key_masked_hint
  default_llm_model
  allowed_llm_models_json
  default_embedding_model
  allowed_embedding_models_json
  embedding_dim
  embedding_token_limit
  is_active
  created_by
  created_at
  updated_at
```

Domain registry/model additions:

```text
lightrag_domain.provider_profile_id
lightrag_domain.llm_model
lightrag_domain.embedding_model
lightrag_domain.embedding_dim
lightrag_domain.embedding_token_limit
lightrag_domain.embedding_locked_at
lightrag_domain.first_ingested_document_id
```

Document additions, if not already available through metadata:

```text
document.lightrag_domain_id
document.embedding_model
document.embedding_dim
document.ingestion_status
```

## If Domains Are Manifest-Backed

If the source of truth is a JSON manifest rather than DB table, add these fields to the manifest schema and provide migration/backfill code for existing manifests.

Required manifest migration behavior:

- old domains load with null provider/embedding fields
- admin must configure provider before new ingestion
- do not infer embedding model silently if documents already exist
- provide explicit admin remediation message

## Migration Safety

Required migrations/tests:

- create provider profile table
- add domain/provider/embedding fields or manifest version bump
- backfill environment-managed default provider profile
- verify existing documents/domains still list
- verify upload fails clearly until domain provider is configured
- verify rollback risk is documented

## Schema Readiness Matrix

| Requirement | Current Readiness | Recommendation |
|---|---|---|
| Provider profile persistence | Missing/unclear | Add provider profile model/table or explicit env-managed profile abstraction |
| API key redaction | Missing/unclear | Add redacted response schema and tests |
| Domain provider linkage | Missing/unclear | Add provider_profile_id or provider snapshot |
| Domain embedding identity | Missing/unclear | Add embedding model/dim fields |
| Embedding lock | Missing | Add lock timestamp/invariant check |
| Document-domain linkage | Appears present | Keep and test domain-required upload |
| Evidence source fields | Mostly present | Add any missing UI fields like section_id/page_number if needed |
