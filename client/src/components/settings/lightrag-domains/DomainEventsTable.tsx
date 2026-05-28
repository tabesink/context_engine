import type { AdminAuditLog } from "@/lib/api/admin-documents";
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table";

function formatDateLabel(value: string): string {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return value;
  return new Date(timestamp).toLocaleString();
}

export function DomainEventsTable({
  domainId,
  logs,
  limit = 5,
}: {
  domainId: string;
  logs: AdminAuditLog[];
  limit?: number;
}) {
  const rows = logs.slice(0, limit);

  return (
    <div className="space-y-2">
      <div className="space-y-0.5">
        <p className="text-sm font-medium text-foreground">Recent events</p>
        <p className="text-xs text-muted-foreground">Lifecycle events for {domainId}</p>
      </div>
      {rows.length === 0 ? (
        <p className="text-xs text-muted-foreground">No events yet.</p>
      ) : (
        <Table>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id} className="border-border/60 hover:bg-transparent">
                <TableCell className="max-w-0 truncate py-2 pl-0 text-xs font-medium text-foreground">
                  {row.event}
                </TableCell>
                <TableCell className="whitespace-nowrap py-2 pr-0 text-right text-xs text-muted-foreground">
                  {formatDateLabel(row.created_at)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
