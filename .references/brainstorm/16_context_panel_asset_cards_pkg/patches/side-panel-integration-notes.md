# SidePanel Integration Notes

Target file:

```text
client/src/components/chat/SidePanel.tsx
```

Add this import near the other local imports:

```ts
import {
  FigureCard,
  TableCard,
  assetCardFromContextItem,
  assetCardFromWorkspaceAsset,
  splitAssetCards,
} from "@/components/chat/AssetCards";
```

## Replace placeholder source asset rendering

Replace the current `SourceAssetCard` implementation with:

```tsx
function SourceAssetCard({ asset }: { asset: WorkspaceContextAsset }) {
  const card = assetCardFromWorkspaceAsset(asset);
  if (card.kind === "figure") {
    return <FigureCard asset={card} density="spacious" />;
  }
  return <TableCard asset={card} density="compact" />;
}
```

## Replace table/figure context item renderers

Replace the current `TableContextItem` implementation with:

```tsx
function TableContextItem({
  item,
  onOpenSourceFromContext,
}: {
  item: ContextPanelItem;
  onOpenSourceFromContext?: (item: ContextPanelItem) => void;
}) {
  return (
    <TableCard
      asset={assetCardFromContextItem(item)}
      density="compact"
      action={
        onOpenSourceFromContext ? (
          <OpenSourceAction item={item} onOpenSourceFromContext={onOpenSourceFromContext} />
        ) : null
      }
    />
  );
}
```

Replace the current `FigureContextItem` implementation with:

```tsx
function FigureContextItem({
  item,
  onOpenSourceFromContext,
}: {
  item: ContextPanelItem;
  onOpenSourceFromContext?: (item: ContextPanelItem) => void;
}) {
  return (
    <FigureCard
      asset={assetCardFromContextItem(item)}
      density="spacious"
      action={
        onOpenSourceFromContext ? (
          <OpenSourceAction item={item} onOpenSourceFromContext={onOpenSourceFromContext} />
        ) : null
      }
    />
  );
}
```

## Improve Source Navigator asset section

Inside the Source Navigator tab, after source text/details and before raw/debug metadata, group assets like this:

```tsx
const assetCards = (context.assets ?? []).map(assetCardFromWorkspaceAsset);
const { primaryFigure, tables, others } = splitAssetCards(assetCards);
```

Then render:

```tsx
{primaryFigure ? (
  <div className="space-y-2">
    <h4 className="text-[10px] font-medium uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
      Figure
    </h4>
    <FigureCard asset={primaryFigure} density="spacious" />
  </div>
) : null}

{tables.length > 0 ? (
  <div className="space-y-2">
    <h4 className="text-[10px] font-medium uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
      Tables
    </h4>
    <div className="space-y-2">
      {tables.map((asset) => (
        <TableCard key={asset.id} asset={asset} density="compact" />
      ))}
    </div>
  </div>
) : null}

{!primaryFigure && tables.length === 0 && others.length > 0 ? (
  <div className="space-y-2">
    <h4 className="text-[10px] font-medium uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
      Assets
    </h4>
    <div className="space-y-2">
      {others.map((asset) => (
        <TableCard key={asset.id} asset={asset} density="compact" />
      ))}
    </div>
  </div>
) : null}
```

## Expected result

- Context Stream: text evidence cards + one figure card + table cards.
- Source Navigator: exact clicked source context + one figure card + table cards.
- Visual language remains aligned with `DESIGN.md`: no color fill, no shadows, thin borders, pill metadata, compact grayscale cards.
