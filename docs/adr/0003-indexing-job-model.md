# Indexing job model

Local indexing runs in Redis-backed workers instead of FastAPI request handlers, because parsing, navigation indexing, semantic indexing, and future graph work can be slow and failure-prone.

The current implementation is status-driven and updates parsed data, navigation data, and semantic chunks in place for one document row. Successful indexing marks the document `ready` and bumps its `active_index_version`; failed indexing marks the document `failed`. A future hardening pass can replace this with a stricter versioned swap if readers must keep using the previous ready index while a rebuild is in progress.

When `LIGHTRAG_BASE_URL=http://localhost:9621`, admin upload forwarding is delegated to the remote LightRAG service and the local response may have no local indexing `job_id`.

