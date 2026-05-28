import { cn } from "@/lib/utils";

type StatusTone = "neutral" | "info" | "success" | "warning" | "danger";

const TONE_STYLES: Record<StatusTone, string> = {
  neutral: "border-[var(--border)] bg-[var(--secondary)] text-[var(--foreground)]",
  info: "border-[var(--border)] bg-[var(--secondary)] text-[var(--foreground)]",
  success: "border-[var(--border)] bg-[var(--secondary)] text-[var(--foreground)]",
  warning: "border-[var(--border)] bg-[var(--secondary)] text-[var(--foreground)]",
  danger: "border-destructive/40 bg-destructive/10 text-destructive",
};

export function StatusChip({
  label,
  tone = "neutral",
  dot = true,
  className,
}: {
  label: string;
  tone?: StatusTone;
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        TONE_STYLES[tone],
        className,
      )}
    >
      {dot ? <span className="text-[10px]" aria-hidden>●</span> : null}
      {label}
    </span>
  );
}
