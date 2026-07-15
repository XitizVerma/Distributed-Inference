import { useState } from "react"
import { api, type TaskStatus } from "@/lib/api"
import { usePolling } from "@/lib/usePolling"
import { StatusDot, statusLabel } from "@/lib/status"
import { TaskDetail } from "./TaskDetail"
import { ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

export function TaskList({ status }: { status: TaskStatus }) {
  const { data: tasks, error } = usePolling(() => api.listTasks(status), 3000, [status])
  const [expandedId, setExpandedId] = useState<number | null>(null)

  if (error) return <p className="text-sm text-[color:var(--destructive)]">Failed to fetch tasks: {error}</p>
  if (tasks === null) return <p className="text-sm text-[color:var(--muted-foreground)]">Loading…</p>
  if (tasks.length === 0) return <p className="text-sm text-[color:var(--muted-foreground)]">No tasks here.</p>

  return (
    <div className="flex flex-col gap-2">
      {tasks.map((t) => {
        const preview = t.prompt.length > 64 ? t.prompt.slice(0, 64) + "…" : t.prompt
        const isOpen = expandedId === t.id
        return (
          <div key={t.id} className="surface-card overflow-hidden">
            <button
              className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm"
              onClick={() => setExpandedId(isOpen ? null : t.id)}
            >
              <ChevronRight
                className={cn(
                  "h-4 w-4 shrink-0 text-[color:var(--muted-foreground)] transition-transform",
                  isOpen && "rotate-90",
                )}
              />
              <span className="shrink-0 font-medium text-[color:var(--muted-foreground)]">#{t.id}</span>
              <span className="shrink-0 rounded-md bg-[color:var(--secondary)] px-1.5 py-0.5 text-xs font-medium">
                {t.model_name}
              </span>
              <span className="flex shrink-0 items-center gap-1.5 text-xs text-[color:var(--muted-foreground)]">
                <StatusDot status={t.status} />
                {statusLabel(t.status)}
              </span>
              <span className="truncate text-[color:var(--muted-foreground)]">{preview}</span>
            </button>
            {isOpen && (
              <div className="border-t border-[color:var(--border)] px-4 py-4">
                <TaskDetail task={t} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
