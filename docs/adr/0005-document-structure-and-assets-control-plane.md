# Document structure and assets stay in the Control Plane

Context Engine will own canonical document structure, source chunks, extracted asset metadata, asset files, thumbnails, and debug views. LightRAG remains the only semantic retrieval plane and owns semantic chunks, embeddings, vector indexes, graph data, and ranking.

## Considered Options

- Let Context Engine own semantic chunks too: rejected because it reintroduces a second retrieval plane and conflicts with ADR 0004.
- Send image bytes or full manifests to LightRAG: rejected because it couples LightRAG to Control Plane storage and bloats retrieval payloads.
- Add parallel upload/query routes for image-aware flows: rejected because existing `/admin/documents/upload` and `/query` routes already define the public contract.

## Consequences

New code should use **SourceChunk** for local citation/navigation units. Source chunks may be sent to LightRAG as text plus metadata, but Context Engine must not embed or rank them semantically. Asset routes stream authenticated files through the API and must not expose raw filesystem paths.
