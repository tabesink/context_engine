# Junior Dev Mental Model

## The simple rule

```text
Users see four lifecycle buttons.
Developers keep technical complexity inside private helpers.
```

## Four product actions

### Create

Creates a domain configuration.

It writes metadata and generated files, but it does not start the LightRAG container.

### Start

Starts the LightRAG container.

Start is smart. It refreshes runtime files and provider secrets before booting.

### Stop

Stops the LightRAG container.

It does not delete domain files or documents.

### Delete

Removes the domain from active use.

It is safe delete/archive, not hard purge. Local document history remains.

## What went away

### Repair

Removed because Start should be the only boot/recovery path.

### Recreate

Removed because Docker force-recreate is an implementation detail.

### Regenerate

Removed because env/Compose generation is an internal helper.

### Purge

Removed because hard delete is dangerous and adds too much surface area.

### Retrieval defaults in UI

Removed because tuning knobs like `top_k` and token budgets are deployment configuration, not normal product settings.

## Provider and embedding model rules

```text
Provider API key can change.
Running containers need restart to use changed keys.
Embedding model is selected when creating a domain.
After ingestion, embedding model should be treated as locked.
```

## Why this helps

A junior developer should not need to ask:

```text
Should I click Start, Repair, Recreate, or Regenerate?
```

They should understand:

```text
Start is the only thing that boots or refreshes runtime config.
```
