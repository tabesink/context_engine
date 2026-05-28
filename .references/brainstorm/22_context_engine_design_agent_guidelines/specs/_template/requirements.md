# Requirements: <Surface Name>

## Surface

- Route(s): `<route>`
- Users: `<admin | authenticated user | anonymous>`
- Feature owner: `<feature>`

## Current capabilities to retain

- [ ] Capability 1
- [ ] Capability 2
- [ ] Capability 3

## User roles and permissions

| Role | Can view | Can edit | Can run actions | Notes |
|---|---:|---:|---:|---|
| Admin | Yes | Yes | Yes |  |
| User | Yes | No | Limited |  |

## Backend/API dependencies

| Capability | Endpoint/hook/type | Notes |
|---|---|---|
|  |  |  |

## Required states

- [ ] Loading
- [ ] Empty
- [ ] Success
- [ ] Warning
- [ ] Error
- [ ] Disabled
- [ ] Permission denied

## Acceptance criteria

- [ ] The UI preserves existing capability.
- [ ] The primary action is visually obvious.
- [ ] Secondary/destructive actions are grouped and confirmed.
- [ ] Admin-only controls are not visible to non-admin users.
- [ ] Live API data is wired or mock data is isolated behind fixtures.

## Non-goals

- Do not change backend contracts unless explicitly requested.
- Do not redesign unrelated routes.

## Risks / open questions

- 
