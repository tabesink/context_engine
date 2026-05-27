# Settings patch

Add these fields to `app/core/config.py::Settings`:

```python
lightrag_storage_backend: str = "postgres"
lightrag_postgres_provisioning_mode: str = "per_domain"
lightrag_postgres_compat_enabled: bool = True
lightrag_postgres_compat_database: str = "lightrag"
lightrag_postgres_compat_user: str = "lightrag"
lightrag_postgres_compat_password: str = "lightrag"
lightrag_postgres_admin_database: str = "context_engine"
lightrag_postgres_vector_extension: str = "vector"
lightrag_postgres_age_extension: str = "age"
lightrag_tokenizer_offline: bool = True
lightrag_tiktoken_cache_dir: str = "/app/.cache/tiktoken"
```

Add matching fields to `LightRAGDeploySettings`:

```python
storage_backend: str = "postgres"
postgres_provisioning_mode: str = "per_domain"
postgres_compat_enabled: bool = True
postgres_compat_database: str = "lightrag"
postgres_compat_user: str = "lightrag"
postgres_compat_password: str = "lightrag"
postgres_admin_database: str = "context_engine"
postgres_vector_extension: str = "vector"
postgres_age_extension: str = "age"
tokenizer_offline: bool = True
tiktoken_cache_dir: str = "/app/.cache/tiktoken"
```

Map them in `LightRAGDeploySettings.from_app_settings()`.

Add validation:

```python
if self.lightrag_storage_backend not in {"postgres", "file"}:
    raise ValueError("LIGHTRAG_STORAGE_BACKEND must be postgres or file")

if self.lightrag_postgres_provisioning_mode not in {"per_domain", "compat", "app_database_shared"}:
    raise ValueError("Invalid LIGHTRAG_POSTGRES_PROVISIONING_MODE")
```
