import { describe, expect, it } from "vitest";

import {
  assetCardFromContextItem,
  assetCardFromWorkspaceAsset,
  classifyAsset,
  parseMarkdownTable,
  splitAssetCards,
  type AssetCardModel,
} from "@/components/chat/AssetCards";
import type { ContextPanelItem, WorkspaceContextAsset } from "@/types/chat";

describe("AssetCards utilities", () => {
  it("classifies figures and tables from asset type and mime type", () => {
    expect(classifyAsset("source_figure", null)).toBe("figure");
    expect(classifyAsset("attachment", "image/png")).toBe("figure");
    expect(classifyAsset("csv_table", null)).toBe("table");
    expect(classifyAsset("attachment", null)).toBe("asset");
  });

  it("splits cards into one primary figure, tables, secondary figures, and others", () => {
    const cards: AssetCardModel[] = [
      { id: "fig-1", kind: "figure", title: "Figure 1" },
      { id: "table-1", kind: "table", title: "Table 1" },
      { id: "fig-2", kind: "figure", title: "Figure 2" },
      { id: "asset-1", kind: "asset", title: "Attachment" },
    ];

    const split = splitAssetCards(cards);

    expect(split.primaryFigure?.id).toBe("fig-1");
    expect(split.secondaryFigures.map((asset) => asset.id)).toEqual(["fig-2"]);
    expect(split.tables.map((asset) => asset.id)).toEqual(["table-1"]);
    expect(split.others.map((asset) => asset.id)).toEqual(["asset-1"]);
  });

  it("maps workspace assets into card models with source navigation metadata", () => {
    const asset: WorkspaceContextAsset = {
      asset_id: "fig-1",
      document_id: "doc-1",
      asset_type: "figure",
      title: "Architecture",
      caption: "System overview",
      page_number: 12,
      section_id: "section-1",
      url: "/assets/fig-1",
      thumbnail_url: "/assets/fig-1/thumb",
      mime_type: "image/png",
      metadata: { source: "workspace" },
    };

    expect(assetCardFromWorkspaceAsset(asset)).toMatchObject({
      id: "fig-1",
      kind: "figure",
      title: "Architecture",
      caption: "System overview",
      documentId: "doc-1",
      assetId: "fig-1",
      pageNumber: 12,
      workspaceNodeId: "asset:doc-1:fig-1",
    });
  });

  it("maps context items using top-level asset fields before handles fallback", () => {
    const item: ContextPanelItem = {
      id: "asset-doc-1-table-1",
      kind: "table",
      title: "Table - Page 3",
      content: "top-level content",
      document_id: "doc-1",
      workspace_node_id: "asset:doc-1:table-1",
      asset_id: "table-1",
      asset_type: "table",
      caption: "Top-level caption",
      url: "/assets/table-1",
      handles: {
        asset: {
          asset_id: "fallback",
          document_id: "doc-1",
          asset_type: "figure",
          caption: "Fallback caption",
          metadata: {},
        },
      },
    };

    expect(assetCardFromContextItem(item)).toMatchObject({
      id: "table-1",
      kind: "table",
      assetId: "table-1",
      assetType: "table",
      caption: "Top-level caption",
      url: "/assets/table-1",
    });
  });

  it("parses markdown tables and ignores plain text", () => {
    expect(parseMarkdownTable("| A | B |\n| --- | --- |\n| 1 | 2 |")).toEqual([
      ["A", "B"],
      ["1", "2"],
    ]);
    expect(parseMarkdownTable("not a table")).toEqual([]);
  });
});
