import { describe, expect, it } from "vitest";

import type { RetrieveResponse } from "@/lib/api/retrieve";
import { adaptRetrieveResponse, retrieveAssetsToContextItems } from "@/lib/retrieve-response-adapter";

function baseResponse(overrides: Partial<RetrieveResponse> = {}): RetrieveResponse {
  return {
    query: "show evidence",
    mode: "hybrid",
    evidence: [
      {
        evidence_id: "ev-1",
        document_id: "doc-1",
        source_engine: "chunks",
        text: "Evidence text",
        document_title: "Document One",
        source_path: "/docs/one.md",
        page_start: 4,
        page_end: 5,
        chunk_id: "chunk-1",
        reference_id: "ref-1",
        workspace_node_id: "chunk:doc-1:chunk-1",
        metadata: { rank: 1 },
      },
    ],
    assets: [],
    ...overrides,
  };
}

describe("adaptRetrieveResponse", () => {
  it("preserves evidence-only responses without asset context items", () => {
    const adapted = adaptRetrieveResponse(baseResponse());

    expect(adapted.contextItems).toHaveLength(1);
    expect(adapted.contextItems[0]).toMatchObject({
      id: "ev-1",
      kind: "text",
      title: "Document One",
      content: "Evidence text",
      workspace_node_id: "chunk:doc-1:chunk-1",
    });
    expect(adapted.retrievalSummary).toBe("1 evidence item retrieved.");
  });

  it("appends one primary figure and every table asset to context items", () => {
    const adapted = adaptRetrieveResponse(
      baseResponse({
        assets: [
          {
            asset_id: "fig-1",
            document_id: "doc-1",
            asset_type: "figure",
            caption: "Primary architecture figure",
            page_number: 6,
            url: "/assets/fig-1",
            thumbnail_url: "/assets/fig-1/thumb",
          },
          {
            asset_id: "fig-2",
            document_id: "doc-1",
            asset_type: "image",
            caption: "Secondary figure",
            page_number: 7,
            url: "/assets/fig-2",
          },
          {
            asset_id: "table-1",
            document_id: "doc-1",
            asset_type: "table",
            caption: "| Col A | Col B |\n| --- | --- |\n| 1 | 2 |",
            page_number: 8,
            url: "/assets/table-1",
          },
          {
            asset_id: "table-2",
            document_id: "doc-1",
            asset_type: "csv_table",
            page_number: 9,
            url: "/assets/table-2",
          },
        ],
      }),
    );

    expect(adapted.contextItems.map((item) => item.kind)).toEqual(["text", "figure", "table", "table"]);
    expect(adapted.contextItems[1]).toMatchObject({
      id: "asset-doc-1-fig-1",
      kind: "figure",
      asset_id: "fig-1",
      asset_type: "figure",
      caption: "Primary architecture figure",
      url: "/assets/fig-1",
      thumbnail_url: "/assets/fig-1/thumb",
      workspace_node_id: "asset:doc-1:fig-1",
      page_start: 6,
      page_end: 6,
    });
    expect(adapted.contextItems.slice(2).map((item) => item.asset_id)).toEqual(["table-1", "table-2"]);
    expect(adapted.retrievalSummary).toBe("1 evidence item retrieved and 4 assets.");
  });
});

describe("retrieveAssetsToContextItems", () => {
  it("returns no cards for unclassified assets", () => {
    expect(
      retrieveAssetsToContextItems([
        {
          asset_id: "file-1",
          document_id: "doc-1",
          asset_type: "attachment",
          page_number: 1,
          url: "/assets/file-1",
        },
      ]),
    ).toEqual([]);
  });
});
