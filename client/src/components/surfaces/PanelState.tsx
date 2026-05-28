import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function PanelState({
  title,
  description,
  tone = "neutral",
  actions,
  className,
}: {
  title: string;
  description?: string;
  tone?: "neutral" | "danger";
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border p-4",
        tone === "danger"
          ? "border-destructive/40 bg-destructive/5"
          : "border-[var(--border)] bg-[var(--background)]",
        className,
      )}
    >
      <p className={cn("text-sm font-medium", tone === "danger" ? "text-destructive" : "text-[var(--foreground)]")}>
        {title}
      </p>
      {description ? <p className="mt-1 text-xs text-[var(--muted-foreground)]">{description}</p> : null}
      {actions ? <div className="mt-3">{actions}</div> : null}
    </div>
  );
}
