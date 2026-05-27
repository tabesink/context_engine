# Compose/env rendering patch

In `app/lightrag_deploy/compose.py`, replace direct use of runtime app DB values with a helper.

```python
def _postgres_target_for_env(domain: LightRAGDomain, settings: LightRAGDeploySettings):
    mode = settings.postgres_provisioning_mode
    if mode == "compat":
        return (
            settings.postgres_compat_database,
            settings.postgres_compat_user,
            settings.postgres_compat_password,
        )
    if mode == "app_database_shared":
        return (
            settings.runtime_postgres_database,
            settings.runtime_postgres_user,
            settings.runtime_postgres_password,
        )
    return (
        domain.postgres_database,
        domain.postgres_user,
        settings.postgres_password,
    )
```

Then render:

```python
database, user, password = _postgres_target_for_env(domain, settings)
lines.extend([
    "LIGHTRAG_KV_STORAGE=PGKVStorage",
    "LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage",
    "LIGHTRAG_GRAPH_STORAGE=PGGraphStorage",
    "LIGHTRAG_VECTOR_STORAGE=PGVectorStorage",
    f"POSTGRES_HOST={settings.postgres_host}",
    f"POSTGRES_PORT={settings.postgres_port}",
    f"POSTGRES_DATABASE={database}",
    f"POSTGRES_USER={user}",
    f"POSTGRES_PASSWORD={password}",
    "POSTGRES_VECTOR_INDEX_TYPE=HNSW",
    f"TIKTOKEN_CACHE_DIR={settings.tiktoken_cache_dir}",
])
```

Only render Postgres block when:

```python
settings.storage_backend == "postgres"
```
