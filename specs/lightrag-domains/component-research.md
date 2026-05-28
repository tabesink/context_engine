# Component Research: LightRAG Domains

## Requirements Source

- `specs/lightrag-domains/requirements.md`

## Design Sources

- `DESIGN.md`
- `docs/design/ui-design-agent-guidelines.md`
- `docs/design/component-selection-rules.md`
- Attached screenshot (card-board layout reference)

## Candidate Components / Blocks

| Candidate | Source | Fits because | Supports capability | Install command |
|---|---|---|---|---|
| Card | shadcn/ui (installed) | Domain cards and create form containers | Card board layout | — |
| Table | shadcn/ui (installed) | Recent events column with right-aligned timestamps | Event tail | — |
| Radio Group | shadcn/ui | Host port mode selection | Create form | `npx shadcn@latest add radio-group` |
| Collapsible | shadcn/ui | Advanced retrieval defaults disclosure | Create form | `npx shadcn@latest add collapsible` |
| Button | shadcn/ui (installed) | Refresh, Create, quick actions | All actions | — |
| Dropdown Menu | shadcn/ui (installed) | More menu (repair, danger zone) | Secondary actions | — |
| Select | shadcn/ui (installed) | Embedding model, retrieval profile | Create form | — |
| Badge / StatusChip | local surfaces | Status legend and runtime labels | Status display | — |
| SectionCard | local surfaces | Board wrapper | Overview header | — |

## Existing Local Components To Reuse

| Component | Path | Reuse plan |
|---|---|---|
| SectionCard | `client/src/components/surfaces/SectionCard.tsx` | Domain board wrapper |
| StatusChip | `client/src/components/surfaces/StatusChip.tsx` | Overview legend counts |
| PanelState | `client/src/components/surfaces/PanelState.tsx` | Loading/empty states |
| settings-controls | `client/src/components/settings/settings-controls.ts` | Button/input styling |

## Recommended Composition

```txt
SettingsDialog header
├── Breadcrumb
└── Refresh + Create (via settings-panel-actions context)

KnowledgeGraphSettingsPanel
├── CreateDomainForm (Card, toggled)
│   ├── CardHeader / CardContent / CardFooter
│   ├── RadioGroup (host port)
│   └── Collapsible (advanced retrieval)
└── DomainBoard (SectionCard)
    ├── DomainOverviewCards
    └── DomainLifecycleCard[]
        ├── Card header (status dot, name, metadata)
        └── Two-column body
            ├── Runtime status + quick actions + More menu
            └── DomainEventsTable
```

## Accessibility Notes

- RadioGroup provides proper radiogroup semantics vs native inputs
- Collapsible uses button trigger for advanced section
- Table headers for events column (optional, compact mode may omit for density)
- More menu has aria-label

## Responsive Notes

- Card body uses `md:grid-cols-2`; stacks on narrow viewports
- Quick actions wrap with flex-wrap

## Rejected Alternatives

| Alternative | Reason rejected |
|---|---|
| Master-detail list + detail stack | User chose card board parity with screenshot |
| Accordion per domain | User chose all cards always expanded |
| Inline danger zone section | User chose More dropdown |
| Sheet/dialog for create form | User chose inline toggle card |

## Final Recommendation

Use installed Card + Table + DropdownMenu for the board; install RadioGroup and Collapsible for create form polish. Lift header actions via lightweight React context.
