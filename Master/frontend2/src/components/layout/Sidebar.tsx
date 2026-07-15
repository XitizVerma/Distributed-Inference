import { NavLink, useNavigate } from "react-router-dom"
import { cn } from "@/lib/utils"
import { api, type Task } from "@/lib/api"
import { usePolling } from "@/lib/usePolling"
import { LiveBadge } from "@/components/LiveBadge"
import { StatusDot } from "@/lib/status"
import { Sparkles, MonitorSmartphone, ListChecks, ScrollText, BrainCircuit, Plus } from "lucide-react"

const NAV_ITEMS = [
  { to: "/", label: "Home", icon: Sparkles, end: true },
  { to: "/devices", label: "Connected Devices", icon: MonitorSmartphone },
  { to: "/tasks", label: "Tasks", icon: ListChecks },
  { to: "/activity", label: "Activity Logs", icon: ScrollText },
  { to: "/models", label: "Models", icon: BrainCircuit },
]

const TASK_HISTORY_LIMIT = 15

export function Sidebar() {
  const navigate = useNavigate()
  const { data: tasks } = usePolling(() => api.listTasks(), 3000, [])

  return (
    <aside className="surface-sidebar flex h-screen w-64 shrink-0 flex-col overflow-y-auto px-4 py-6">
      <div className="mb-6 flex items-center gap-2 px-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[color:var(--primary)] text-[color:var(--primary-foreground)]">
          <Sparkles className="h-4 w-4" />
        </div>
        <span className="text-sm font-semibold tracking-tight">Distributed Inference</span>
      </div>

      <nav className="flex flex-col gap-0.5">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-[color:var(--secondary)] font-medium text-[color:var(--foreground)]"
                  : "text-[color:var(--muted-foreground)] hover:bg-[color:var(--accent)] hover:text-[color:var(--foreground)]",
              )
            }
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <button
        className="mt-4 flex items-center justify-center gap-2 rounded-lg bg-[color:var(--primary)] px-3 py-2 text-sm font-medium text-[color:var(--primary-foreground)] transition-opacity hover:opacity-90"
        onClick={() => navigate("/")}
      >
        <Plus className="h-4 w-4" />
        New task
      </button>

      <div className="my-6 border-t border-[color:var(--border)]" />

      <div className="mb-3 flex items-center justify-between px-2">
        <p className="text-xs font-semibold tracking-wide text-[color:var(--muted-foreground)]">RECENT TASKS</p>
        <LiveBadge intervalSeconds={3} />
      </div>

      <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto">
        {tasks === null ? (
          <p className="px-2 text-xs text-[color:var(--muted-foreground)]">Loading…</p>
        ) : tasks.length === 0 ? (
          <p className="px-2 text-xs text-[color:var(--muted-foreground)]">No tasks yet</p>
        ) : (
          tasks.slice(0, TASK_HISTORY_LIMIT).map((t: Task) => {
            const prompt = t.prompt.trim() || "(empty prompt)"
            const preview = prompt.length > 32 ? prompt.slice(0, 32) + "…" : prompt
            return (
              <button
                key={t.id}
                className="sidebar-nav-item flex items-center gap-2 truncate px-3 py-2 text-left text-sm"
                onClick={() => navigate(`/tasks?selected=${t.id}`)}
              >
                <StatusDot status={t.status} />
                <span className="truncate">{preview}</span>
              </button>
            )
          })
        )}
      </div>
    </aside>
  )
}
