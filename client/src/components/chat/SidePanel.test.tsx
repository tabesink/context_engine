import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { SidePanel } from "@/components/chat/SidePanel";
import type { SourceNavigatorState } from "@/types/chat";

vi.mock("next/image", () => ({
  default: (props: Record<string, unknown>) => {
    const { alt = "", src = "" } = props;
    return <img alt={String(alt)} src={String(src)} />;
  },
}));

describe("SidePanel source navigator", () => {
  it("renders secondary source-context figures instead of dropping them", () => {
    const sourceNavigator: SourceNavigatorState = {
      loading: false,
      selectedNodeId: "chunk:doc-1:chunk-1",
      context: {
        node_id: "chunk:doc-1:chunk-1",
        kind: "chunk",
        title: "Pump overview",
        domain_id: "manuals",
        breadcrumb: [],
        document: {
          document_id: "doc-1",
          title: "Manual",
        },
        text: "Exact source text",
        assets: [
          {
            asset_id: "fig-1",
            document_id: "doc-1",
            asset_type: "figure",
            title: "Primary diagram",
            caption: "Primary diagram",
            url: "/documents/doc-1/assets/fig-1",
            thumbnail_url: "/documents/doc-1/assets/fig-1/thumbnail",
            mime_type: "image/png",
            metadata: {},
          },
          {
            asset_id: "fig-2",
            document_id: "doc-1",
            asset_type: "figure",
            title: "Secondary diagram",
            caption: "Secondary diagram",
            url: "/documents/doc-1/assets/fig-2",
            thumbnail_url: "/documents/doc-1/assets/fig-2/thumbnail",
            mime_type: "image/png",
            metadata: {},
          },
        ],
        metadata: {},
      },
    };

    const markup = renderToStaticMarkup(
      <SidePanel
        open
        onOpenChange={() => undefined}
        contextItems={[]}
        activeTab="source-navigator"
        onActiveTabChange={() => undefined}
        sourceNavigator={sourceNavigator}
        hasAssistantMessages={false}
      />,
    );

    expect(markup).toContain("Primary diagram");
    expect(markup).toContain("Secondary diagram");
  });
});
