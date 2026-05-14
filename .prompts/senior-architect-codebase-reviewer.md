You are a senior software architect and codebase reviewer.

Review and compare these two codebases:

- https://github.com/HKUDS/LightRAG.git
- https://github.com/VectifyAI/PageIndex.git

Your goal is to understand their function, purpose, architecture, overlap, differences, and possible unification strategy.

Important clarification:
The goal is NOT to make the system overly simple or lightweight by removing important capability.

The goal is to design a powerful, extensible, production-capable architecture that is still easy for a junior developer to understand when they open the codebase.

That means:
- clear module boundaries
- readable naming
- explicit data flow
- well-documented abstractions
- minimal hidden magic
- examples near the code
- predictable folder structure
- architecture that can grow without becoming chaotic

Review Objectives:

1. Understand Each Codebase

For each codebase, explain:
- What problem it solves
- Its main purpose
- Core architecture
- Main modules/components
- Data flow
- Important abstractions
- Storage/indexing/retrieval strategy
- External dependencies
- How a developer would use it

2. Compare Them

Compare LightRAG and PageIndex across:
- shared concepts
- overlapping responsibilities
- architectural differences
- retrieval differences
- indexing differences
- storage differences
- what each does better
- where each is more maintainable
- where each is harder for a new developer to understand

3. Identify Unification Opportunities

Analyze whether the two systems can be unified without creating a bloated framework.

Consider:
- shared ingestion pipeline
- shared document/page/chunk/section models
- shared retrieval interface
- shared evidence/citation model
- shared storage abstractions
- separate retrieval engines where appropriate
- common agent/tool interface
- shared observability/logging
- shared tests and examples

Important:
Do not recommend unification just because two systems look similar.
Recommend unification only where it reduces duplicated mental models, duplicated code, or long-term maintenance burden.

4. Preserve Capability While Improving Understandability

The unified design should not be “toy code.”

It should support advanced capabilities such as:
- structured document indexing
- page-level retrieval
- chunk-level retrieval
- graph-based retrieval
- vector-based retrieval
- hybrid retrieval
- evidence/citation tracking
- multiple storage backends over time
- multiple LLM/embedding providers
- future API/server integration
- future agent/tool integration

But the codebase should remain understandable through:
- clear interfaces
- layered architecture
- small focused modules
- readable naming
- explicit control flow
- examples and diagrams
- good default configuration
- strong tests around core flows

5. Reduce Code Debt and Entropy

Look for:
- duplicated concepts
- duplicated models
- duplicated storage logic
- unclear naming
- hidden control flow
- over-generalized abstractions
- files that are too large
- weak boundaries between ingestion, indexing, retrieval, and answering
- places where a junior developer would not know where to start

6. Recommend a Unified Architecture

Propose an architecture that is powerful but understandable.

The architecture should include:
- core domain models
- ingestion layer
- indexing layer
- retrieval layer
- answer-generation layer
- storage layer
- provider/adapters layer
- observability/logging layer
- public API or tool interface layer

Use a layered design such as:

source documents
  → parser
  → normalized document model
  → index builders
  → retrieval engines
  → evidence objects
  → answer composer
  → API/tool interface

7. Junior-Readable Codebase Requirements

The final recommendation should explain how a junior developer would navigate the codebase.

Include:
- suggested folder structure
- where to start reading
- what each module owns
- what modules should not know about each other
- naming conventions
- documentation strategy
- examples strategy
- testing strategy
- comments/docstrings strategy

8. Output Format

Produce the final review in this structure:

# Codebase Review: LightRAG vs PageIndex

## 1. Executive Summary

## 2. LightRAG Overview

## 3. PageIndex Overview

## 4. Shared Concepts

## 5. Key Differences

## 6. What Each Codebase Excels At

## 7. Maintainability and Understandability Findings

## 8. Code Debt / Entropy Risks

## 9. Recommended Unified Architecture

## 10. Proposed Folder Structure

## 11. Core Interfaces and Data Models

## 12. Retrieval Strategy

## 13. Storage Strategy

## 14. Observability and Debugging Strategy

## 15. Documentation Strategy for Junior Developers

## 16. Migration Plan

## 17. Concrete Refactoring Tasks

## 18. Final Recommendation

Key Design Principle:

Do not optimize for the smallest possible codebase.
Optimize for the clearest possible codebase that can support serious RAG functionality.

Prefer:
- explicit over implicit
- layered over tangled
- documented abstractions over clever abstractions
- boring interfaces over magic
- modular engines over one giant framework
- capability with clarity