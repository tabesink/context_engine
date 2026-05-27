# ADRs to Write

## ADR-001: Provider Profile Model

Decision:

- How providers, base URLs, model names, and API key references are represented.
- Whether provider profiles are global, per-domain, or both.

Recommended:

```text
Global AIModelProfile rows.
Domain stores embedding profile snapshot.
Default LLM profile remains global unless product requires per-domain LLM.
```

## ADR-002: API Key and Secret Handling

Decision:

- Whether secrets are env-only, DB-encrypted, or both.
- How UI-saved secrets are used by domain deployment.
- What masking/redaction is required.

Recommended:

```text
Support encrypted DB secrets for local trusted deployments.
Never return raw keys.
Allow env-managed secrets as fallback.
```

## ADR-003: LightRAG Domain Embedding Lock

Decision:

- Whether embedding profile can change after domain creation or ingestion.

Recommended:

```text
Domain embedding can be changed only while domain is empty.
After first successful ingestion, full reindex is required.
```

## ADR-004: Provider vs LLM vs Embedding UI Semantics

Decision:

- How Settings → Provider explains LLM and embedding defaults.

Recommended:

```text
Provider route manages credentials and model profiles.
Embedding model is domain-critical.
LLM model is runtime/default behavior and may be changed more freely.
```

## ADR-005: Canonical Retrieval API

Decision:

- Whether `/retrieve` is the only chat/evidence retrieval endpoint.

Recommended:

```text
Use /retrieve as canonical.
Do not introduce duplicate query endpoints.
```

## ADR-006: Evidence and Context Panel Contract

Decision:

- Stable fields backend must return for context panel and workspace tree linking.

Recommended contract:

```text
reference_id
document_id
document_title
source_path
chunk_id
section_id
section_title
page_number
page_start
page_end
score
text
assets
metadata
```

## ADR-007: Workspace Tree Source of Truth

Decision:

- Whether workspace tree is populated from retrieval evidence or dedicated endpoint.

Recommended:

```text
Use dedicated workspace-tree endpoint for tree.
Use retrieval evidence to highlight/select nodes.
```

## ADR-008: Shared Corpus Read Model

Decision:

- Whether all authenticated users can read all ready documents in visible domains.

Recommended:

```text
V1 shared corpus.
Admin-only writes.
Regular users can retrieve and view workspace tree.
```
