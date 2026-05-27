# Compose/env Patch Guidance

## app/lightrag_deploy/compose.py

Replace the current implicit check:

```python
if domain.postgres_database and domain.postgres_user:
    ...
```

with explicit storage-backend rendering:

```python
if settings and settings.storage_backend == "postgres":
    if settings.postgres_provisioning_mode == "per_domain":
        postgres_database = domain.postgres_database
        postgres_user = domain.postgres_user
        postgres_password = settings.postgres_password
    else:
        postgres_database = settings.runtime_postgres_database
        postgres_user = settings.runtime_postgres_user
        postgres_password = settings.runtime_postgres_password

    if not postgres_database or not postgres_user or not postgres_password:
        raise ValueError("LightRAG postgres storage requires database, user, and password")

    lines.extend([
        "LIGHTRAG_KV_STORAGE=PGKVStorage",
        "LIGHTRAG_DOC_STATUS_STORAGE=PGDocStatusStorage",
        "LIGHTRAG_GRAPH_STORAGE=PGGraphStorage",
        "LIGHTRAG_VECTOR_STORAGE=PGVectorStorage",
        f"POSTGRES_HOST={settings.postgres_host}",
        f"POSTGRES_PORT={settings.postgres_port}",
        f"POSTGRES_DATABASE={postgres_database}",
        f"POSTGRES_USER={postgres_user}",
        f"POSTGRES_PASSWORD={postgres_password}",
        f"POSTGRES_VECTOR_INDEX_TYPE={settings.postgres_vector_index_type}",
    ])
```

Also add explicit network aliases to the generated service:

```yaml
networks:
  context_engine_lightrag:
    aliases:
      - lightrag_fatigue
```

The generated YAML block can be rendered as:

```python
" networks:",
f"   {self.settings.docker_network}:",
"     aliases:",
f"       - {domain.service_name}",
```

instead of list-style `- network` if aliases are needed.
