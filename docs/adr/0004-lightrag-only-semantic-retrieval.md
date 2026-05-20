# LightRAG-only semantic retrieval with per-domain PostgreSQL storage

Context Engine will act as the control plane for users, documents, domain lifecycle, jobs, status, navigation, and audit records, while LightRAG is the only semantic retrieval plane. LightRAG domain containers share the project PostgreSQL service but use one LightRAG-owned database per domain, plus a matching LightRAG workspace, so Context Engine never stores semantic chunks, embeddings, vector indexes, or graph internals.

## Considered Options

- Keep local semantic fallback through `semantic_chunks`: rejected because it makes Context Engine a second retrieval plane and hides LightRAG failures.
- Use file-based LightRAG storage: rejected for this implementation because Option 3 intentionally centralizes durable LightRAG state in PostgreSQL.
- Use one shared LightRAG PostgreSQL database with workspace-only isolation: rejected because database-per-domain gives clearer backup, restore, delete, and collision boundaries.

## Consequences

The PostgreSQL service must support both `pgvector` and Apache `AGE`, because the selected LightRAG PostgreSQL vector and graph stores require them. LightRAG credentials are generated per domain and written only to domain env files; manifests, domain list APIs, TUI screens, and audit logs must not expose those secrets.
