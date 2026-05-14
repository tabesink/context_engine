# V1 backend scope and infrastructure

V1 is a backend-only FastAPI application with no browser UI, because the highest-risk work is the document, retrieval, indexing, and access-control backend. The production-local stack is Docker Compose with PostgreSQL using the `pgvector/pgvector` image, Redis-backed workers, local filesystem document storage, and API/worker services so the app can be run end to end without committing early to hosted infrastructure. Local development can also run against the default SQLite database; real pgvector column/type usage remains a hardening item rather than a requirement for every run.

