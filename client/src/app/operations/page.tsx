"use client";

import * as React from "react";
import { RefreshCw, RotateCcw } from "lucide-react";
import { AppPageFrame } from "@/components/layout/AppPageFrame";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { operationsApi, type Operation, type OperationStatus } from "@/lib/api/operations";
import { APIError } from "@/lib/api/client";
import { selectIsAdmin, useAuthStore } from "@/stores/auth-store";

const statusFilters: Array<OperationStatus | "all"> = ["all", "queued", "running", "succeeded", "failed", "canceled"];
const resourceFilters = ["all", "document", "domain", "provider", "system"] as const;

type ResourceFilter = (typeof resourceFilters)[number];

const statusTone: Record<string, { label: string; dot: string; text: string }> = {
  queued: { label: "queued", dot: "bg-orange-500", text: "text-orange-700" },
  running: { label: "running", dot: "bg-blue-600", text: "text-blue-700" },
  succeeded: { label: "succeeded", dot: "bg-green-600", text: "text-green-700" },
  failed: { label: "failed", dot: "bg-red-600", text: "text-red-700" },
  canceled: { label: "canceled", dot: "bg-neutral-400", text: "text-neutral-700" },
};

const stageLabels: Record<string, string> = {
  register_upload: "Register upload",
  parse_local_structure: "Parse local structure",
  push_to_lightrag: "Push to LightRAG",
  poll_remote_indexing: "Poll remote indexing",
  complete: "Complete",
  failed: "Failed",
};

function getErrorMessage(error: unknown, fallback: string) {
  if (error instanceof APIError) {
    const detail = error.body && typeof error.body === "object" && "detail" in error.body ? error.body.detail : null;
    return typeof detail === "string" ? detail : error.message || fallback;
  }
  return error instanceof Error && error.message ? error.message : fallback;
}

function formatOperationType(type: string) {
  return type.replace(/_/g, " ");
}

function formatStage(stage: string | null | undefined) {
  if (!stage) return "Not started";
  return stageLabels[stage] ?? stage.replace(/_/g, " ");
}

function formatTimestamp(value: string | null | undefined) {
  if (!value) return "n/a";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function StatusBadge({ status }: { status: string }) {
  const tone = statusTone[status] ?? { label: status, dot: "bg-neutral-400", text: "text-neutral-700" };
  return (
    <Badge variant="outline" className={`rounded-md border-neutral-200 bg-white text-[11px] font-medium ${tone.text}`}>
      <span className={`mr-1.5 inline-block size-1.5 rounded-full ${tone.dot}`} aria-hidden />
      {tone.label}
    </Badge>
  );
}

function ProgressCell({ value }: { value: number | null | undefined }) {
  if (value === null || value === undefined) {
    return <span className="font-mono text-[11px] text-neutral-500">n/a</span>;
  }
  const bounded = Math.max(0, Math.min(100, value));
  return (
    <div className="min-w-28 space-y-1.5">
      <div className="h-1.5 rounded-md bg-neutral-100">
        <div className="h-1.5 rounded-md bg-blue-600" style={{ width: `${bounded}%` }} />
      </div>
      <p className="font-mono text-[11px] text-neutral-500">{bounded}%</p>
    </div>
  );
}

function canRetry(operation: Operation) {
  return operation.status === "failed" && operation.type === "document_ingest";
}

export default function OperationsPage() {
  const isAdmin = useAuthStore(selectIsAdmin);
  const [operations, setOperations] = React.useState<Operation[]>([]);
  const [statusFilter, setStatusFilter] = React.useState<OperationStatus | "all">("all");
  const [resourceFilter, setResourceFilter] = React.useState<ResourceFilter>("all");
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [retryingId, setRetryingId] = React.useState<string | null>(null);

  const loadOperations = React.useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError(null);
    try {
      const nextOperations = await operationsApi.list({
        limit: 100,
        status: statusFilter === "all" ? undefined : statusFilter,
        resourceType: resourceFilter === "all" ? undefined : resourceFilter,
      });
      setOperations(nextOperations);
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to load operations"));
    } finally {
      setLoading(false);
    }
  }, [isAdmin, resourceFilter, statusFilter]);

  React.useEffect(() => {
    const task = window.setTimeout(() => {
      void loadOperations();
    }, 0);
    return () => window.clearTimeout(task);
  }, [loadOperations]);

  const activeCount = React.useMemo(
    () => operations.filter((operation) => operation.status === "queued" || operation.status === "running").length,
    [operations],
  );

  const retryOperation = async (operationId: string) => {
    setRetryingId(operationId);
    setError(null);
    try {
      await operationsApi.retry(operationId);
      await loadOperations();
    } catch (nextError) {
      setError(getErrorMessage(nextError, "Failed to retry operation"));
    } finally {
      setRetryingId(null);
    }
  };

  return (
    <AppPageFrame contentClassName="overflow-y-auto">
      <main className="mx-auto flex min-h-full w-full max-w-7xl flex-col bg-white px-6 py-6 md:px-8">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-neutral-100 pb-5">
          <div>
            <p className="font-mono text-[11px] text-neutral-500">/operations</p>
            <h1 className="mt-1 text-xl font-semibold tracking-tight text-neutral-950">Operations</h1>
            <p className="mt-1 max-w-2xl text-sm text-neutral-600">
              Global async activity across document ingestion, domain lifecycle, and provider tasks.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="rounded-md border-neutral-200 bg-white text-[11px] text-neutral-700">
              <span className="mr-1.5 inline-block size-1.5 rounded-full bg-blue-600" aria-hidden />
              {activeCount} active
            </Badge>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => void loadOperations()}
              disabled={!isAdmin || loading}
              className="h-8 rounded-md border-neutral-200 bg-white px-3 text-sm shadow-none hover:bg-neutral-50"
            >
              <RefreshCw className={`size-3.5 ${loading ? "animate-spin" : ""}`} aria-hidden />
              Refresh
            </Button>
          </div>
        </header>

        {!isAdmin ? (
          <section className="mt-5 rounded-lg border border-neutral-200 bg-neutral-50 p-4">
            <p className="text-sm font-medium text-neutral-900">Admin access required</p>
            <p className="mt-1 text-sm text-neutral-600">Sign in as an admin to view global operation history.</p>
          </section>
        ) : (
          <>
            <section className="flex flex-wrap gap-3 border-b border-neutral-100 py-4">
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="mr-1 text-xs font-medium text-neutral-600">Status</span>
                {statusFilters.map((status) => (
                  <button
                    key={status}
                    type="button"
                    onClick={() => setStatusFilter(status)}
                    className={`h-7 rounded-md border px-2.5 text-xs transition-colors ${
                      statusFilter === status
                        ? "border-neutral-950 bg-neutral-950 text-white"
                        : "border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-50"
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="mr-1 text-xs font-medium text-neutral-600">Resource</span>
                {resourceFilters.map((resource) => (
                  <button
                    key={resource}
                    type="button"
                    onClick={() => setResourceFilter(resource)}
                    className={`h-7 rounded-md border px-2.5 text-xs transition-colors ${
                      resourceFilter === resource
                        ? "border-neutral-950 bg-neutral-950 text-white"
                        : "border-neutral-200 bg-white text-neutral-700 hover:bg-neutral-50"
                    }`}
                  >
                    {resource}
                  </button>
                ))}
              </div>
            </section>

            {error ? (
              <div className="mt-4 rounded-lg border border-red-200 bg-white p-3 text-sm text-red-700">{error}</div>
            ) : null}

            <section className="mt-4 overflow-hidden rounded-lg border border-neutral-200 bg-white">
              <div className="flex items-center justify-between border-b border-neutral-100 px-4 py-3">
                <p className="text-sm font-medium text-neutral-900">Recent operations</p>
                <p className="font-mono text-[11px] text-neutral-500">{operations.length} shown</p>
              </div>

              {loading ? (
                <div className="p-4 text-sm text-neutral-600">Loading operations...</div>
              ) : operations.length === 0 ? (
                <div className="p-4 text-sm text-neutral-600">No operations match the current filters.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-neutral-100 bg-neutral-50 text-xs font-medium text-neutral-500">
                      <tr>
                        <th className="px-4 py-2.5">Operation</th>
                        <th className="px-4 py-2.5">Status</th>
                        <th className="px-4 py-2.5">Stage</th>
                        <th className="px-4 py-2.5">Progress</th>
                        <th className="px-4 py-2.5">Resource</th>
                        <th className="px-4 py-2.5">Updated</th>
                        <th className="px-4 py-2.5 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-100">
                      {operations.map((operation) => (
                        <tr key={operation.id} className="align-top hover:bg-neutral-50/70">
                          <td className="max-w-xs px-4 py-3">
                            <p className="font-medium capitalize text-neutral-950">{formatOperationType(operation.type)}</p>
                            <p className="mt-1 truncate font-mono text-[11px] text-neutral-500">{operation.id}</p>
                            {operation.message ? (
                              <p className="mt-1 line-clamp-2 text-xs text-neutral-600">{operation.message}</p>
                            ) : null}
                            {operation.error_message ? (
                              <p className="mt-1 line-clamp-2 text-xs text-red-700">{operation.error_message}</p>
                            ) : null}
                          </td>
                          <td className="px-4 py-3">
                            <StatusBadge status={operation.status} />
                          </td>
                          <td className="px-4 py-3 text-sm text-neutral-700">{formatStage(operation.stage)}</td>
                          <td className="px-4 py-3">
                            <ProgressCell value={operation.progress} />
                          </td>
                          <td className="px-4 py-3">
                            <p className="text-sm text-neutral-800">{operation.resource_label || operation.resource_id || "n/a"}</p>
                            <p className="mt-1 font-mono text-[11px] text-neutral-500">{operation.resource_type || "unknown"}</p>
                          </td>
                          <td className="px-4 py-3 font-mono text-[11px] text-neutral-500">
                            {formatTimestamp(operation.updated_at)}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {canRetry(operation) ? (
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => void retryOperation(operation.id)}
                                disabled={retryingId === operation.id}
                                className="h-8 rounded-md border-neutral-200 bg-white px-3 text-sm shadow-none hover:bg-neutral-50"
                              >
                                <RotateCcw className="size-3.5" aria-hidden />
                                {retryingId === operation.id ? "Retrying..." : "Retry"}
                              </Button>
                            ) : (
                              <span className="text-xs text-neutral-400">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </AppPageFrame>
  );
}
