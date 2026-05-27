"use client";

import Image from "next/image";
import { useCallback, useEffect, useMemo, useState } from "react";
import { PanelRightOpen } from "lucide-react";
import { fetchWorkspaceSourceContext } from "@/api/workspace-context";
import { fetchWorkspaceTree } from "@/api/workspace-tree";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { ConversationView } from "@/components/chat/ConversationView";
import { SidePanel } from "@/components/chat/SidePanel";
import { WorkspaceTree } from "@/components/chat/WorkspaceTree";
import { retrieveApi, toRetrievalMode } from "@/lib/api/retrieve";
import { adaptRetrieveResponse } from "@/lib/retrieve-response-adapter";
import { errorMessage } from "@/lib/utils";
import {
  createId,
  setChatSessionState,
  useChatSessionStore,
} from "@/stores/chat-session-store";
import {
  DEFAULT_LIGHTRAG_PORT,
  getSelectedLightRagDomainId,
  useLightRagDomainStore,
} from "@/stores/lightrag-domain-store";
import type {
  AssistantTurnContext,
  ActivityEntry,
  ChatMessage,
  PipelineProgressEvent,
  RetrievalSettings,
  SidePanelTab,
  SourceTreeItem,
} from "@/types/chat";

const DEFAULT_RETRIEVAL_SETTINGS: RetrievalSettings = {
  lightrag_port: DEFAULT_LIGHTRAG_PORT,
  mode: "mix",
  top_k: 10,
  chunk_top_k: 10,
  chunk_rerank_top_k: 10,
  max_token_for_text_unit: 4000,
  max_token_for_global_context: 4000,
  max_token_for_local_context: 4000,
};

type ConnectionStatus = "idle" | "connecting" | "streaming" | "error";

export function LightRagChatShell() {
  const messages = useChatSessionStore((session) => session.messages);
  const contextByAssistantId = useChatSessionStore((session) => session.contextByAssistantId);
  const progressByAssistantId = useChatSessionStore((session) => session.progressByAssistantId);
  const selectedAssistantMessageId = useChatSessionStore((session) => session.selectedAssistantMessageId);
  const sourceTree = useChatSessionStore((session) => session.sourceTree);
  const sidePanelTab = useChatSessionStore((session) => session.sidePanelTab);
  const sourceNavigator = useChatSessionStore((session) => session.sourceNavigator);
  const status = useChatSessionStore((session) => session.status);
  const lastError = useChatSessionStore((session) => session.lastError);
  const [retrievalSettings, setRetrievalSettings] = useState<RetrievalSettings>(DEFAULT_RETRIEVAL_SETTINGS);
  const [sidePanelOpen, setSidePanelOpen] = useState(false);
  const lightragDomains = useLightRagDomainStore((domainState) => domainState.domains);
  const selectedPort = useLightRagDomainStore((domainState) => domainState.selectedPort);
  const selectedDomain = useLightRagDomainStore((domainState) => domainState.selectedDomain);
  const domainStatus = useLightRagDomainStore((domainState) => domainState.status);
  const domainError = useLightRagDomainStore((domainState) => domainState.error);
  const loadDomains = useLightRagDomainStore((domainState) => domainState.loadDomains);
  const setSelectedPort = useLightRagDomainStore((domainState) => domainState.setSelectedPort);
  const setMessages = useCallback((update: StateUpdate<ChatMessage[]>) => {
    setChatSessionState((session) => ({ messages: resolveNext(session.messages, update) }));
  }, []);
  const setActivities = useCallback((update: StateUpdate<ActivityEntry[]>) => {
    setChatSessionState((session) => ({ activities: resolveNext(session.activities, update) }));
  }, []);
  const setProgressByAssistantId = useCallback((update: StateUpdate<Record<string, PipelineProgressEvent[]>>) => {
    setChatSessionState((session) => ({ progressByAssistantId: resolveNext(session.progressByAssistantId, update) }));
  }, []);
  const setContextByAssistantId = useCallback((update: StateUpdate<Record<string, AssistantTurnContext>>) => {
    setChatSessionState((session) => ({ contextByAssistantId: resolveNext(session.contextByAssistantId, update) }));
  }, []);
  const setSelectedAssistantMessageId = useCallback((update: StateUpdate<string | undefined>) => {
    setChatSessionState((session) => ({ selectedAssistantMessageId: resolveNext(session.selectedAssistantMessageId, update) }));
  }, []);
  const setStatus = useCallback((status: ConnectionStatus) => {
    setChatSessionState({ status });
  }, []);
  const setLastError = useCallback((lastError: string | undefined) => {
    setChatSessionState({ lastError });
  }, []);
  const setSidePanelTab = useCallback((sidePanelTab: SidePanelTab) => {
    setChatSessionState({ sidePanelTab });
  }, []);

  useEffect(() => {
    void loadDomains();
  }, [loadDomains]);

  const loadWorkspaceForDomain = useCallback(async (domainId: string) => {
    try {
      const tree = await fetchWorkspaceTree(domainId);
      setChatSessionState({ sourceTree: tree });
    } catch {
      // Keep chat interactive even if workspace-tree fetch fails.
    }
  }, []);

  useEffect(() => {
    const defaults = selectedDomain?.retrieval_defaults;
    if (!defaults) return;
    const task = window.setTimeout(() => {
      setRetrievalSettings((current) => ({
        ...current,
        top_k: defaults.top_k,
        chunk_top_k: defaults.chunk_top_k,
        chunk_rerank_top_k: defaults.chunk_rerank_top_k,
        max_token_for_text_unit: defaults.max_token_for_text_unit,
        max_token_for_global_context: defaults.max_token_for_global_context,
        max_token_for_local_context: defaults.max_token_for_local_context,
      }));
    }, 0);
    void loadWorkspaceForDomain(selectedDomain.domain_id);
    return () => window.clearTimeout(task);
  }, [loadWorkspaceForDomain, selectedDomain]);

  const effectiveRetrievalSettings: RetrievalSettings = useMemo(
    () => ({
      ...retrievalSettings,
      lightrag_port: selectedPort,
    }),
    [retrievalSettings, selectedPort],
  );
  const displayedLastError = lastError ?? (domainStatus === "error" ? domainError : undefined);

  const handleRetrievalSettingsChange = useCallback(
    (nextSettings: RetrievalSettings) => {
      setRetrievalSettings({ ...nextSettings, lightrag_port: selectedPort });
      if (nextSettings.lightrag_port !== undefined && nextSettings.lightrag_port !== selectedPort) {
        setSelectedPort(nextSettings.lightrag_port);
      }
    },
    [selectedPort, setSelectedPort],
  );

  const submit = useCallback(
    async (content: string) => {
      const settingsForTurn = effectiveRetrievalSettings;

      const userMessage: ChatMessage = {
        id: createId("user"),
        role: "user",
        content,
        createdAt: Date.now(),
      };
      const assistantId = createId("assistant");
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        createdAt: Date.now() + 1,
      };
      const activityId = createId("activity");
      const activity: ActivityEntry = {
        id: activityId,
        label: "Query started",
        detail: `Retrieving ${settingsForTurn.mode} context from domain ${getSelectedLightRagDomainId()}.`,
        createdAt: Date.now(),
        status: "pending",
      };

      setMessages((current) => [...current, userMessage, assistantMessage]);
      setActivities((current) => [activity, ...current].slice(0, 8));
      setProgressByAssistantId((current) => ({ ...current, [assistantId]: [] }));
      setLastError(undefined);
      setStatus("connecting");
      setSelectedAssistantMessageId(assistantId);
      setSidePanelTab("context-stream");
      const activeAssistantId = assistantId;

      try {
        const domainId = getSelectedLightRagDomainId();
        const response = await retrieveApi.retrieve({
          query: content,
          mode: toRetrievalMode(settingsForTurn.mode),
          lightrag_domain_id: domainId,
          top_k: settingsForTurn.top_k,
          include_assets: true,
        });
        const adapted = adaptRetrieveResponse(response);
        const workspaceTree = await fetchWorkspaceTree(domainId).catch(() => null);
        setMessages((current) =>
          current.map((message) =>
            message.id === activeAssistantId
              ? { ...message, content: adapted.assistantText }
              : message,
          ),
        );
        setContextByAssistantId((current) => ({
          ...current,
          [activeAssistantId]: {
            assistantMessageId: activeAssistantId,
            contextItems: adapted.contextItems,
            retrievalSummary: adapted.retrievalSummary,
            sourceTree: workspaceTree ?? sourceTree ?? { root_id: "root", items: {} },
          },
        }));
        if (workspaceTree) {
          setChatSessionState({ sourceTree: workspaceTree });
        }
        setProgressByAssistantId((current) => ({
          ...current,
          [activeAssistantId]: [],
        }));
        setStatus("streaming");

        setActivities((current) =>
          current.map((activity) =>
            activity.id === activityId
              ? { ...activity, label: "Query complete", detail: "Completed grounded response.", status: "complete" }
              : activity,
          ),
        );
        setStatus("idle");
      } catch (error) {
        const message = error instanceof Error ? error.message : "Knowledge Graph query failed.";
        setLastError(message);
        setStatus("error");
        setMessages((current) =>
          current.map((item) =>
            item.id === activeAssistantId
              ? {
                  ...item,
                  content: item.content || "The retrieval request failed before a response was returned.",
                  error: message,
                }
              : item,
          ),
        );
        setActivities((current) =>
          current.map((activity) =>
            activity.id === activityId
              ? { ...activity, label: "Query failed", detail: message, status: "error" }
              : activity,
          ),
        );
      }
    },
    [
      effectiveRetrievalSettings,
      setActivities,
      setContextByAssistantId,
      setLastError,
      setMessages,
      setProgressByAssistantId,
      setSelectedAssistantMessageId,
      setSidePanelTab,
      setStatus,
      sourceTree,
    ],
  );

  const loadSourceNavigator = useCallback(async (nodeId: string, selectedTreeLabel?: string) => {
    const domainId = getSelectedLightRagDomainId();
    setSidePanelOpen(true);
    setChatSessionState({
      sidePanelTab: "source-navigator",
      sourceNavigator: {
        selectedDomainId: domainId,
        selectedNodeId: nodeId,
        selectedTreeLabel,
        loading: true,
      },
    });

    try {
      const context = await fetchWorkspaceSourceContext(domainId, nodeId);
      setChatSessionState((current) => {
        if (current.sourceNavigator.selectedNodeId !== nodeId) return {};
        return {
          sourceNavigator: {
            ...current.sourceNavigator,
            context,
            loading: false,
            error: undefined,
          },
        };
      });
    } catch (error) {
      const message = errorMessage(error, "Could not load source context.");
      setChatSessionState((current) => {
        if (current.sourceNavigator.selectedNodeId !== nodeId) return {};
        return {
          sourceNavigator: {
            ...current.sourceNavigator,
            loading: false,
            error: message,
          },
        };
      });
    }
  }, []);

  const handleWorkspaceNodeSelect = useCallback(
    (nodeId: string, item: SourceTreeItem) => {
      void loadSourceNavigator(nodeId, item.name);
    },
    [loadSourceNavigator],
  );

  const handleOpenSourceFromContext = useCallback(
    (nodeId: string) => {
      void loadSourceNavigator(nodeId);
    },
    [loadSourceNavigator],
  );

  const handleAssistantSelect = useCallback(
    (messageId: string) => {
      setSelectedAssistantMessageId(messageId);
      setSidePanelTab("context-stream");
    },
    [setSelectedAssistantMessageId, setSidePanelTab],
  );

  const busy = status === "connecting" || status === "streaming";
  const selectedContext = selectedAssistantMessageId ? contextByAssistantId[selectedAssistantMessageId] : undefined;
  const selectedProgress = selectedAssistantMessageId ? progressByAssistantId[selectedAssistantMessageId] : undefined;
  const displayedSourceTree = sourceTree;
  const hasAssistantMessages = messages.some((message) => message.role === "assistant");
  const loadingSelection = Boolean(
    busy && selectedAssistantMessageId && hasAssistantMessages && !contextByAssistantId[selectedAssistantMessageId],
  );

  return (
    <div className="flex h-full min-h-0 bg-[var(--background)]">
      <aside className="min-h-0 w-[280px] shrink-0 overflow-y-auto bg-[var(--background)] px-4 py-3">
        <WorkspaceTree
          sourceTree={displayedSourceTree}
          selectedNodeId={sourceNavigator.selectedNodeId}
          onNodeSelect={handleWorkspaceNodeSelect}
        />
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="px-4 py-3">
          <div className="flex w-full justify-end">
            <div className="flex min-w-0 flex-wrap items-start justify-end gap-2">
              <button
                type="button"
                onClick={() => setSidePanelOpen(true)}
                className="inline-flex size-9 items-center justify-center rounded-lg text-[var(--muted-foreground)] transition-colors hover:bg-[var(--muted)] hover:text-[var(--foreground)] lg:hidden"
                aria-label="Open retrieved context"
              >
                <PanelRightOpen className="size-4" aria-hidden />
              </button>
            </div>
          </div>
        </header>

        <ConversationView
          messages={messages}
          busy={busy}
          selectedAssistantMessageId={selectedAssistantMessageId}
          onAssistantSelect={handleAssistantSelect}
          emptyState={
            <div className="mx-auto flex max-w-lg flex-col items-center gap-3 px-4 text-center">
              <Image src="/logo.svg" alt="Knowledge Graph" width={112} height={112} priority className="h-28 w-28 text-[var(--foreground)]" />
              <p className="text-2xl font-medium tracking-tight text-[var(--foreground)]">Ask your knowledge graph.</p>
              <p className="text-sm leading-6 text-[var(--muted-foreground)]">
                Use the retrieval settings button in the composer to choose a knowledge graph domain, then ask a plain-language question.
              </p>
              <button
                type="button"
                onClick={() => void submit("Summarize the indexed corpus and list the most important topics.")}
                disabled={busy}
                className="mt-1 rounded-full bg-[var(--muted)] px-4 py-2 text-sm text-[var(--foreground)] transition-colors hover:bg-[var(--secondary)] disabled:cursor-not-allowed disabled:opacity-50"
              >
                Summarize this knowledge graph
              </button>
            </div>
          }
        />

        <div className="px-4 pt-3 pb-8 sm:px-6">
          <div className="mx-auto flex w-full max-w-4xl flex-col gap-3">
            {displayedLastError ? (
              <div className="rounded-xl bg-[var(--muted)] px-3 py-2 text-sm text-[var(--foreground)]">
                {displayedLastError}
              </div>
            ) : null}
            <ChatComposer
              onSubmit={submit}
              disabled={busy}
              busy={busy}
              placeholder="Ask Knowledge Graph"
              retrievalSettings={effectiveRetrievalSettings}
              onRetrievalSettingsChange={handleRetrievalSettingsChange}
              lightragDomains={lightragDomains}
            />
          </div>
        </div>
      </div>
      <SidePanel
        open={sidePanelOpen}
        onOpenChange={setSidePanelOpen}
        activeTab={sidePanelTab}
        onActiveTabChange={setSidePanelTab}
        contextItems={selectedContext?.contextItems ?? []}
        sourceNavigator={sourceNavigator}
        retrievalSummary={selectedContext?.retrievalSummary}
        progressItems={selectedProgress ?? []}
        lastError={displayedLastError}
        hasAssistantMessages={hasAssistantMessages}
        selectedAssistantMessageId={selectedAssistantMessageId}
        loadingSelection={loadingSelection}
        onOpenSourceFromContext={handleOpenSourceFromContext}
      />
    </div>
  );
}

type StateUpdate<T> = T | ((current: T) => T);

function resolveNext<T>(current: T, update: StateUpdate<T>) {
  return typeof update === "function" ? (update as (current: T) => T)(current) : update;
}
