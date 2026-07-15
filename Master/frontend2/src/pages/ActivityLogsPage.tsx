import { PageTitle } from "@/components/layout/Layout"
import { LiveBadge } from "@/components/LiveBadge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { api } from "@/lib/api"
import { usePolling } from "@/lib/usePolling"
import { statusLabel } from "@/lib/status"

export function ActivityLogsPage() {
  const { data: logs, error } = usePolling(() => api.listActivity(), 3000, [])

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <PageTitle>Activity Logs</PageTitle>
        <LiveBadge intervalSeconds={3} />
      </div>

      {error && <p className="text-sm text-[color:var(--destructive)]">Failed to fetch activity: {error}</p>}
      {logs && logs.length === 0 && (
        <p className="text-sm text-[color:var(--muted-foreground)]">No activity yet.</p>
      )}

      {logs && logs.length > 0 && (
        <div className="surface-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-[color:var(--border)] hover:bg-transparent">
                <TableHead>Time</TableHead>
                <TableHead>Event</TableHead>
                <TableHead>Worker ID</TableHead>
                <TableHead>Task ID</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((l) => (
                <TableRow key={l.id} className="border-[color:var(--border)]">
                  <TableCell className="text-[color:var(--muted-foreground)]">{l.created_at}</TableCell>
                  <TableCell className="font-medium">{statusLabel(l.event_type)}</TableCell>
                  <TableCell className="text-[color:var(--muted-foreground)]">{l.worker_id ?? "—"}</TableCell>
                  <TableCell className="text-[color:var(--muted-foreground)]">{l.task_id ?? "—"}</TableCell>
                  <TableCell className="whitespace-pre-wrap text-[color:var(--muted-foreground)]">
                    {l.details ? JSON.stringify(l.details) : "—"}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
