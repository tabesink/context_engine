# Retrieval engine boundaries

The app exposes semantic retrieval and document navigation as separate engines behind one `RetrievalEngine` interface and one `Evidence` model. This keeps LightRAG-style and PageIndex-style complexity isolated in adapters while giving API routes, services, answer composition, and tests a stable local contract.

