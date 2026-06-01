"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { ExternalLink, Image as ImageIcon, Table2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { fetchAuthenticatedAssetBlob, resolveAssetUrl } from "@/lib/api/assets";
import { cn } from "@/lib/utils";
import type { ContextPanelItem, WorkspaceContextAsset } from "@/types/chat";

export type AssetCardKind = "figure" | "table" | "asset";

export type AssetCardModel = {
  id: string;
  kind: AssetCardKind;
  title: string;
  content?: string | null;
  caption?: string | null;
  documentId?: string | null;
  assetId?: string | null;
  assetType?: string | null;
  pageNumber?: number | null;
  pageStart?: number | null;
  pageEnd?: number | null;
  sectionId?: string | null;
  url?: string | null;
  thumbnailUrl?: string | null;
  mimeType?: string | null;
  workspaceNodeId?: string | null;
  metadata?: Record<string, unknown> | null;
};

type AssetCardProps = {
  asset: AssetCardModel;
  className?: string;
  action?: ReactNode;
  density?: "compact" | "spacious";
};

export function assetCardFromWorkspaceAsset(asset: WorkspaceContextAsset): AssetCardModel {
  const kind = classifyAsset(asset.asset_type, asset.mime_type);
  return {
    id: asset.asset_id,
    kind,
    title: asset.title || defaultAssetTitle(kind, asset.asset_type),
    content: asset.caption ?? null,
    caption: asset.caption ?? null,
    documentId: asset.document_id,
    assetId: asset.asset_id,
    assetType: asset.asset_type,
    pageNumber: asset.page_number ?? null,
    sectionId: asset.section_id ?? null,
    url: asset.url ?? null,
    thumbnailUrl: asset.thumbnail_url ?? null,
    mimeType: asset.mime_type ?? null,
    workspaceNodeId: `asset:${asset.document_id}:${asset.asset_id}`,
    metadata: asset.metadata ?? null,
  };
}

export function assetCardFromContextItem(item: ContextPanelItem): AssetCardModel {
  const handles = item.handles as Record<string, unknown> | undefined;
  const rawAsset = handles?.asset as Partial<WorkspaceContextAsset> | undefined;
  const kind = item.kind === "figure" || item.kind === "table"
    ? item.kind
    : classifyAsset(item.asset_type ?? rawAsset?.asset_type ?? null, item.mime_type ?? rawAsset?.mime_type ?? null);

  return {
    id: item.asset_id ?? rawAsset?.asset_id ?? item.id,
    kind,
    title: item.title || defaultAssetTitle(kind, item.asset_type ?? rawAsset?.asset_type),
    content: item.content,
    caption: item.caption ?? rawAsset?.caption ?? null,
    documentId: item.document_id ?? rawAsset?.document_id ?? null,
    assetId: item.asset_id ?? rawAsset?.asset_id ?? null,
    assetType: item.asset_type ?? rawAsset?.asset_type ?? null,
    pageNumber: item.page_start ?? rawAsset?.page_number ?? null,
    pageStart: item.page_start,
    pageEnd: item.page_end,
    sectionId: rawAsset?.section_id ?? null,
    url: item.url ?? rawAsset?.url ?? null,
    thumbnailUrl: item.thumbnail_url ?? rawAsset?.thumbnail_url ?? null,
    mimeType: item.mime_type ?? rawAsset?.mime_type ?? null,
    workspaceNodeId: item.workspace_node_id,
    metadata: rawAsset?.metadata ?? null,
  };
}

export function splitAssetCards(cards: AssetCardModel[]) {
  const figures = cards.filter((asset) => asset.kind === "figure");
  const tables = cards.filter((asset) => asset.kind === "table");
  const others = cards.filter((asset) => asset.kind !== "figure" && asset.kind !== "table");

  return {
    primaryFigure: figures[0] ?? null,
    secondaryFigures: figures.slice(1),
    tables,
    others,
  };
}

export function FigureCard({ asset, className, action, density = "spacious" }: AssetCardProps) {
  const imageUrl = asset.thumbnailUrl || asset.url;

  return (
    <figure
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--card)] p-3 shadow-none",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
            <ImageIcon className="h-3 w-3" aria-hidden />
            Figure
          </div>
          <h4 className="mt-1 truncate text-sm font-medium text-[var(--foreground)]">{asset.title}</h4>
        </div>
        <AssetMetaBadges asset={asset} />
      </div>

      <div
        className={cn(
          "mt-3 overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--muted)]",
          density === "spacious" ? "min-h-[190px]" : "min-h-[128px]",
        )}
      >
        <AuthenticatedAssetImage
          src={imageUrl}
          alt={asset.caption || asset.title || "Source figure"}
          className={density === "spacious" ? "max-h-[320px]" : "max-h-[180px]"}
        />
      </div>

      {asset.caption || asset.content ? (
        <figcaption className="mt-3 text-xs leading-5 text-[var(--muted-foreground)]">
          {asset.caption || asset.content}
        </figcaption>
      ) : null}

      <AssetCardFooter asset={asset} action={action} openLabel="Open figure" />
    </figure>
  );
}

export function TableCard({ asset, className, action, density = "compact" }: AssetCardProps) {
  const preview = asset.content || asset.caption || "Table asset available from this source.";
  const rows = parseMarkdownTable(preview);

  return (
    <section
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--card)] p-3 shadow-none",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-[0.18em] text-[var(--muted-foreground)]">
            <Table2 className="h-3 w-3" aria-hidden />
            Table
          </div>
          <h4 className="mt-1 truncate text-sm font-medium text-[var(--foreground)]">{asset.title}</h4>
        </div>
        <AssetMetaBadges asset={asset} />
      </div>

      <div className="mt-3 overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--muted)]">
        {rows.length > 0 ? (
          <div className="max-h-56 overflow-auto">
            <table className="w-full border-collapse text-left text-xs">
              <tbody>
                {rows.slice(0, density === "compact" ? 6 : 12).map((row, rowIndex) => (
                  <tr key={`${asset.id}-row-${rowIndex}`} className="border-b border-[var(--border)] last:border-b-0">
                    {row.map((cell, cellIndex) => {
                      const Cell = rowIndex === 0 ? "th" : "td";
                      return (
                        <Cell
                          key={`${asset.id}-${rowIndex}-${cellIndex}`}
                          className={cn(
                            "px-3 py-2 align-top text-[var(--foreground)]",
                            rowIndex === 0 ? "bg-[var(--card)] font-medium" : "font-normal",
                          )}
                        >
                          {cell}
                        </Cell>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="max-h-40 overflow-auto whitespace-pre-wrap px-3 py-2 text-xs leading-5 text-[var(--foreground)]">
            {preview}
          </p>
        )}
      </div>

      {asset.caption && asset.caption !== preview ? (
        <p className="mt-3 text-xs leading-5 text-[var(--muted-foreground)]">{asset.caption}</p>
      ) : null}

      <AssetCardFooter asset={asset} action={action} openLabel="Open table" />
    </section>
  );
}

function AssetMetaBadges({ asset }: { asset: AssetCardModel }) {
  return (
    <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
      {asset.pageNumber ? (
        <Badge variant="secondary" className="rounded-full bg-[var(--muted)] px-2 py-0.5 text-[10px] font-normal text-[var(--muted-foreground)] shadow-none">
          Page {asset.pageNumber}
        </Badge>
      ) : null}
      {asset.assetType ? (
        <Badge variant="outline" className="rounded-full border-[var(--border)] px-2 py-0.5 text-[10px] font-normal text-[var(--muted-foreground)] shadow-none">
          {asset.assetType}
        </Badge>
      ) : null}
    </div>
  );
}

function AssetCardFooter({ asset, action, openLabel }: { asset: AssetCardModel; action?: ReactNode; openLabel: string }) {
  const href = resolveAssetUrl(asset.url);

  if (!href && !action) {
    return null;
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2 border-t border-[var(--border)] pt-3">
      {action}
      {href ? (
        <a
          href={href}
          target="_blank"
          rel="noreferrer"
          className="inline-flex h-8 items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--card)] px-3 text-xs font-medium text-[var(--foreground)] transition-colors hover:bg-[var(--muted)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
        >
          {openLabel}
          <ExternalLink className="h-3 w-3" aria-hidden />
        </a>
      ) : null}
    </div>
  );
}

function AuthenticatedAssetImage({ src, alt, className }: { src?: string | null; alt: string; className?: string }) {
  const resolvedSrc = useMemo(() => resolveAssetUrl(src), [src]);
  const [result, setResult] = useState<{ src: string; objectUrl: string | null; error: boolean } | null>(null);

  useEffect(() => {
    if (!resolvedSrc) {
      return;
    }

    const controller = new AbortController();
    let nextObjectUrl: string | null = null;

    async function loadImage() {
      try {
        const blob = await fetchAuthenticatedAssetBlob(resolvedSrc!, {
          signal: controller.signal,
        });
        nextObjectUrl = URL.createObjectURL(blob);
        setResult({ src: resolvedSrc!, objectUrl: nextObjectUrl, error: false });
      } catch {
        if (!controller.signal.aborted) {
          setResult({ src: resolvedSrc!, objectUrl: null, error: true });
        }
      }
    }

    void loadImage();

    return () => {
      controller.abort();
      if (nextObjectUrl) {
        URL.revokeObjectURL(nextObjectUrl);
      }
    };
  }, [resolvedSrc]);

  if (!resolvedSrc) {
    return <AssetImagePlaceholder label="No preview available" />;
  }

  if (!result || result.src !== resolvedSrc) {
    return <AssetImagePlaceholder label="Loading preview..." />;
  }

  if (result.error || !result.objectUrl) {
    return <AssetImagePlaceholder label="Preview unavailable" />;
  }

  // Blob URLs from authenticated asset fetches cannot use Next image optimization.
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={result.objectUrl} alt={alt} className={cn("mx-auto h-auto w-full object-contain", className)} />;
}

function AssetImagePlaceholder({ label }: { label: string }) {
  return (
    <div className="flex min-h-[160px] flex-col items-center justify-center gap-2 px-4 py-8 text-center text-xs text-[var(--muted-foreground)]">
      <ImageIcon className="h-5 w-5" aria-hidden />
      <span>{label}</span>
    </div>
  );
}

export function classifyAsset(assetType?: string | null, mimeType?: string | null): AssetCardKind {
  const normalizedType = String(assetType ?? "").toLowerCase();
  const normalizedMime = String(mimeType ?? "").toLowerCase();

  if (
    normalizedMime.startsWith("image/") ||
    /(^|[_-])(figure|image|img|plot|chart|diagram|photo|screenshot)([_-]|$)/.test(normalizedType)
  ) {
    return "figure";
  }

  if (/(^|[_-])(table|spreadsheet|csv|matrix)([_-]|$)/.test(normalizedType)) {
    return "table";
  }

  return "asset";
}

function defaultAssetTitle(kind: AssetCardKind, assetType?: string | null) {
  if (kind === "figure") return "Source figure";
  if (kind === "table") return "Source table";
  return assetType ? `Source ${assetType}` : "Source asset";
}

export function parseMarkdownTable(value?: string | null): string[][] {
  if (!value) return [];
  const lines = value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const tableLines = lines.filter((line) => line.includes("|"));
  if (tableLines.length < 2) return [];

  const rows = tableLines
    .filter((line) => !/^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?$/.test(line))
    .map((line) => line.replace(/^\|/, "").replace(/\|$/, ""))
    .map((line) => line.split("|").map((cell) => cell.trim()).filter(Boolean));

  if (rows.length < 2) return [];
  const width = Math.max(...rows.map((row) => row.length));
  if (width < 2) return [];

  return rows.map((row) => {
    const padded = [...row];
    while (padded.length < width) padded.push("");
    return padded;
  });
}
