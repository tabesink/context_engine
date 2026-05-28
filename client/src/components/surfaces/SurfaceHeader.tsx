import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function SurfaceHeader({
  title,
  description,
  actions,
  className,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("flex flex-wrap items-start justify-between gap-3", className)}>
      <div>
        <p className="text-sm font-medium text-[var(--foreground)]">{title}</p>
        {description ? <p className="mt-1 text-xs text-[var(--muted-foreground)]">{description}</p> : null}
      </div>
      {actions ? <div>{actions}</div> : null}
    </header>
  );
}
