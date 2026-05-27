"use client";

import { useState, type PointerEvent, type ReactNode } from "react";
import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type {
  ContextPanelItem,
  PipelineProgressEvent,
  SidePanelTab,
  SourceNavigatorState,
  WorkspaceContextAsset,
} from "@/types/chat";

const SIDE_PANEL_MIN_WIDTH = 400;
const SIDE_PANEL_MAX_WIDTH = 720;

type SidePanelProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  contextItems: ContextPanelItem[];
  activeTab: SidePanelTab;
  onActiveTabChange: (tab: SidePanelTab) => void;
  sourceNavigator: SourceNavigatorState;
  retrievalSummary?: string;
  progressItems?: PipelineProgressEvent[];
  lastError?: string;
  hasAssistantMessages: boolean;
  selectedAssistantMessageId?: string;
  loadingSelection?: boolean;
  onOpenSourceFromContext?: (nodeId: string) => void;
};

export function SidePanel({
  open,
  onOpenChange,
  contextItems,
  activeTab,
  onActiveTabChange,
  sourceNavigator,
  retrievalSummary,
  progressItems = [],
  lastError,
  hasAssistantMessages,
  selectedAssistantMessageId,
  loadingSelection,
  onOpenSourceFromContext,
}: SidePanelProps) {
  const [panelWidth, setPanelWidth] = useState(SIDE_PANEL_MIN_WIDTH);

  function startPanelResize(event: PointerEvent<HTMLDivElement>) {
    event.preventDefault();

    const startX = event.clientX;
    const startWidth = panelWidth;
    const previousCursor = document.body.style.cursor;
    const previousUserSelect = document.body.style.userSelect;

    function handlePointerMove(moveEvent: globalThis.PointerEvent) {
      const nextWidth = startWidth + startX - moveEvent.clientX;

      setPanelWidth(Math.min(SIDE_PANEL_MAX_WIDTH, Math.max(SIDE_PANEL_MIN_WIDTH, nextWidth)));
    }

    function stopPanelResize() {
      document.body.style.cursor = previousCursor;
      document.body.style.userSelect = previousUserSelect;
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", stopPanelResize);
    }

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", stopPanelResize);
  }

  const content = (
    <PanelContent
      contextItems={contextItems}
      activeTab={activeTab}
      onActiveTabChange={onActiveTabChange}
      sourceNavigator={sourceNavigator}
      retrievalSummary={retrievalSummary}
      progressItems={progressItems}
      lastError={lastError}
      hasAssistantMessages={hasAssistantMessages}
      selectedAssistantMessageId={selectedAssistantMessageId}
      loadingSelection={loadingSelection}
      onOpenSourceFromContext={onOpenSourceFromContext}
      onClose={() => onOpenChange(false)}
    />
  );

  return (
    <>
      <aside
        className="relative hidden shrink-0 border-l border-[var(--border)] bg-[var(--background)] lg:flex"
        style={{ width: panelWidth }}
      >
        <div
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize context panel"
          onPointerDown={startPanelResize}
          className="absolute inset-y-0 left-0 z-10 w-2 -translate-x-1 cursor-col-resize touch-none"
        />
        {content}
      </aside>
      <div
        className={cn(
          "fixed inset-0 z-50 bg-black/20 transition-opacity lg:hidden",
          open ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={() => onOpenChange(false)}
        aria-hidden={!open}
      >
        <div
          className={cn(
            "ml-auto flex h-full w-[min(100vw,400px)] transform border-l border-[var(--border)] bg-[var(--background)] transition-transform",
            open ? "translate-x-0" : "translate-x-full",
          )}
          onClick={(event) => event.stopPropagation()}
        >
          {content}
        </div>
      </div>
    </>
  );
}

function PanelContent({
  contextItems,
  activeTab,
  onActiveTabChange,
  sourceNavigator,
  retrievalSummary,
  progressItems,
  lastError,
  hasAssistantMessages,
  selectedAssistantMessageId,
  loadingSelection,
  onOpenSourceFromContext,
  onClose,
}: {
  contextItems: ContextPanelItem[];
  activeTab: SidePanelTab;
  onActiveTabChange: (tab: SidePanelTab) => void;
  sourceNavigator: SourceNavigatorState;
  retrievalSummary?: string;
  progressItems: PipelineProgressEvent[];
  lastError?: string;
  hasAssistantMessages: boolean;
  selectedAssistantMessageId?: string;
  loadingSelection?: boolean;
  onOpenSourceFromContext?: (nodeId: string) => void;
  onClose: () => void;
}) {
  return (
    <div className="flex h-full min-h-0 w-full flex-col">
      <div className="px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium tracking-tight text-[var(--foreground)]">Context</p>
            <p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">
              Retrieved evidence and exact source inspection.
            </p>
          </div>
          <Button
            type="button"
            variant="outline"
            size="icon-sm"
            onClick={onClose}
            className="rounded-full border-[var(--border)] text-[var(--muted-foreground)] shadow-none transition-none lg:hidden"
            aria-label="Close side panel"
          >
            <X className="size-4" aria-hidden />
          </Button>
        </div>
        <div
          role="tablist"
          aria-label="Context panel tabs"
          className="mt-4 grid grid-cols-2 gap-1 rounded-full border border-[var(--border)] p-1"
        >
          <TabButton
            tab="context-stream"
            activeTab={activeTab}
            onActiveTabChange={onActiveTabChange}
          >
            Context Stream
          </TabButton>
          <TabButton
            tab="source-navigator"
            activeTab={activeTab}
            onActiveTabChange={onActiveTabChange}
          >
            Source Navigator
          </TabButton>
        </div>
      </div>
      <div className="min-h-0 min-w-0 flex-1 overflow-y-auto px-4 pb-4">
        <Separator />
        {activeTab === "context-stream" ? (
          <ContextStreamTab
            contextItems={contextItems}
            retrievalSummary={retrievalSummary}
            progressItems={progressItems}
            lastError={lastError}
            hasAssistantMessages={hasAssistantMessages}
            selectedAssistantMessageId={selectedAssistantMessageId}
            loadingSelection={loadingSelection}
            onOpenSourceFromContext={onOpenSourceFromContext}
          />
        ) : (
          <SourceNavigatorTab sourceNavigator={sourceNavigator} />
        )}
      </div>
    </div>
  );
}

function TabButton({
  tab,
  activeTab,
  onActiveTabChange,
  children,
}: {
  tab: SidePanelTab;
  activeTab: SidePanelTab;
  onActiveTabChange: (tab: SidePanelTab) => void;
  children: ReactNode;
}) {
  const active = tab === activeTab;
  return (
    <Button
      type="button"
      role="tab"
      aria-selected={active}
      variant={active ? "secondary" : "ghost"}
      size="xs"
      onClick={() => onActiveTabChange(tab)}
      className={cn(
        "h-7 rounded-full px-3 text-xs font-medium shadow-none transition-none",
        active ? "bg-[var(--muted)] text-[var(--foreground)]" : "text-[var(--muted-foreground)]",
      )}
    >
      {children}
    </Button>
  );
}

function ContextStreamTab({
  contextItems,
  retrievalSummary,
  progressItems,
  lastError,
  hasAssistantMessages,
  selectedAssistantMessageId,
  loadingSelection,
  onOpenSourceFromContext,
}: {
  contextItems: ContextPanelItem[];
  retrievalSummary?: string;
  progressItems: PipelineProgressEvent[];
  lastError?: string;
  hasAssistantMessages: boolean;
  selectedAssistantMessageId?: string;
  loadingSelection?: boolean;
  onOpenSourceFromContext?: (nodeId: string) => void;
}) {
  const summary = loadingSelection
    ? "Retrieving context for this response..."
    : retrievalSummary || "No retrieved context yet.";

  return (
    <>
      <section className="py-5">
        <p className="text-xs leading-5 text-[var(--muted-foreground)]">{summary}</p>
        {lastError ? <p className="mt-2 text-xs leading-5 text-[var(--destructive)]">{lastError}</p> : null}
      </section>
      {progressItems.length ? (
        <section className="space-y-3 pb-5">
          <p className="text-xs font-medium tracking-tight text-[var(--foreground)]">Pipeline</p>
          <div className="space-y-3">
            {progressItems.map((item, index) => (
              <PipelineProgressItem key={`${item.step}-${item.status}-${index}`} item={item} />
            ))}
          </div>
        </section>
      ) : null}
      <section className="space-y-5">
        {contextItems.length ? (
          contextItems.map((item) => (
            <ContextItem
              key={item.id}
              item={item}
              onOpenSourceFromContext={onOpenSourceFromContext}
            />
          ))
        ) : null}
        {!contextItems.length && loadingSelection ? (
          <p className="text-xs leading-5 text-[var(--muted-foreground)]">Waiting for retrieval results...</p>
        ) : null}
        {!contextItems.length && !loadingSelection && !hasAssistantMessages ? (
          <p className="text-xs leading-5 text-[var(--muted-foreground)]">
            Ask a question or select an assistant response to inspect retrieved evidence.
          </p>
        ) : null}
        {!contextItems.length && !loadingSelection && hasAssistantMessages && !selectedAssistantMessageId ? (
          <p className="text-xs leading-5 text-[var(--muted-foreground)]">
            Select an assistant response in the timeline to inspect its retrieved context.
          </p>
        ) : null}
        {!contextItems.length && !loadingSelection && selectedAssistantMessageId ? (
          <p className="text-xs leading-5 text-[var(--muted-foreground)]">
            No retrieved context is available for this response.
          </p>
        ) : null}
      </section>
    </>
  );
}

function SourceNavigatorTab({ sourceNavigator }: { sourceNavigator: SourceNavigatorState }) {
  if (sourceNavigator.loading) {
    return (
      <SourceStateBlock
        title="Loading source context"
        description="Loading source context..."
      />
    );
  }
  if (sourceNavigator.error) {
    return (
      <SourceStateBlock
        title="Source context is unavailable"
        description={sourceNavigator.error}
        tone="error"
      />
    );
  }
  if (!sourceNavigator.context) {
    return (
      <SourceStateBlock
        title="No source selected"
        description="Select a document, section, page, chunk, or asset from the workspace tree."
      />
    );
  }

  const context = sourceNavigator.context;
  const badges = [
    context.kind,
    context.page_number ? `Page ${context.page_number}` : null,
    context.page_start && !context.page_number
      ? context.page_end && context.page_end !== context.page_start
        ? `Pages ${context.page_start}-${context.page_end}`
        : `Page ${context.page_start}`
      : null,
    context.chunk_id ? `Chunk ${context.chunk_id}` : null,
    context.asset_id ? `Asset ${context.asset_id}` : null,
  ].filter(Boolean);

  return (
    <div className="space-y-4 py-5">
      {context.breadcrumb.length ? (
        <nav className="flex flex-wrap items-center gap-1.5 text-xs leading-5 text-[var(--muted-foreground)]" aria-label="Source breadcrumb">
          {context.breadcrumb.map((item, index) => (
            <span key={`${item.id ?? item.title}-${index}`} className="inline-flex items-center gap-1.5">
              {index ? <span aria-hidden>/</span> : null}
              <span className="truncate">{item.title}</span>
            </span>
          ))}
        </nav>
      ) : null}

      <section className="space-y-2">
        <div className="flex flex-wrap gap-1.5">
          {badges.map((badge) => (
            <Badge
              key={badge}
              variant="muted"
              className="rounded-full border-transparent px-2 py-0.5 text-[11px] font-normal"
            >
              {badge}
            </Badge>
          ))}
        </div>
        <div>
          <h3 className="text-sm font-medium tracking-tight text-[var(--foreground)]">{context.title}</h3>
          {context.document ? (
            <p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">{context.document.title}</p>
          ) : null}
        </div>
      </section>

      {context.summary ? (
        <p className="text-xs leading-5 text-[var(--muted-foreground)]">{context.summary}</p>
      ) : null}

      <Card className="gap-0 rounded-xl border-[var(--border)] bg-[var(--background)] py-0 shadow-none">
        <CardContent className="px-3 py-3">
          {context.text ? (
            <p className="whitespace-pre-wrap text-xs leading-5 text-[var(--foreground)]">{context.text}</p>
          ) : (
            <p className="text-xs leading-5 text-[var(--muted-foreground)]">
              No source text is available for this selection.
            </p>
          )}
        </CardContent>
      </Card>

      {context.assets.length ? (
        <section className="space-y-2">
          <p className="text-xs font-medium tracking-tight text-[var(--foreground)]">Assets</p>
          <div className="space-y-2">
            {context.assets.map((asset) => (
              <SourceAssetCard key={asset.asset_id} asset={asset} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function SourceStateBlock({
  title,
  description,
  tone,
}: {
  title: string;
  description: string;
  tone?: "error";
}) {
  return (
    <section className="py-5">
      <p className="text-xs font-medium tracking-tight text-[var(--foreground)]">{title}</p>
      <p className={cn("mt-1 text-xs leading-5 text-[var(--muted-foreground)]", tone === "error" && "text-[var(--destructive)]")}>
        {description}
      </p>
    </section>
  );
}

function SourceAssetCard({ asset }: { asset: WorkspaceContextAsset }) {
  return (
    <Card className="gap-0 rounded-xl border-[var(--border)] bg-[var(--background)] py-0 shadow-none">
      <CardContent className="px-3 py-2">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-[var(--foreground)]">{asset.title}</p>
            <p className="mt-1 text-xs leading-5 text-[var(--muted-foreground)]">
              {asset.asset_type}
              {asset.page_number ? ` - Page ${asset.page_number}` : ""}
            </p>
          </div>
          {asset.url ? (
            <Badge variant="outline" className="rounded-full text-[11px] font-normal">
              source
            </Badge>
          ) : null}
        </div>
        {asset.caption ? (
          <p className="mt-2 whitespace-pre-wrap text-xs leading-5 text-[var(--muted-foreground)]">{asset.caption}</p>
        ) : null}
      </CardContent>
    </Card>
  );
}

function PipelineProgressItem({ item }: { item: PipelineProgressEvent }) {
  const isFailed = item.status === "failed";
  const isWarning = item.status === "warning";
  const statusLabel = item.status === "complete" ? "Done" : item.status[0].toUpperCase() + item.status.slice(1);

  return (
    <article className="text-xs leading-5">
      <div className="flex items-center gap-2 text-[var(--muted-foreground)]">
        <span className="text-[var(--foreground)]">{progressStepLabel(item.step)}</span>
        <span
          className={cn(
            isFailed && "text-[var(--destructive)]",
            isWarning && "text-[var(--foreground)]",
          )}
        >
          {statusLabel}
        </span>
      </div>
      <p className={cn("mt-1 whitespace-pre-wrap", isFailed ? "text-[var(--destructive)]" : "text-[var(--muted-foreground)]")}>
        {item.message}
      </p>
    </article>
  );
}

function progressStepLabel(step: PipelineProgressEvent["step"]) {
  const labels: Record<PipelineProgressEvent["step"], string> = {
    prepare: "Prepare",
    plan: "Plan",
    retrieve: "Retrieve",
    index: "Index",
    context: "Context",
    synthesize: "Synthesize",
    stream: "Generate",
    finalize: "Finalize",
  };
  return labels[step];
}

function Separator() {
  return <div className="border-t border-[var(--border)]" />;
}

function ContextItem({
  item,
  onOpenSourceFromContext,
}: {
  item: ContextPanelItem;
  onOpenSourceFromContext?: (nodeId: string) => void;
}) {
  if (item.kind === "table") {
    return <TableContextItem item={item} onOpenSourceFromContext={onOpenSourceFromContext} />;
  }
  if (item.kind === "figure") {
    return <FigureContextItem item={item} onOpenSourceFromContext={onOpenSourceFromContext} />;
  }
  return <TextContextItem item={item} onOpenSourceFromContext={onOpenSourceFromContext} />;
}

function TextContextItem({
  item,
  onOpenSourceFromContext,
}: {
  item: ContextPanelItem;
  onOpenSourceFromContext?: (nodeId: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <article className="text-xs leading-5">
      <button
        type="button"
        onClick={() => setExpanded((current) => !current)}
        className="block w-full text-left text-[var(--foreground)] hover:text-[var(--foreground)]"
        aria-expanded={expanded}
      >
        {item.title}
      </button>
      <p className={cn("mt-1 whitespace-pre-wrap text-[var(--muted-foreground)]", expanded ? "line-clamp-none" : "line-clamp-3")}>
        {item.content || "No text content was returned for this chunk."}
      </p>
      <OpenSourceAction item={item} onOpenSourceFromContext={onOpenSourceFromContext} />
    </article>
  );
}

function TableContextItem({
  item,
  onOpenSourceFromContext,
}: {
  item: ContextPanelItem;
  onOpenSourceFromContext?: (nodeId: string) => void;
}) {
  return (
    <article className="text-xs leading-5">
      <div className="rounded-xl border border-[var(--border)]">
        <div className="border-b border-[var(--border)] px-3 py-2 text-xs text-[var(--foreground)]">{item.title}</div>
        <div className="max-h-64 overflow-auto p-3">
          <pre className="min-w-full w-max whitespace-pre font-mono text-xs leading-5 text-[var(--muted-foreground)]">
            {item.content || "Table content will appear here when returned by retrieval."}
          </pre>
        </div>
      </div>
      <OpenSourceAction item={item} onOpenSourceFromContext={onOpenSourceFromContext} />
    </article>
  );
}

function FigureContextItem({
  item,
  onOpenSourceFromContext,
}: {
  item: ContextPanelItem;
  onOpenSourceFromContext?: (nodeId: string) => void;
}) {
  return (
    <article className="text-xs leading-5">
      <div className="overflow-hidden rounded-xl border border-[var(--border)]">
        <div className="border-b border-[var(--border)] px-3 py-2 text-xs text-[var(--foreground)]">{item.title}</div>
        <div className="p-3 text-xs leading-5 text-[var(--muted-foreground)]">
          <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-[var(--border)] bg-[var(--muted)]">
            figure artifact placeholder
          </div>
          <p className="mt-2 whitespace-pre-wrap">{item.content || "Backend image/artifact loading will be wired later."}</p>
        </div>
      </div>
      <OpenSourceAction item={item} onOpenSourceFromContext={onOpenSourceFromContext} />
    </article>
  );
}

function OpenSourceAction({
  item,
  onOpenSourceFromContext,
}: {
  item: ContextPanelItem;
  onOpenSourceFromContext?: (nodeId: string) => void;
}) {
  if (!item.workspace_node_id || !onOpenSourceFromContext) return null;
  return (
    <Button
      type="button"
      variant="ghost"
      size="xs"
      onClick={() => onOpenSourceFromContext(item.workspace_node_id!)}
      className="mt-2 h-6 rounded-full px-2 text-xs text-[var(--muted-foreground)] shadow-none transition-none"
    >
      Open source
    </Button>
  );
}
