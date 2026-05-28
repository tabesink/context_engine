# 01 — Product Scope

## Objective
Implement the **Provider** settings route using the **Option C2 — Borderless Rows** layout.

## Users
- **Admin**: can refresh status, inspect provider health, enter/update credentials, inspect profile usage.
- **Non-admin**: should not access this route if the current product already restricts it.

## Required capabilities to retain
1. Show providers: **OpenAI**, **AWS Bedrock**, **Ollama**.
2. Show provider state:
   - enabled / healthy / missing key / local / no profiles
   - profile count per provider
3. Allow **Refresh status**.
4. Allow credential entry and saving for providers that require keys.
5. Show secure-handling message: keys are encrypted server-side and not returned to browser.
6. Show selected provider detail pane.
7. Show model profiles using the provider credential.
8. Preserve settings route shell and navigation structure.

## Non-goals
- No redesign of the entire Settings module.
- No provider-creation flow.
- No advanced secrets-management UI beyond current needs.
- No backend contract expansion unless strictly necessary.

## Success criteria
- The page visually matches the Option C2 layout intent.
- Existing provider functionality remains intact.
- The page is easier to scan and flatter / less noisy than the current UI.
