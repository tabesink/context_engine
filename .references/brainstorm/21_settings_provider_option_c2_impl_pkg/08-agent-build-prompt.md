# 08 — Coding Agent Build Prompt

Use this prompt with a coding agent:

---
Implement the **Settings → Provider** route in the Context Engine frontend using the **Option C2 — Borderless Rows** layout.

## Design intent
Recreate a flatter, more borderless provider-management page with:
- existing Settings shell/sidebar preserved
- left provider list / summary column
- right selected-provider detail pane
- low-noise, soft-separator visual style
- minimal card nesting
- selected row shown with soft accent background and narrow left accent bar

## Required functionality
Retain all existing capabilities:
- show provider status for OpenAI, AWS Bedrock, Ollama
- show profile counts
- allow Refresh status
- allow secure credential entry and save for providers that require keys
- do not display stored secrets
- show linked model profiles
- preserve admin-only behavior if present

## Build constraints
- Reuse existing shared UI primitives where possible
- Keep backend integration lean via existing API/service/query layers
- Avoid over-abstraction
- Keep components small and composable
- Prefer view-model mapping at the route / hook layer

## Deliverables
1. New Provider page UI implementation
2. Necessary supporting hooks / mappers / service updates
3. Loading / error / empty states
4. Responsive behavior
5. Short implementation summary and file map

## Suggested file structure
- `.../routes/settings/provider/*`
- `ProviderPage.tsx`
- `ProviderPageHeader.tsx`
- `ProviderListPane.tsx`
- `ProviderRow.tsx`
- `ProviderHealthSummary.tsx`
- `ProviderDetailPane.tsx`
- `ProviderCredentialSection.tsx`
- `ProviderProfilesSection.tsx`
- `useProviderOverview.ts`
- `useProviderDetail.ts`
- `providerViewModel.ts`

## Acceptance criteria
- Page matches Option C2 intent
- Existing provider capabilities preserved
- Clean, flat, borderless row presentation achieved
- Code is junior-friendly and low-entropy
---
