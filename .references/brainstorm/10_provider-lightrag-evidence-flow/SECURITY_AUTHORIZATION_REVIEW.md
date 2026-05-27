# Security and Authorization Review

## Required Product Posture

```text
Admin
  → configure providers
  → manage API keys/secrets
  → create/manage LightRAG domains
  → upload/reingest/delete/archive documents

Regular authenticated user
  → select available domain
  → ask questions
  → view evidence/context panel
  → view workspace tree
  → cannot modify providers/domains/documents
```

## Current Strengths

- Backend has `get_current_user` and `require_admin` style dependencies.
- Admin document upload is admin-only.
- Admin LightRAG lifecycle routes are admin-only.
- `/retrieve` uses authenticated user, not admin requirement.
- Workspace tree uses authenticated user, not admin requirement.

## Provider Secret Requirements

Provider API key handling must obey:

- never return raw API key in any response
- never log raw API key
- never expose secrets to regular users
- only admin can write/update provider secrets
- UI displays only masked state, e.g. `sk-...abcd` or `Configured`
- test endpoint returns health/error, not secret details

## Secret Storage Options

### Option A: Environment-managed provider

Lowest risk for local/internal deployment.

```text
.env contains provider secrets
admin UI shows read-only environment-managed profile
```

### Option B: Database-stored encrypted provider profiles

More flexible but requires encryption/key management.

```text
provider_profiles table
encrypted_api_key column or secret_ref
application secret/key encrypts values
```

### Option C: External secret manager

Best for production maturity, but likely too much for current local small-team deployment.

## Recommended V1

Support both:

```text
Environment-managed default provider profile
  + optional DB-backed admin-created provider profiles if encryption is implemented
```

If encryption is not implemented, do not pretend DB secret storage is production-grade. Document the local-trusted assumption.

## Required Authorization Tests

- regular user cannot create/update/delete provider profile
- regular user cannot see raw/masked secret-management fields beyond safe status
- regular user cannot upload documents
- regular user cannot create/start/stop/delete LightRAG domain
- regular user can retrieve from ready domain
- regular user can view workspace tree
- unauthenticated requests fail
