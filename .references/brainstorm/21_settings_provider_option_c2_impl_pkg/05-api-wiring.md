# 05 — API Wiring

## Goal
Integrate the new UI with the backend in a **lean, low-entropy** way.

## Principle
Do **not** let the page talk directly to fetch everywhere. Use the app's existing API abstraction / service layer and existing auth-aware client.

## Recommended wiring layers
1. **API client layer**
2. **Query hooks layer**
3. **View-model mapping layer**
4. **UI components**

## Suggested frontend service contracts
These names are illustrative. Map them to the real codebase.

```ts
getProviderOverview(): Promise<ProviderOverviewResponse>
getProviderDetail(providerId: ProviderId): Promise<ProviderDetailResponse>
saveProviderCredential(input: SaveProviderCredentialRequest): Promise<void>
refreshProviderStatus(): Promise<void | ProviderOverviewResponse>
```

## Suggested response shapes
```ts
type ProviderId = 'openai' | 'bedrock' | 'ollama'

interface ProviderOverviewItem {
  id: ProviderId
  name: string
  profileCount: number
  status: 'healthy' | 'missing_key' | 'local' | 'disabled' | 'no_profiles' | 'unknown'
  requiresCredential: boolean
}

interface ProviderOverviewResponse {
  items: ProviderOverviewItem[]
  lastUpdated: string
}

interface ProviderProfileItem {
  id: string
  name: string
  enabled: boolean
}

interface ProviderDetailResponse {
  id: ProviderId
  name: string
  profileCount: number
  requiresCredential: boolean
  credentialLabel: string
  credentialPlaceholder: string
  helperText: string
  profiles: ProviderProfileItem[]
}

interface SaveProviderCredentialRequest {
  providerId: ProviderId
  credential: string
}
```

## Mapping guidance
Normalize raw backend data into a UI view model before it touches presentational components.

Example:
```ts
function mapProviderStatusToBadge(status: ProviderOverviewItem['status']) {
  switch (status) {
    case 'local':
      return { label: 'Local', tone: 'muted' }
    case 'missing_key':
      return { label: 'Missing key', tone: 'warning' }
    case 'healthy':
      return { label: 'Healthy', tone: 'success' }
    case 'no_profiles':
      return { label: 'No profiles', tone: 'subtle' }
    default:
      return undefined
  }
}
```

## Security notes
- Never attempt to read back stored credentials into the browser.
- UI should only submit new credential values.
- On success, show confirmation, do not display the saved secret.
