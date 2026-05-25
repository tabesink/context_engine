Here is a cleaner, stronger version of the prompt:

````markdown
# Task: Review and Update Documentation After Recent Context Engine Changes

You are a senior software architect and technical documentation reviewer.

## Context

The `context-engine` codebase has recently evolved after the original documentation was written.

New documentation has been added in:

- `@docs/lightrag_docs`
- `@docs/cli_docs`

These documents were added **after** the original `context-engine` codebase and documentation were developed.

There is also a brainstorm folder:

- `@docs/brainstorm`

Important: `@docs/brainstorm` is **not authoritative documentation**. It is only a collection of brainstormed architecture ideas, possible plans, and rough design thinking. Use it only as supporting context to understand intended direction, possible tensions, and design alternatives.

The remaining documentation in the `docs` folder may now be outdated or inconsistent with the current implementation.

---

## Objective

Review the current `context-engine` codebase and the full documentation set, then identify and update any documentation that no longer reflects the current codebase architecture, CLI behavior, LightRAG integration direction, API design, or deployment model.

The main goal is to discover and resolve **documentation/codebase tension**.

---

## What to Review

Review:

1. The current `context-engine` codebase
2. `@docs/lightrag_docs`
3. `@docs/cli_docs`
4. `@docs/brainstorm`
5. All other documentation under `@docs`

---

## Key Questions to Answer

While reviewing, identify:

1. Which documents are outdated?
2. Which documents contradict the current codebase?
3. Which documents contradict the newer LightRAG or CLI documentation?
4. Which brainstorm ideas were never implemented and should remain clearly marked as non-authoritative?
5. Which documentation still describes old architecture assumptions?
6. Which docs need to be rewritten, archived, merged, or deleted?
7. Are there missing docs needed for junior developers or coding agents to understand the current system?
8. Are the CLI docs aligned with the current API-layer-first architecture?
9. Are the LightRAG docs aligned with the intended architecture where:
   - LightRAG is the semantic/vector/graph retrieval engine
   - `context-engine` is the orchestration/application layer
   - the integration should remain modular and low-entropy
   - CLI commands should mirror API routes rather than bypass the API layer

---

## Expected Output

Produce a documentation review report with the following sections:

### 1. Documentation Inventory

Create a table of all reviewed docs with:

- File path
- Current purpose
- Status: current / outdated / partially outdated / brainstorm-only / duplicate / unclear
- Recommended action

### 2. Codebase Reality Check

Summarize what the current codebase actually does today, including:

- API structure
- CLI structure
- LightRAG-related code or integration points
- Deployment assumptions
- Auth/admin boundaries
- Any retrieval, ingestion, or graph visualization capabilities currently present

### 3. Documentation Tensions

List all discovered tensions between documentation and code.

For each tension, include:

- Document path
- Conflicting claim
- Actual codebase behavior
- Severity: high / medium / low
- Recommended fix

### 4. Brainstorm Triage

Review `@docs/brainstorm` and classify ideas into:

- Already implemented
- Still useful future direction
- Conflicts with current architecture
- Should be archived
- Should be converted into formal documentation

Make sure brainstorm content does not get treated as current system truth unless verified in code.

### 5. Recommended Documentation Structure

Propose a clean documentation structure for the repo going forward.

The structure should be simple enough for junior developers and coding agents to follow.

Include recommended files such as:

- `README.md`
- `docs/architecture.md`
- `docs/api.md`
- `docs/cli.md`
- `docs/lightrag-integration.md`
- `docs/deployment.md`
- `docs/admin-ingestion.md`
- `docs/graph-visualization.md`
- `docs/decisions/ADR-*.md`
- `docs/archive/`

### 6. Update Plan

Create a phased documentation update plan:

#### Phase 1 — Identify and mark stale docs
- Add warnings to outdated docs
- Move brainstorm-only or obsolete docs into archive if needed

#### Phase 2 — Update core docs
- Update architecture docs
- Update CLI docs
- Update LightRAG integration docs
- Update API route documentation

#### Phase 3 — Add missing developer guidance
- Add junior-dev-friendly architecture map
- Add coding-agent onboarding notes
- Add examples of API-first CLI commands
- Add deployment and admin-ingestion flows

#### Phase 4 — Final consistency pass
- Ensure all docs agree with the current codebase
- Ensure future plans are clearly separated from implemented behavior
- Ensure terminology is consistent

### 7. Concrete File-Level Changes

Recommend exact edits using this format:

```markdown
## File: docs/example.md

### Current issue
Explain what is wrong.

### Recommended change
Explain what should be changed.

### Suggested replacement text
Provide replacement text where useful.
````

---

## Constraints

* Do not assume brainstorm documents are correct.
* Do not rewrite architecture based only on intentions; verify against the code.
* Preserve useful design thinking, but clearly separate:

  * implemented behavior
  * planned behavior
  * rejected ideas
  * unresolved questions
* Keep the documentation lean and practical.
* Prefer simple explanations over abstract architecture language.
* Write so that a junior developer or coding agent can understand the system quickly.
* Avoid adding unnecessary complexity or documentation sprawl.

---

## Final Deliverable

Produce:

1. A documentation/codebase tension report
2. A recommended documentation structure
3. A phased documentation cleanup plan
4. File-by-file recommended updates
5. Any critical architecture questions that must be answered before finalizing the docs

````

A shorter version you can pass directly to a coding agent:

```markdown
Review the current `context-engine` codebase and all docs under `@docs`.

Important context:

- `@docs/lightrag_docs` and `@docs/cli_docs` were added after the original `context-engine` documentation was written.
- `@docs/brainstorm` is only brainstormed architecture planning, not authoritative documentation.
- The remaining docs may now be outdated and need to be reviewed against the current codebase.

Your task is to discover documentation/codebase tension and propose updates.

Specifically:

1. Inventory all docs under `@docs`.
2. Compare each doc against the current codebase.
3. Identify outdated, conflicting, duplicated, or unclear documentation.
4. Treat `@docs/brainstorm` as non-authoritative planning material only.
5. Verify whether CLI docs reflect the API-first rule: CLI commands should mirror API routes and go through the API layer.
6. Verify whether LightRAG docs reflect the intended separation:
   - LightRAG = semantic/vector/graph retrieval engine
   - `context-engine` = orchestration/application layer
   - integration should remain modular, lightweight, and low-entropy.
7. Recommend which docs should be updated, merged, archived, deleted, or rewritten.
8. Propose a clean documentation structure suitable for junior developers and coding agents.

Deliver:

- Documentation inventory table
- Current codebase reality summary
- List of documentation tensions
- Brainstorm triage
- Recommended docs structure
- Phased update plan
- File-by-file recommended edits
- Open architecture questions
````
