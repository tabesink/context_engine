# Retrieval Adapter Replacement Notes

Replace:

```text
client/src/lib/retrieve-response-adapter.ts
```

with:

```text
files/client/src/lib/retrieve-response-adapter.ts
```

## Why

The existing adapter converts evidence into text context items but does not surface `RetrieveResponse.assets` as table/figure cards in the Context Stream tab.

## Behavior after replacement

For each retrieval response:

1. Evidence remains text context.
2. First figure/image asset becomes one `ContextPanelItem` with `kind: "figure"`.
3. Every table asset becomes a `ContextPanelItem` with `kind: "table"`.
4. Context Stream can render all of these using the same `SidePanel` item renderer.

## UI choice

Only one primary figure is added to the context stream to avoid stacking many large image cards in a narrow right panel. Tables are compact and can be listed multiple times.
