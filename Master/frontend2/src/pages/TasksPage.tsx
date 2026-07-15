import { useSearchParams } from "react-router-dom"
import { PageTitle } from "@/components/layout/Layout"
import { LiveBadge } from "@/components/LiveBadge"
import { TaskList } from "@/components/TaskList"
import { TaskDetail } from "@/components/TaskDetail"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { api } from "@/lib/api"
import { usePolling } from "@/lib/usePolling"
import { StatusDot, statusLabel } from "@/lib/status"
import { X } from "lucide-react"

export function TasksPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedId = searchParams.get("selected")

  const { data: task, error } = usePolling(
    () => (selectedId ? api.getTask(Number(selectedId)) : Promise.resolve(null)),
    3000,
    [selectedId],
  )

  function closeSelected() {
    const next = new URLSearchParams(searchParams)
    next.delete("selected")
    setSearchParams(next)
  }

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <PageTitle>Tasks</PageTitle>
        <LiveBadge intervalSeconds={3} />
      </div>

      {selectedId && (
        <div className="surface-card mb-6 p-5">
          {error ? (
            <p className="text-sm text-[color:var(--destructive)]">
              Task #{selectedId} not found: {error}
            </p>
          ) : task ? (
            <>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="flex items-center gap-2 text-base font-semibold">
                  #{task.id}
                  <span className="rounded-md bg-[color:var(--secondary)] px-1.5 py-0.5 text-xs font-medium">
                    {task.model_name}
                  </span>
                  <span className="flex items-center gap-1.5 text-xs font-normal text-[color:var(--muted-foreground)]">
                    <StatusDot status={task.status} />
                    {statusLabel(task.status)}
                  </span>
                </h2>
                <button
                  onClick={closeSelected}
                  className="flex items-center gap-1 rounded-md px-2 py-1 text-sm text-[color:var(--muted-foreground)] transition-colors hover:bg-[color:var(--accent)] hover:text-[color:var(--foreground)]"
                >
                  <X className="h-4 w-4" /> Close
                </button>
              </div>
              <TaskDetail task={task} />
            </>
          ) : (
            <p className="text-sm text-[color:var(--muted-foreground)]">Loading…</p>
          )}
        </div>
      )}

      <Tabs defaultValue="queued">
        <TabsList>
          <TabsTrigger value="queued">Queued</TabsTrigger>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>
        <TabsContent value="queued" className="mt-4">
          <TaskList status="queued" />
        </TabsContent>
        <TabsContent value="active" className="mt-4 flex flex-col gap-6">
          <div>
            <p className="mb-2 text-xs font-semibold tracking-wide text-[color:var(--muted-foreground)]">ASSIGNED</p>
            <TaskList status="assigned" />
          </div>
          <div>
            <p className="mb-2 text-xs font-semibold tracking-wide text-[color:var(--muted-foreground)]">RUNNING</p>
            <TaskList status="running" />
          </div>
        </TabsContent>
        <TabsContent value="completed" className="mt-4">
          <TaskList status="completed" />
        </TabsContent>
      </Tabs>
    </div>
  )
}
