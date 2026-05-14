# Indexing job model

Local indexing runs in Redis-backed workers instead of FastAPI request handlers, because parsing, navigation indexing, semantic indexing, and future graph work can be slow and failure-prone. Documents keep an active ready index version while a new version builds, so admin writes do not corrupt or block normal user reads. When `LIGHTRAG_ENABLED=true`, admin upload forwarding is delegated to the remote LightRAG service and the local response may have no local indexing `job_id`.

