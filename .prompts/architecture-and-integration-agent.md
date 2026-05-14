**Role:**
You are a senior software architect and coding agent.

---

**Objective:**
Using the provided **Development Plan: Multi-User Hybrid RAG Application**, design and implement a production-grade system by leveraging and adapting code from the following reference repositories:

* LightRAG
* PageIndex

The goal is to **combine semantic retrieval (LightRAG)** with **structured document navigation (PageIndex)** into a unified, clean, and maintainable system.

---

**Core Requirements:**

1. **System Design First**

   * Analyze both codebases and extract:

     * Core abstractions
     * Data models
     * Retrieval logic
     * Strengths and limitations
   * Map these into a **unified architecture** aligned with the development plan

2. **Code Reuse Strategy**

   * Do NOT blindly copy entire repositories
   * Identify **specific modules/files/functions** to reuse or adapt
   * Clearly justify:

     * Why each piece is reused
     * What modifications are required

3. **Unified Architecture Goals**

   * FastAPI-based backend
   * Multi-user support (5–10 users)
   * Admin-only write / ingestion permissions
   * Concurrent retrieval support
   * Clean separation of:

     * Retrieval layer (semantic + graph)
     * Index/navigation layer
     * API layer
     * Storage layer (vector DB + metadata)

4. **Hybrid Retrieval Design**

   * Combine:

     * Graph-based / semantic retrieval (LightRAG-style)
     * Hierarchical / page-level navigation (PageIndex-style)
   * Define:

     * Retrieval orchestration logic
     * When to use which method
     * How results are merged/ranked

---

**Implementation Phases:**

Break the work into clear phases:

1. **Codebase Analysis**
2. **Architecture Design**
3. **Core Retrieval Layer Implementation**
4. **Indexing & Ingestion Pipeline**
5. **API Layer (FastAPI)**
6. **Multi-user & Access Control**
7. **Testing & Validation**

---

**Output Format (STRICT):**

Produce the following sections:

### 1. Codebase Comparison

* What LightRAG does best
* What PageIndex does best
* Overlap and gaps

### 2. Unified System Architecture

* High-level diagram (textual)
* Key components and responsibilities

### 3. File/Module Plan

* Exact folder structure
* Which files are:

  * Reused
  * Adapted
  * Newly created

### 4. Integration Strategy

* How both systems are merged
* Data flow from ingestion → retrieval → response

### 5. Step-by-Step Implementation Plan

* Actionable steps for a coding agent

### 6. Risks & Design Tradeoffs

* Complexity vs performance
* Maintainability concerns
* Failure modes

---

**Constraints:**

* Code must be **understandable by a junior developer**
* Avoid over-engineering
* Prefer **clear abstractions over clever optimizations**
* Keep components **modular and testable**

---

If you want, I can go one level deeper and turn this into a **Cursor / Claude Code agent prompt with tool usage + file editing instructions** so it actually executes end-to-end.
