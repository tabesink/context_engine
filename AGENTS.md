# Agent Guidance

- Do not edit files under `docs/brainstorm/` unless the user explicitly asks for brainstorm documentation changes.
- Treat `docs/brainstorm/` as historical planning material; keep implementation, tests, live docs, and root guidance elsewhere.
- CLI is no longer supported or tracked. Do not modify CLI-related code, documentation, or tests unless the user explicitly asks for a CLI exception.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **context_engine** (12844 symbols, 24223 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/context_engine/context` | Codebase overview, check index freshness |
| `gitnexus://repo/context_engine/clusters` | All functional areas |
| `gitnexus://repo/context_engine/processes` | All execution flows |
| `gitnexus://repo/context_engine/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.cursor/skills/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.cursor/skills/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.cursor/skills/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.cursor/skills/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.cursor/skills/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.cursor/skills/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
