# 03 — Component Architecture

## Recommended component tree

```text
SettingsProviderRoute
├─ SettingsPageShell                (existing)
│  ├─ SettingsSidebar               (existing)
│  └─ ProviderPageContent
│     ├─ ProviderPageHeader
│     ├─ ProviderPageGrid
│     │  ├─ ProviderListPane
│     │  │  ├─ ProviderListHeader
│     │  │  ├─ ProviderRowList
│     │  │  │  ├─ ProviderRow
│     │  │  │  ├─ ProviderRow
│     │  │  │  └─ ProviderRow
│     │  │  └─ ProviderHealthSummary
│     │  └─ ProviderDetailPane
│     │     ├─ ProviderIdentityHeader
│     │     ├─ ProviderCredentialSection
│     │     └─ ProviderProfilesSection
│     └─ PageFeedbackLayer
```

## Component responsibilities

### `SettingsProviderRoute`
- route-level container
- authorization check if needed
- composes data hooks + page

### `ProviderPageContent`
- orchestrates page-level loading / error / empty states
- manages selected provider state

### `ProviderPageHeader`
Props:
- `onRefresh()`
- `isRefreshing`

### `ProviderListPane`
Props:
- `providers`
- `selectedProviderId`
- `onSelectProvider(id)`
- `healthSummary`
- `lastUpdated`

### `ProviderRow`
Props:
- `provider`
- `selected`
- `onClick`

Suggested provider shape:
```ts
interface ProviderListItemVM {
  id: 'openai' | 'bedrock' | 'ollama'
  name: string
  profileCount: number
  local?: boolean
  statusLabel?: string
  iconKey: string
}
```

### `ProviderHealthSummary`
Props:
- `items`
- `lastUpdated`

### `ProviderDetailPane`
Props:
- `provider`
- `credentialState`
- `profiles`
- `onSaveCredential`
- `isSaving`

### `ProviderCredentialSection`
Props:
- `provider`
- `credentialLabel`
- `placeholder`
- `helpText`
- `requiresCredential`
- `onSave(value)`
- `isSaving`

### `ProviderProfilesSection`
Props:
- `profiles`
- `onManageProfiles?`

## Implementation advice
- Keep view-model mapping close to route-level hooks.
- Avoid over-generalizing provider-specific differences.
- Prefer small presentational components with simple props.
