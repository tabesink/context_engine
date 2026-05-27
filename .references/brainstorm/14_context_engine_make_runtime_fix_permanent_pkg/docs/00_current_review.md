# 00 — Current Review

## Current symptom

The temporary runtime fix worked because it created the missing compatibility objects:

```text
role: lightrag
database: lightrag
extension: vector
```

That explains why the error stopped:

```text
FATAL: password authentication failed for user "lightrag"
DETAIL: Role "lightrag" does not exist.
```

and why `http://127.0.0.1:9622/health` became healthy.

## What the current codebase still does

### 1. Domain creation always assigns per-domain Postgres names

`LightRAGDomainService.create_domain()` currently sets:

```python
postgres_database=f"{self.settings.postgres_database_prefix}_{postgres_suffix}"
postgres_user=f"{self.settings.postgres_user_prefix}_{postgres_suffix}"
```

This means a domain like `fatigue` is intended to have:

```text
postgres_database = lightrag_fatigue
postgres_user     = lightrag_fatigue
```

That is good, but incomplete unless those DB objects are actually provisioned before container startup.

### 2. `domain.env` still renders runtime/app DB credentials instead of per-domain credentials

`render_domain_env()` currently renders the Postgres storage block when `domain.postgres_database` and `domain.postgres_user` exist, but uses:

```python
POSTGRES_DATABASE={settings.runtime_postgres_database}
POSTGRES_USER={settings.runtime_postgres_user}
POSTGRES_PASSWORD={settings.runtime_postgres_password}
```

This is the central bug. It mixes app runtime database credentials with LightRAG domain-level database identity.

The permanent fix is:

```python
POSTGRES_DATABASE={domain.postgres_database}
POSTGRES_USER={domain.postgres_user}
POSTGRES_PASSWORD={settings.lightrag_postgres_password}
```

or, if using compatibility mode:

```python
POSTGRES_DATABASE=lightrag
POSTGRES_USER=lightrag
POSTGRES_PASSWORD={settings.lightrag_postgres_password}
```

### 3. There is no Postgres provisioner

The code creates the manifest/env/compose, but it does not create:

- Postgres role
- Postgres database
- required extensions
- privileges

So the current system can generate a `domain.env` that references a role/database that does not exist.

### 4. `up()` and `recreate()` do not repair dependencies

`LightRAGDomainService.up()` currently writes compose and starts the domain. It should first provision Postgres objects and regenerate `domain.env`.

Target order:

```text
get domain
ensure paths
ensure Postgres role/database/extensions
write domain.env
write compose
recreate/up container
probe health
persist status
```

### 5. Registry still trusts persisted `base_url`

`LightRAGDomainRegistry.get_required()` reads `base_url` directly from manifest. This is fragile because Docker mode can change. Runtime URL should be computed:

```text
socket mode -> container_base_url
host mode   -> host_base_url
```

### 6. Tokenizer DNS startup issue remains separate

The managed `context_engine_lightrag_fatigue` container is failing due tokenizer/tiktoken DNS startup. The Dockerfile currently downloads tiktoken cache during build, but runtime still needs an explicit offline/stable cache path. Permanent fix:

- Mount/cache tiktoken files inside the image.
- Set `TIKTOKEN_CACHE_DIR` in generated `domain.env`.
- Avoid startup-time downloads.
- Optionally set tokenizer cache fallback env vars used by LightRAG/tiktoken.

## Conclusion

The current temporary SQL fix is valid as a compatibility bridge, but the permanent implementation must happen in the domain lifecycle service.
