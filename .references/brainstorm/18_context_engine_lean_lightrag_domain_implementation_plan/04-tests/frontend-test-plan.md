# Frontend Test Plan

## Create form

Assert visible fields are only:

```text
Domain ID
Display name
Embedding model
Host port mode/custom port
Create button
```

Assert these are absent:

```text
Advanced retrieval defaults
retrieval preset
Top K
Chunk Top K
Rerank Top K
token budgets
```

## Domain lifecycle card

Assert lifecycle actions shown:

```text
Start or Stop
Delete
```

Assert absent:

```text
Repair
Recreate container
Regenerate config
Preview purge
Purge permanently
```

## API client

Assert no methods exist for:

```text
repair
recreate
regenerate
purgePreview
purge
```

Assert create payload excludes:

```text
start
retrieval default fields
```

## Notices

After provider setting changes, show either immediate notice or global banner:

```text
Running LightRAG domains need restart to use updated provider settings.
```

This can be simple in first implementation.
