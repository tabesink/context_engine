# Requirements: <Surface Name>

## Surface

- Route(s): `<route>`
- Users: `<admin | authenticated user | anonymous>`
- Surface owner: `<settings | chat | graph | other>`

## Current Capabilities To Retain

- [ ] Capability 1
- [ ] Capability 2
- [ ] Capability 3

## User Roles And Permissions

| Role | Can view | Can edit | Can run actions | Notes |
|---|---:|---:|---:|---|
| Admin | Yes | Yes | Yes |  |
| User | Yes | No | Limited |  |

## Backend/API Dependencies

| Capability | Endpoint/hook/type | Notes |
|---|---|---|
|  |  |  |

## Required States

- [ ] Loading
- [ ] Empty
- [ ] Success
- [ ] Warning
- [ ] Error
- [ ] Disabled
- [ ] Permission denied

## Accessibility Requirements

- [ ] Keyboard-accessible controls.
- [ ] Visible focus states.
- [ ] Status is not communicated by color alone.
- [ ] Labels or accessible names for icon-only controls.

## Responsive Requirements

- [ ] Desktop layout.
- [ ] Tablet layout where applicable.
- [ ] Mobile layout where applicable.

## Acceptance Criteria

- [ ] The UI preserves existing capability.
- [ ] The primary action is visually obvious.
- [ ] Secondary/destructive actions are grouped and confirmed.
- [ ] Admin-only controls are not visible to non-admin users.
- [ ] Live API data is wired or mock data is isolated behind fixtures.
- [ ] The design follows `DESIGN.md` and the UI design-agent docs.

## Non-Goals

- Do not change backend contracts unless explicitly requested.
- Do not redesign unrelated routes.
- Do not introduce a second design system outside shadcn/ui.

## Risks / Open Questions

- 
