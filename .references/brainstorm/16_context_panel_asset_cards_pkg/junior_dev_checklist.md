# Junior Developer Checklist

## Before coding

- [ ] Pull latest `main`.
- [ ] Confirm `SidePanel.tsx` has two tabs: `Context Stream` and `Source Navigator`.
- [ ] Confirm `WorkspaceSourceContext.assets` is returned from backend.
- [ ] Confirm `RetrieveResponse.assets` is returned from retrieval.

## Code changes

- [ ] Add `AssetCards.tsx`.
- [ ] Replace `retrieve-response-adapter.ts`.
- [ ] Add asset fields to `ContextPanelItem`.
- [ ] Wire `FigureCard` and `TableCard` into `SidePanel.tsx`.
- [ ] Keep existing text evidence cards working.
- [ ] Keep existing workspace tree click behavior working.

## Visual checks

- [ ] Cards use thin borders, no shadows.
- [ ] Cards are grayscale only.
- [ ] Figure card is larger than table cards.
- [ ] Only one figure card appears per panel context.
- [ ] Multiple table cards can appear.
- [ ] Captions do not overflow the panel.
- [ ] Long tables scroll inside the card.

## Functional checks

- [ ] Chat retrieval still works when no assets are returned.
- [ ] Context Stream displays asset cards when assets are returned.
- [ ] Source Navigator displays asset cards when clicked source has assets.
- [ ] Image preview loads through the authenticated fetch helper.
- [ ] If image preview fails, fallback state is clean and not alarming.
- [ ] `Open figure` and `Open table` links resolve to backend asset URLs.

## Do not do

- [ ] Do not call LightRAG directly from the client.
- [ ] Do not use bright accent colors for asset cards.
- [ ] Do not silently change retrieval filters when a source is clicked.
- [ ] Do not dump raw metadata as the primary UI.
