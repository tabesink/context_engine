import { Button } from "@/components/ui/button";
import { settingsCompactButtonClassName } from "@/components/settings/settings-controls";

export function DocumentRetryAction({
  canRetry,
  busy,
  onRetry,
}: {
  canRetry: boolean;
  busy: boolean;
  onRetry: () => void;
}) {
  if (!canRetry) {
    return <span className="text-xs text-[var(--muted-foreground)]">-</span>;
  }
  return (
    <Button size="sm" variant="outline" className={settingsCompactButtonClassName} disabled={busy} onClick={onRetry}>
      {busy ? "Retrying..." : "Retry"}
    </Button>
  );
}
