# Settings Patch Guidance

## app/core/config.py

Add:

```python
lightrag_storage_backend: str = "postgres"
lightrag_postgres_provisioning_mode: str = "per_domain"
lightrag_postgres_vector_index_type: str = "HNSW"
```

In validation:

```python
if self.lightrag_storage_backend not in {"postgres", "file"}:
    raise ValueError("LIGHTRAG_STORAGE_BACKEND must be 'postgres' or 'file'.")

if self.lightrag_postgres_provisioning_mode not in {"per_domain", "shared_runtime"}:
    raise ValueError("LIGHTRAG_POSTGRES_PROVISIONING_MODE must be 'per_domain' or 'shared_runtime'.")

if self.lightrag_storage_backend == "postgres" and not self.lightrag_postgres_password:
    raise ValueError("LIGHTRAG_POSTGRES_PASSWORD must be configured when LIGHTRAG_STORAGE_BACKEND=postgres.")
```

## app/lightrag_deploy/settings.py

Add dataclass fields:

```python
storage_backend: str = "postgres"
postgres_provisioning_mode: str = "per_domain"
postgres_vector_index_type: str = "HNSW"
database_url_for_admin: str = ""
```

In `from_app_settings()` map:

```python
storage_backend=settings.lightrag_storage_backend,
postgres_provisioning_mode=settings.lightrag_postgres_provisioning_mode,
postgres_vector_index_type=settings.lightrag_postgres_vector_index_type,
database_url_for_admin=settings.database_url,
```

Keep existing `runtime_postgres_*` fields for backward-compatible shared-runtime mode, but do not use them in per-domain mode.
