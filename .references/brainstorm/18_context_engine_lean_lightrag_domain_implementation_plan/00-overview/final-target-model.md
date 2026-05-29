# Final Target Model

## Lifecycle

```text
Create -> Stopped/Configured -> Start -> Running -> Stop -> Stopped -> Delete -> Deleted/Archived
```

## Create

Create configures a domain. It does not boot Docker.

Admin provides:

```text
domain_id
display_name
embedding_profile_id
host_port / auto port
```

Admin does not provide:

```text
start=true
retrieval defaults
advanced retrieval presets
repair/recreate/regenerate choices
```

## Start

Start is the only runtime boot path. It internally does all required preparation.

```text
Start
  -> ensure domain folders
  -> resolve runtime config
  -> read current provider secrets
  -> use locked domain embedding snapshot
  -> write domain.env
  -> write generated Compose file
  -> ensure/provision Postgres
  -> docker compose build/up
  -> health check
  -> persist status
```

## Stop

Stop stops the running container and persists stopped/error status.

## Delete

Delete removes the domain from active use safely.

```text
Delete
  -> remove from domains.json
  -> rewrite Compose without domain service
  -> move runtime folder to deleted/archive folder
  -> mark lifecycle archived/deleted
  -> preserve local documents and structure
```

## Runtime retrieval defaults

Retrieval defaults are not product settings. They are backend/deployment config values written to `domain.env`.

Preferred source:

```text
app/core/config.py / LightRAGDeploySettings
  -> write_domain_env()
  -> .data/lightrag/domains/<id>/domain.env
  -> LightRAG container
```

## Provider/model settings

AI Settings remain product-facing.

```text
Provider keys can change.
Model profiles can change.
Default LLM can change.
Default embedding profile can change.
```

But running containers only pick up changes after restart.

```text
Provider/model setting changed -> affected running domains need Stop/Start or restart notice.
```
