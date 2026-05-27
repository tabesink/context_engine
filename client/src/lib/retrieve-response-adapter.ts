import type { RetrieveResponse } from "@/lib/api/retrieve";
import type { ContextPanelItem } from "@/types/chat";

type AdaptedContext = {
  contextItems: ContextPanelItem[];
  retrievalSummary: string;
  assistantText: string;
};

export function adaptRetrieveResponse(response: RetrieveResponse): AdaptedContext {
  const contextItems = response.evidence.map<ContextPanelItem>((item, index) => ({
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
    score: item.score ?? null,
    handles: item.metadata ?? {},
  }));

  const summary = `${response.evidence.length} evidence item${response.evidence.length === 1 ? "" : "s"} retrieved${response.assets.length ? ` and ${response.assets.length} assets` : ""}.`;
  const assistantText = response.evidence.slice(0, 4).map((item) => item.text.trim()).filter(Boolean).join("\n\n");

  return {
    contextItems,
    retrievalSummary: summary,
    assistantText: assistantText || "No grounded answer text was returned.",
  };
}
