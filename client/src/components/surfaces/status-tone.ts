export type SurfaceStatusTone = "neutral" | "info" | "success" | "warning" | "danger";

export function toneForProcessingStatus(status?: string | null): SurfaceStatusTone {
  if (!status) return "neutral";
  const value = status.toLowerCase();
  if (value === "failed" || value === "error" || value === "unreachable") return "danger";
  if (value === "running" || value === "busy" || value === "indexing") return "info";
  if (value === "queued" || value === "uploaded" || value === "stale") return "warning";
  if (value === "ready" || value === "completed" || value === "indexed") return "success";
  return "neutral";
}
