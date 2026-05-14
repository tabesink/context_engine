# Retrieval engine boundaries

The app exposes semantic retrieval, document navigation, and optional remote LightRAG retrieval behind one `Evidence` model. Local semantic/navigation engines use the `RetrievalEngine` interface; remote LightRAG access stays behind an HTTP adapter and is normalized into the same evidence contract. This keeps LightRAG-style and PageIndex-style complexity isolated while giving API routes, services, answer composition, CLI commands, and tests a stable local contract.

