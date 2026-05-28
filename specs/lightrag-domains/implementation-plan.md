# Implementation Plan: LightRAG Domains

## Goal

Restructure LightRAG Domains from master-detail list to card-board layout matching screenshot, with shadcn primitives and shell header actions.

## Files To Change

| File | Change |
|---|---|
| `client/src/components/settings/SettingsDialog.tsx` | Header actions slot for lightrag-domains |
| `client/src/components/settings/panels/KnowledgeGraphSettingsPanel.tsx` | Card-board orchestration, remove master-detail |
| `client/src/components/settings/lightrag-domains/DomainOverviewCards.tsx` | StatusChip for legend |
| `client/src/components/settings/lightrag-domains/DomainRuntimeStatusCard.tsx` | Inline fragment variant |

## New Files

| File | Purpose |
|---|---|
| `client/src/components/settings/settings-panel-actions.tsx` | Context bridge panel → shell header |
| `client/src/components/settings/lightrag-domains/DomainLifecycleCard.tsx` | Per-domain card |
| `client/src/components/settings/lightrag-domains/DomainEventsTable.tsx` | Compact events table |
| `client/src/components/settings/lightrag-domains/CreateDomainForm.tsx` | Extracted create form |
| `client/src/hooks/use-running-domains-processing-status.ts` | Multi-domain polling |
| `client/src/components/ui/radio-group.tsx` | shadcn primitive |
| `client/src/components/ui/collapsible.tsx` | shadcn primitive |

## Removed / Deprecated

| File | Reason |
|---|---|
| `DomainRegistryTable.tsx` | Replaced by DomainLifecycleCard |
| `DomainLifecycleWorkflowCard.tsx` | Inlined into DomainLifecycleCard |
| `DomainDangerZone.tsx` | Actions moved to More menu |
| `DomainEventTail.tsx` | Replaced by DomainEventsTable |

## API Wiring

| UI need | Hook/API function | Source endpoint |
|---|---|---|
| Domain list | `knowledgeGraphAdminApi.list()` | Admin KG API |
| Processing status | `useRunningDomainsProcessingStatus` | `fetchAdminDomainProcessingStatus` |
| Audit logs | `adminDocumentsApi.listAuditLogs()` | Admin documents API |

## State Handling

- Loading: PanelState while domains load
- Empty: PanelState "No domains yet"
- Success: notice banner
- Error: destructive text banner
- Disabled: busyAction locks per domain
- Permission denied: admin gate in panel

## Implementation Steps

- [x] Specs (requirements, research, plan)
- [x] Install radio-group, collapsible
- [x] Settings panel actions context + header wiring
- [x] DomainLifecycleCard + DomainEventsTable
- [x] CreateDomainForm with Card/RadioGroup/Collapsible
- [x] useRunningDomainsProcessingStatus hook
- [x] More menu consolidation
- [x] Verification report

## Test / Verification Plan

- [x] Admin can open LightRAG Domains
- [x] Header shows Refresh + Create
- [x] Create toggles form card
- [x] All domains show full card bodies
- [x] Actions and events work per card
