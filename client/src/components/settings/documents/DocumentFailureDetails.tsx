export function DocumentFailureDetails({ message }: { message?: string | null }) {
  if (!message) return <span className="text-xs text-[var(--muted-foreground)]">-</span>;
  return (
    <details>
      <summary className="cursor-pointer list-none text-xs text-destructive">Failed: show details</summary>
      <p className="mt-1 whitespace-pre-wrap text-xs text-[var(--muted-foreground)]">{message}</p>
    </details>
  );
}
