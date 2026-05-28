# UI Agent MCP Setup

Use shadcn.io MCP as a block-discovery and implementation-assistance tool, not as an authority to overwrite Context Engine's design system.

The purpose of MCP use is to help Cursor retrieve current shadcn block metadata, examples, icons, and install commands so coding agents do not hallucinate props, paths, or component APIs.

## Recommended Cursor Setup

For individual local use, configure the MCP server globally in Cursor.

For team/project use, prefer a project-level `.cursor/mcp.json` committed with a token placeholder, not a real token.

Project-safe shape:

```json
{
  "mcpServers": {
    "shadcnio": {
      "url": "https://www.shadcn.io/api/mcp?token=${SHADCNIO_TOKEN}"
    }
  }
}
```

Each developer should provide `SHADCNIO_TOKEN` through their shell or a git-ignored local environment file. Do not commit a real shadcn.io token. Treat the full MCP URL like an API key.

## Cursor Usage Rules

When asking Cursor to use shadcn.io, name the MCP server explicitly:

```text
use shadcnio to search for compact dashboard/job queue/status workflow blocks that could fit this Context Engine admin surface
```

Preferred workflow:

1. Search for candidate blocks.
2. Inspect the block metadata and component structure.
3. Select the best-fit block and import it wholesale by default.
4. Wire data and auth constraints with minimal visual changes.
5. Run lint/build before committing when code changed.

## Approved MCP-Assisted Tasks

Use shadcn.io MCP for:

- Finding dashboard, monitoring, workflow, job queue, table, danger-zone, timeline, skeleton, and empty-state patterns.
- Checking exact block names/slugs before installation.
- Retrieving install commands.
- Inspecting component structure before adapting it.
- Finding icons or small UI primitives that match an existing surface.
- Comparing multiple candidate blocks for the same admin workflow.

Do not use shadcn.io MCP for:

- Deciding backend architecture.
- Changing API contracts.
- Introducing new state management patterns.
- Replacing existing Context Engine routing/state boundaries.
- Bypassing `DESIGN.md`.
- Exposing LightRAG directly to the frontend.
- Creating a second component system outside shadcn/ui.

## Context Engine Block Adaptation Checklist

Before committing any MCP-sourced block, verify:

- The block remains visually close to the original shadcn design unless a product constraint requires adaptation.
- The block does not expose backend-only actions to regular users.
- The block does not duplicate an existing card/table/status component.
- The block does not create another polling loop.
- The block does not merge retrieval evidence state with processing-status state.
- The block does not make frontend calls to LightRAG.
- The block follows the simplified lifecycle action model: Start, Stop, Repair, Archive, Preview purge, and Purge permanently.
- Advanced actions such as recreate/regenerate remain hidden, internal, or clearly marked as advanced/debug-only.

## Good Cursor Prompts

```text
use shadcnio to find three compact status workflow blocks. Do not install yet. Compare their structure for a LightRAG domain lifecycle card with Start, Stop, Repair, Archive, Preview purge, and Purge permanently actions.
```

```text
use shadcnio to inspect a dashboard job queue block. Adapt only the table and status chip structure for Context Engine jobs. Keep existing API client and store boundaries. Do not add a new polling loop.
```

```text
use shadcnio to find a danger-zone block. Adapt it for Archive, Preview purge, and Purge permanently. Use existing shadcn tokens and require explicit confirmation for purge.
```

Avoid prompts like:

```text
wire this block directly to LightRAG APIs
```

## Dependency And File Hygiene

If a block installation adds files under `client/src/components/ui/`, review every generated file before committing.

Keep app-specific composites near the feature surface first, for example:

```txt
client/src/components/settings/lightrag-domains/DomainLifecycleCard.tsx
client/src/components/settings/lightrag-domains/DomainProcessingStatusCard.tsx
client/src/components/settings/lightrag-domains/DomainDangerZone.tsx
```

Only promote a component to a shared location after at least two real Context Engine surfaces use it.

## Token And Security Rules

- Do not commit a real shadcn.io MCP token.
- Do not paste a real MCP URL with token into documentation, issues, screenshots, or prompts.
- Prefer `${SHADCNIO_TOKEN}` placeholders in project config.
- Keep `.env` files and local token files ignored by git.
- If a token is accidentally committed, rotate/revoke it immediately.

## Final Rule

MCP should speed up accurate shadcn block discovery. It should not weaken Context Engine's architecture boundaries, auth model, polling model, or frontend/backend contracts.
