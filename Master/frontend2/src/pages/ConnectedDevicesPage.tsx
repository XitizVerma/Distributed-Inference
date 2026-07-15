import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { PageTitle } from "@/components/layout/Layout"
import { LiveBadge } from "@/components/LiveBadge"
import { MetricCard } from "@/components/MetricCard"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { api, type Worker, type WorkerStatus } from "@/lib/api"
import { usePolling } from "@/lib/usePolling"
import { StatusDot, statusLabel } from "@/lib/status"
import { BarChart3 } from "lucide-react"

const FILTERS: { label: string; value: WorkerStatus | null }[] = [
  { label: "All", value: null },
  { label: "Online", value: "online" },
  { label: "Busy", value: "busy" },
  { label: "Offline", value: "offline" },
]

export function ConnectedDevicesPage() {
  const navigate = useNavigate()
  const { data: workers, error } = usePolling(() => api.listWorkers(), 3000, [])
  const [filter, setFilter] = useState<WorkerStatus | null>(null)

  const counts = useMemo(() => {
    const c: Record<string, number> = { online: 0, busy: 0, offline: 0 }
    for (const w of workers ?? []) c[w.status] = (c[w.status] ?? 0) + 1
    return c
  }, [workers])

  const filtered = (workers ?? []).filter((w) => filter === null || w.status === filter)

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <PageTitle>Connected Devices</PageTitle>
        <LiveBadge intervalSeconds={3} />
      </div>

      {error && <p className="text-sm text-[color:var(--destructive)]">Failed to fetch nodes: {error}</p>}

      {workers && workers.length === 0 ? (
        <p className="text-sm text-[color:var(--muted-foreground)]">
          No nodes registered yet. Start a Node process pointed at this Master.
        </p>
      ) : (
        <>
          <div className="mb-8 flex flex-wrap gap-4">
            <MetricCard label="Total nodes" value={workers?.length ?? 0} />
            <MetricCard label="Online" value={counts.online ?? 0} />
            <MetricCard label="Busy" value={counts.busy ?? 0} />
            <MetricCard label="Offline" value={counts.offline ?? 0} />
          </div>

          <div className="mb-4 flex gap-1 rounded-lg bg-[color:var(--muted)] p-1">
            {FILTERS.map((f) => (
              <button
                key={f.label}
                onClick={() => setFilter(f.value)}
                data-active={filter === f.value}
                className="pill-toggle flex-1 px-3 py-1.5 text-sm"
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="surface-card overflow-hidden">
            {filtered.length === 0 ? (
              <p className="p-6 text-sm text-[color:var(--muted-foreground)]">No nodes match this filter.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow className="border-[color:var(--border)] hover:bg-transparent">
                    <TableHead>Node</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>GPU</TableHead>
                    <TableHead>CPU</TableHead>
                    <TableHead>Memory (free/total MB)</TableHead>
                    <TableHead>Last heartbeat</TableHead>
                    <TableHead />
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((w: Worker) => (
                    <TableRow key={w.id} className="border-[color:var(--border)]">
                      <TableCell className="font-medium">{w.node_name || w.hostname}</TableCell>
                      <TableCell>
                        <span className="inline-flex items-center gap-1.5">
                          <StatusDot status={w.status} />
                          {statusLabel(w.status)}
                        </span>
                      </TableCell>
                      <TableCell className="text-[color:var(--muted-foreground)]">{w.worker_type || "—"}</TableCell>
                      <TableCell className="text-[color:var(--muted-foreground)]">{w.gpu_info || "—"}</TableCell>
                      <TableCell className="text-[color:var(--muted-foreground)]">{w.cpu_info || "—"}</TableCell>
                      <TableCell className="text-[color:var(--muted-foreground)]">
                        {w.available_memory_mb ?? 0} / {w.total_memory_mb ?? 0}
                      </TableCell>
                      <TableCell className="text-[color:var(--muted-foreground)]">{w.last_heartbeat_at || "—"}</TableCell>
                      <TableCell>
                        <button
                          title="View analytics for this node"
                          onClick={() => navigate(`/analytics?nodeId=${w.id}`)}
                          className="rounded-md p-1.5 text-[color:var(--muted-foreground)] transition-colors hover:bg-[color:var(--accent)] hover:text-[color:var(--foreground)]"
                        >
                          <BarChart3 className="h-4 w-4" />
                        </button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </>
      )}
    </div>
  )
}
