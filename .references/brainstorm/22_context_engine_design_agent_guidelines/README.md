# Context Engine UI Design Agent Guidelines Package

This package converts the supplied transcript into a repeatable coding-agent workflow for UI work using shadcn-style component research, staged implementation, and Playwright-based UX verification.

## What is inside

```txt
context_engine_design_agent_guidelines/
├── README.md
├── docs/
│   ├── design/
│   │   ├── DESIGN_AGENT_GUIDELINES.md
│   │   ├── FRONTEND_FOLDER_STRUCTURE.md
│   │   └── COMPONENT_SELECTION_RULES.md
│   ├── agent-workflows/
│   │   └── UI_AGENT_WORKFLOW.md
│   └── implementation/
│       └── CODING_AGENT_HANDOFF.md
├── agents/
│   ├── 01-requirements-analyzer.md
│   ├── 02-shadcn-component-researcher.md
│   ├── 03-implementation-builder.md
│   └── 04-playwright-ux-verifier.md
├── specs/
│   └── _template/
│       ├── requirements.md
│       ├── component-research.md
│       ├── implementation-plan.md
│       └── verification-report.md
├── mcp/
│   ├── components.example.json
│   └── mcp.example.json
└── .cursor/
    └── rules/
        └── ui-design-agent.mdc
```

## Intended use

Give this package to a coding agent before it changes the UI. The agent should first analyze requirements, then research shadcn blocks/components, then implement in a small feature slice, and finally run visual/UX verification. Do not let the implementation agent skip directly to code.

## Recommended workflow

1. Copy the relevant files into the repository root, or keep them as external handoff docs.
2. For each UI surface, create a new folder under `specs/<surface-name>/` from `specs/_template/`.
3. Run the agents in order:
   - `01-requirements-analyzer`
   - `02-shadcn-component-researcher`
   - `03-implementation-builder`
   - `04-playwright-ux-verifier`
4. The implementation agent must preserve existing user capabilities and API contracts unless the requirements file explicitly says otherwise.

