# Indexing job model

Indexing runs in Redis-backed workers instead of FastAPI request handlers, because parsing, navigation indexing, semantic indexing, and future graph work can be slow and failure-prone. Documents keep an active ready index version while a new version builds, so admin writes do not corrupt or block normal user reads.

