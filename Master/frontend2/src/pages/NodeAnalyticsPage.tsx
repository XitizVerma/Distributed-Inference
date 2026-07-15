import { useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { PageTitle, PageDescription } from "@/components/layout/Layout"
import { LiveBadge } from "@/components/LiveBadge"
import { MetricChart } from "@/components/MetricChart"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { usePolling } from "@/lib/usePolling"
import { StatusDot, statusLabel } from "@/lib/status"
import { ArrowLeft } from "lucide-react"

const RANGES: { label: string; minutes: number }[] = [
  { label: "15 min", minutes: 15 },
  { label: "1 hour", minutes: 60 },
  { label: "6 hours", minutes: 360 },
  { label: "24 hours", minutes: 1440 },
]

function NodePicker() {
  const navigate = useNavigate()
  const { data: workers } = usePolling(() => api.listWorkers(), 5000, [])
  const [chosen, setChosen] = useState<string>("")

  return (
    <div>
      <PageTitle>Node Analytics</PageTitle>
      <PageDescription>Pick a node to see its live CPU, memory, and GPU utilization.</PageDescription>
      {workers === null ? (
        <p className="text-sm text-[color:var(--muted-foreground)]">Loading…</p>
      ) : workers.length === 0 ? (
        <p className="text-sm text-[color:var(--muted-foreground)]">No nodes registered yet.</p>
      ) : (
        <div className="surface-card flex max-w-md flex-col gap-4 p-6">
          <Select value={chosen} onValueChange={setChosen}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Pick a node" />
            </SelectTrigger>
            <SelectContent>
              {workers.map((w) => (
                <SelectItem key={w.id} value={String(w.id)}>
                  {w.node_name || w.hostname} (id={w.id})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button disabled={!chosen} onClick={() => navigate(`/analytics?nodeId=${chosen}`)}>
            View analytics
          </Button>
        </div>
      )}
    </div>
  )
}

function NodeAnalyticsView({ nodeId }: { nodeId: number }) {
  const [rangeMinutes, setRangeMinutes] = useState(60)

  const { data: node, error: nodeError } = usePolling(() => api.getWorker(nodeId), 5000, [nodeId])
  const { data: metricsData, error: metricsError } = usePolling(
    () => api.getWorkerMetrics(nodeId, rangeMinutes),
    5000,
    [nodeId, rangeMinutes],
  )

  if (nodeError) {
    return <p className="text-sm text-[color:var(--destructive)]">Node {nodeId} not found — it may have been removed.</p>
  }

  const metrics = metricsData?.metrics ?? []
  const taskIntervals = metricsData?.task_intervals ?? []
  const hasGpuData = metrics.some((m) => m.gpu_percent !== null)

  return (
    <div>
      {node && (
        <>
          <div className="mb-1 flex items-center justify-between">
            <PageTitle>{node.node_name || node.hostname}</PageTitle>
            <LiveBadge intervalSeconds={5} />
          </div>
          <PageDescription>
            <span className="inline-flex items-center gap-1.5">
              <StatusDot status={node.status} />
              {statusLabel(node.status)}
            </span>{" "}
            · {node.worker_type || "unknown type"} · {node.gpu_info || "no GPU info"} · {node.cpu_info || "no CPU info"}
          </PageDescription>
        </>
      )}

      <div className="mb-6 flex gap-1 rounded-lg bg-[color:var(--muted)] p-1" style={{ width: "fit-content" }}>
        {RANGES.map((r) => (
          <button
            key={r.minutes}
            onClick={() => setRangeMinutes(r.minutes)}
            data-active={rangeMinutes === r.minutes}
            className="pill-toggle px-3 py-1.5 text-sm"
          >
            {r.label}
          </button>
        ))}
      </div>

      {metricsError && (
        <p className="text-sm text-[color:var(--destructive)]">Failed to fetch metrics: {metricsError}</p>
      )}

      {taskIntervals.length > 0 && (
        <p className="mb-4 text-xs text-[color:var(--muted-foreground)]">
          Shaded bands mark when a task was actually running on this node ({taskIntervals.length} task(s) in this
          window) — use them to spot which task caused a spike.
        </p>
      )}

      {!metricsError && metrics.length === 0 ? (
        <p className="text-sm text-[color:var(--muted-foreground)]">
          No metrics recorded for this node in the last window. Metrics only exist for nodes running the updated
          Node code that reports live CPU/memory/GPU on each heartbeat.
        </p>
      ) : (
        <div className="flex flex-col gap-8">
          <div>
            <h3 className="mb-2 text-sm font-semibold">CPU</h3>
            <MetricChart metrics={metrics} dataKey="cpu_percent" color="var(--chart-cpu)" taskIntervals={taskIntervals} />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold">Memory</h3>
            <MetricChart
              metrics={metrics}
              dataKey="memory_percent"
              color="var(--chart-memory)"
              taskIntervals={taskIntervals}
            />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold">GPU</h3>
            {hasGpuData ? (
              <MetricChart
                metrics={metrics}
                dataKey="gpu_percent"
                color="var(--chart-gpu)"
                taskIntervals={taskIntervals}
              />
            ) : (
              <p className="text-sm text-[color:var(--muted-foreground)]">
                GPU utilization isn't available for this node — it either has no discrete/NVIDIA GPU, or (common on
                Apple Silicon) the OS only exposes real-time GPU load through a root-only API, so it can't be sampled
                from an ordinary process.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export function NodeAnalyticsPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const nodeIdParam = searchParams.get("nodeId")
  const nodeId = nodeIdParam ? Number(nodeIdParam) : null

  return (
    <div>
      <button
        onClick={() => navigate("/devices")}
        className="mb-4 flex items-center gap-1 text-sm text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)]"
      >
        <ArrowLeft className="h-4 w-4" /> Connected Devices
      </button>
      {nodeId === null ? <NodePicker /> : <NodeAnalyticsView nodeId={nodeId} />}
    </div>
  )
}
