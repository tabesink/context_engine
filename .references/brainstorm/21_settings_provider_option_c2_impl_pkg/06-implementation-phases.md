# 06 — Implementation Phases

## Phase 1 — Audit and scaffolding
**Owner:** Coding agent / senior reviewer

Tasks:
1. Locate the current `Settings / Provider` route.
2. Identify existing hooks/services for:
   - provider status
   - credential save
   - profile counts
3. Identify current settings shell/sidebar components.
4. Identify shared button, input, badge, and separator primitives.
5. Confirm admin-only access behavior.

Deliverable:
- short code map / implementation notes

## Phase 2 — Layout build
**Owner:** Junior dev with coding agent support

Tasks:
1. Build `ProviderPageHeader`.
2. Build the 2-column desktop layout.
3. Build `ProviderListPane` with flat rows.
4. Build `ProviderHealthSummary`.
5. Build `ProviderDetailPane` shell.

Deliverable:
- static UI with mock data matching Option C2

## Phase 3 — Data integration
Tasks:
1. Wire provider overview query.
2. Wire selected provider detail query.
3. Map API responses to view models.
4. Ensure selected provider switches detail pane.

Deliverable:
- live read-only page with real provider data

## Phase 4 — Mutations and interactions
Tasks:
1. Wire `Refresh status` action.
2. Wire `Save key` mutation.
3. Add loading states.
4. Add success/error feedback.

Deliverable:
- fully interactive provider page

## Phase 5 — Polish and QA
Tasks:
1. Match spacing and typography to Option C2.
2. Remove excess visual noise.
3. Test keyboard navigation and focus states.
4. Test error states.
5. Test responsive behavior.

Deliverable:
- merge-ready implementation
