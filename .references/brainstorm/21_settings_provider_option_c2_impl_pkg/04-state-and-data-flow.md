# 04 — State and Data Flow

## Page state model

### Server state
Use the app's existing query layer (likely React Query or equivalent) for:
- provider status summary
- provider credential coverage / profile counts
- provider-specific profile list

### Client UI state
Minimal local state:
- `selectedProviderId`
- `credentialDraft`
- `showCredential`

## Suggested query model

### Query A — provider overview
Returns all providers with:
- id
- name
- status / health
- local flag
- requiresCredential
- profileCount
- missingKey

### Query B — selected provider detail
Returns for selected provider:
- provider identity info
- credential metadata
- help text
- linked profiles

### Mutation A — save provider credential
Input:
- provider id
- credential value

Effects on success:
- invalidate provider overview query
- invalidate selected provider detail query
- preserve selected provider
- clear input value if desired
- show success toast

### Mutation B — refresh provider status
Could be:
- a dedicated mutation endpoint, or
- invalidation / refetch only

## Loading states
### Initial page load
- show skeleton for provider list and detail pane

### Provider switch
- keep selected row state visible
- show lightweight skeleton or loading placeholder in right pane only

### Save credential
- disable save button
- show pending state on button
- preserve input until success/failure known

### Refresh status
- show spinner or rotating icon on refresh button
- no full page lock

## Error states
- provider overview load failure: inline alert with retry
- provider detail load failure: inline pane alert, provider list remains usable
- save failure: inline field error or toast + keep draft value
- refresh failure: toast + retain last known data

## Recommended defaults
- default selected provider = first provider in list, usually `openai`
- if provider detail unavailable for selected item, show graceful error state in detail pane
