# Context Engine

Context Engine manages authenticated access to document corpora, delegates semantic retrieval to LightRAG, and keeps local metadata and navigation data for operational control and document browsing.

## Language

**LightRAG Domain**:
A named knowledge corpus hosted by a LightRAG runtime and selected by users for semantic retrieval.
_Avoid_: User instance, tenant database

**Semantic Engine**:
The retrieval system that owns chunks, embeddings, vector search, graph retrieval, and semantic ranking.
_Avoid_: Target engine, indexing backend

**Navigation**:
Local page and structure data used for document browsing, inspection, and TUI support.
_Avoid_: Local semantic index, fallback retrieval

**Document Structure**:
The Control Plane's canonical page, section, block, source chunk, and asset map for an uploaded document.
_Avoid_: LightRAG document state, semantic index

**Source Chunk**:
A Control Plane citation unit that links text spans to pages, sections, blocks, and assets before or after LightRAG retrieval.
_Avoid_: Semantic chunk, embedding chunk, vector chunk

**Asset**:
An extracted image, figure, table rendering, or thumbnail stored by the Control Plane and linked from source chunks or blocks.
_Avoid_: Image embedding, LightRAG binary payload

**TOC Refiner**:
An optional bounded LLM pass that repairs section/page ranges when deterministic document structure is weak.
_Avoid_: Parser of record, semantic retriever

**Control Plane**:
The Context Engine responsibility for users, document metadata, domain lifecycle, jobs, status, and audit records.
_Avoid_: Vector database, retrieval plane

**Retrieval Plane**:
The LightRAG responsibility for semantic chunks, embeddings, graph data, vector search, and answer evidence.
_Avoid_: Control metadata, document manager

## Relationships

- A **LightRAG Domain** belongs to the **Retrieval Plane**.
- The **Control Plane** records which **LightRAG Domain** a document was sent to.
- A **Semantic Engine** owns semantic retrieval data; **Navigation** owns local page/tree browsing data.
- **Document Structure**, **Source Chunks**, and **Assets** belong to the **Control Plane** for citation, browsing, and enrichment; they do not make Context Engine a **Semantic Engine**.
- **Navigation** can be ready or failed independently from **Semantic Engine** readiness.

## Example dialogue

> **Dev:** "Should PageIndex become another semantic engine?"
> **Domain expert:** "No. LightRAG remains the semantic engine. PageIndex can become a navigation implementation later."

## Flagged ambiguities

- "LightRAG" previously referred to a local fake embedding adapter, a remote HTTP integration, and domain deployment. Resolved: **LightRAG** now means the external semantic retrieval plane.
- "target engine" blurred semantic retrieval and navigation. Resolved: use **Semantic Engine** for LightRAG and **Navigation** for local page/tree processing.
