# V1 backend scope and infrastructure

V1 is a backend-only FastAPI application with no browser UI, because the highest-risk work is the document, retrieval, indexing, and access-control backend. The production-local stack is PostgreSQL with pgvector, Redis-backed workers, local filesystem document storage, and Docker Compose so the app can be run end to end without committing early to hosted infrastructure.

