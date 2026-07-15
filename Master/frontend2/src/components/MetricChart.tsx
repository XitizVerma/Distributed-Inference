import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type { TaskInterval, WorkerMetric } from "@/lib/api"

interface Props {
  metrics: WorkerMetric[]
  dataKey: "cpu_percent" | "memory_percent" | "gpu_percent"
  color: string
  taskIntervals: TaskInterval[]
}

function fmtTime(ts: number) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

export function MetricChart({ metrics, dataKey, color, taskIntervals }: Props) {
  const rows = metrics.map((m) => ({ ...m, ts: Date.parse(m.recorded_at) }))
  const lastTs = rows.length > 0 ? rows[rows.length - 1].ts : Date.now()
  const showLabels = taskIntervals.length <= 6

  return (
    <div className="surface-card h-[280px] p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={rows} margin={{ top: 20, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="ts"
            type="number"
            domain={["dataMin", "dataMax"]}
            tickFormatter={fmtTime}
            stroke="var(--muted-foreground)"
            fontSize={11}
            axisLine={false}
            tickLine={false}
          />
          <YAxis stroke="var(--muted-foreground)" fontSize={11} unit="%" axisLine={false} tickLine={false} />
          <Tooltip
            labelFormatter={(v) => fmtTime(Number(v))}
            contentStyle={{
              background: "var(--popover)",
              border: "1px solid var(--border)",
              borderRadius: 10,
              color: "var(--foreground)",
              fontSize: 12,
              boxShadow: "0 8px 24px rgba(0, 0, 0, 0.3)",
            }}
          />
          {taskIntervals.map((interval) => {
            const x1 = Date.parse(interval.started_at)
            const x2 = interval.completed_at ? Date.parse(interval.completed_at) : lastTs
            return (
              <ReferenceArea
                key={interval.task_id}
                x1={x1}
                x2={x2}
                fill="var(--chart-task-band)"
                fillOpacity={0.15}
                stroke="none"
                label={
                  showLabels
                    ? {
                        value: `#${interval.task_id} ${interval.model_name}`,
                        position: "insideTopLeft",
                        fontSize: 10,
                        fill: "var(--muted-foreground)",
                      }
                    : undefined
                }
              />
            )
          })}
          <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
