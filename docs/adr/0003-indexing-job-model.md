# Indexing Operation Model

Local indexing runs in Redis-backed workers instead of FastAPI request handlers, because parsing, navigation indexing, semantic indexing, and future graph work can be slow and failure-prone.

The storage table remains named `jobs`, but HTTP clients use `/operations`. The current implementation is status-driven and updates parsed data, navigation data, and LightRAG ingestion metadata in place for one document row. Successful indexing marks the document `ready`; failed indexing marks the document `failed`. A future hardening pass can replace this with a stricter versioned swap if readers must keep using the previous ready index while a rebuild is in progress.

Admin upload responses expose `operation_id` and a `processing-status` URL. The internal worker id and table name are not product API concepts.

