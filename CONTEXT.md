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
- **Navigation** can be ready or failed independently from **Semantic Engine** readiness.

## Example dialogue

> **Dev:** "Should PageIndex become another semantic engine?"
> **Domain expert:** "No. LightRAG remains the semantic engine. PageIndex can become a navigation implementation later."

## Flagged ambiguities

- "LightRAG" previously referred to a local fake embedding adapter, a remote HTTP integration, and domain deployment. Resolved: **LightRAG** now means the external semantic retrieval plane.
- "target engine" blurred semantic retrieval and navigation. Resolved: use **Semantic Engine** for LightRAG and **Navigation** for local page/tree processing.
