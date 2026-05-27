import type { RetrieveAsset, RetrieveResponse } from "@/lib/api/retrieve";
import type { ContextPanelItem } from "@/types/chat";

const FIGURE_ASSET_PATTERN = /(^|[_-])(figure|image|img|plot|chart|diagram|photo|screenshot)([_-]|$)/i;
const TABLE_ASSET_PATTERN = /(^|[_-])(table|spreadsheet|csv|matrix)([_-]|$)/i;

type AdaptedContext = {
  contextItems: ContextPanelItem[];
  retrievalSummary: string;
  assistantText: string;
};

export function adaptRetrieveResponse(response: RetrieveResponse): AdaptedContext {
  const evidenceItems = response.evidence.map<ContextPanelItem>((item, index) => ({
    id: item.evidence_id || `evidence-${index}`,
    kind: "text",
    title: item.document_title || item.section_title || item.source_path || `Evidence ${index + 1}`,
    content: item.text || "",
    page_start: item.page_start ?? null,
    page_end: item.page_end ?? null,
    section_path: item.section_title ?? null,
    file_path: item.source_path ?? null,
    chunk_id: item.chunk_id ?? null,
    source_type: item.source_engine ?? null,
    document_id: item.document_id,
    reference_id: item.reference_id ?? null,
    workspace_node_id: item.workspace_node_id ?? inferWorkspaceNodeId(item),
    score: item.score ?? null,
    handles: item.metadata ?? {},
  }));
  const assetItems = retrieveAssetsToContextItems(response.assets ?? []);
  const contextItems = [...evidenceItems, ...assetItems];

  const summary = `${response.evidence.length} evidence item${response.evidence.length === 1 ? "" : "s"} retrieved${response.assets.length ? ` and ${response.assets.length} assets` : ""}.`;
  const assistantText = response.evidence.slice(0, 4).map((item) => item.text.trim()).filter(Boolean).join("\n\n");

  return {
    contextItems,
    retrievalSummary: summary,
    assistantText: assistantText || "No grounded answer text was returned.",
  };
}

export function retrieveAssetsToContextItems(assets: RetrieveAsset[]): ContextPanelItem[] {
  const figures = assets.filter(isFigureAsset);
  const tables = assets.filter(isTableAsset);
  const primaryFigure = figures[0] ? [assetToContextPanelItem(figures[0], "figure")] : [];
  const tableCards = tables.map((asset) => assetToContextPanelItem(asset, "table"));

  return [...primaryFigure, ...tableCards];
}

function assetToContextPanelItem(asset: RetrieveAsset, kind: "figure" | "table"): ContextPanelItem {
  const page = asset.page_number ?? null;

  return {
    id: `asset-${asset.document_id}-${asset.asset_id}`,
    kind,
    title: buildAssetTitle(asset, kind),
    content: asset.caption ?? (kind === "figure" ? "Source figure from retrieved context." : "Source table from retrieved context."),
    page_start: page,
    page_end: page,
    section_path: null,
    file_path: null,
    chunk_id: null,
    source_type: null,
    document_id: asset.document_id,
    reference_id: null,
    workspace_node_id: `asset:${asset.document_id}:${asset.asset_id}`,
    score: null,
    asset_id: asset.asset_id,
    asset_type: asset.asset_type,
    caption: asset.caption ?? null,
    url: asset.url ?? null,
    thumbnail_url: asset.thumbnail_url ?? null,
    mime_type: null,
    handles: {
      asset,
    },
  };
}

function isFigureAsset(asset: RetrieveAsset): boolean {
  return FIGURE_ASSET_PATTERN.test(asset.asset_type ?? "") || /image/i.test(asset.thumbnail_url ?? "") || /image/i.test(asset.url ?? "");
}

function isTableAsset(asset: RetrieveAsset): boolean {
  return TABLE_ASSET_PATTERN.test(asset.asset_type ?? "");
}

function buildAssetTitle(asset: RetrieveAsset, kind: "figure" | "table") {
  const label = kind === "figure" ? "Figure" : "Table";
  const page = asset.page_number ? ` - Page ${asset.page_number}` : "";
  const caption = asset.caption?.trim();
  if (caption) {
    return `${label}${page}: ${caption.slice(0, 72)}${caption.length > 72 ? "..." : ""}`;
  }
  return `${label}${page}`;
}

function inferWorkspaceNodeId(item: RetrieveResponse["evidence"][number]) {
  if (item.workspace_node_id) return item.workspace_node_id;
  if (item.document_id && item.chunk_id) return `chunk:${item.document_id}:${item.chunk_id}`;
  if (item.document_id && item.page_start) return `page:${item.document_id}:${item.page_start}`;
  if (item.document_id) return `document:${item.document_id}`;
  return null;
}
