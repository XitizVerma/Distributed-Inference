import { useState } from "react"
import { PageTitle, PageDescription } from "@/components/layout/Layout"
import { LiveBadge } from "@/components/LiveBadge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Separator } from "@/components/ui/separator"
import { api, type ModelCommandAction } from "@/lib/api"
import { usePolling } from "@/lib/usePolling"
import { StatusDot, statusLabel } from "@/lib/status"
import { Trash2 } from "lucide-react"

const ACTIONS: ModelCommandAction[] = ["install", "uninstall", "start", "stop"]
const ACTION_HELP: Record<ModelCommandAction, string> = {
  install: "Download the model onto the node's disk",
  uninstall: "Remove the model from the node's disk",
  start: "Preload into GPU/RAM so it's warm for inference",
  stop: "Evict from memory (stays installed on disk)",
}

function CatalogSection({ onChanged }: { onChanged: () => void }) {
  const { data: models, error, refresh } = usePolling(() => api.listModels(), 5000, [])
  const [name, setName] = useState("")
  const [backend, setBackend] = useState("ollama")
  const [taskType, setTaskType] = useState("")
  const [feedback, setFeedback] = useState<string | null>(null)

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    try {
      await api.createModel({ name: name.trim(), backend, task_type: taskType.trim() || null })
      setFeedback(`Added ${name.trim()} (${backend})`)
      setName("")
      setTaskType("")
      refresh()
      onChanged()
    } catch (err) {
      setFeedback(`Failed to add model: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  async function handleDelete(id: number) {
    await api.deleteModel(id)
    refresh()
    onChanged()
  }

  return (
    <section className="mb-12">
      <h2 className="mb-4 text-base font-semibold">Model catalog</h2>

      <form onSubmit={handleAdd} className="surface-card mb-4 flex flex-wrap items-end gap-3 p-4">
        <div className="flex min-w-[180px] flex-1 flex-col gap-1.5">
          <label className="text-xs font-medium text-[color:var(--muted-foreground)]">Model name</label>
          <Input placeholder="llama3.1:8b" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="flex w-40 flex-col gap-1.5">
          <label className="text-xs font-medium text-[color:var(--muted-foreground)]">Backend</label>
          <Select value={backend} onValueChange={setBackend}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ollama">ollama</SelectItem>
              <SelectItem value="huggingface">huggingface</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex w-40 flex-col gap-1.5">
          <label className="text-xs font-medium text-[color:var(--muted-foreground)]">Task type</label>
          <Input placeholder="text" value={taskType} onChange={(e) => setTaskType(e.target.value)} />
        </div>
        <Button type="submit">Add model</Button>
      </form>

      {feedback && <p className="mb-4 text-sm text-[color:var(--muted-foreground)]">{feedback}</p>}
      {error && <p className="text-sm text-[color:var(--destructive)]">Failed to fetch models: {error}</p>}

      {models && models.length === 0 ? (
        <p className="text-sm text-[color:var(--muted-foreground)]">No models in the catalog yet. Add one above.</p>
      ) : models && models.length > 0 ? (
        <div className="surface-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-[color:var(--border)] hover:bg-transparent">
                <TableHead>Name</TableHead>
                <TableHead>Backend</TableHead>
                <TableHead>Task type</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {models.map((m) => (
                <TableRow key={m.id} className="border-[color:var(--border)]">
                  <TableCell className="font-medium">{m.name}</TableCell>
                  <TableCell className="text-[color:var(--muted-foreground)]">{m.backend}</TableCell>
                  <TableCell className="text-[color:var(--muted-foreground)]">{m.task_type || "—"}</TableCell>
                  <TableCell>
                    <button
                      onClick={() => handleDelete(m.id)}
                      className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-[color:var(--destructive)] transition-colors hover:bg-[color:var(--destructive)]/10"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Delete
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : null}
    </section>
  )
}

function ControlSection({ refreshKey }: { refreshKey: number }) {
  const { data: workers } = usePolling(() => api.listWorkers(), 5000, [refreshKey])
  const { data: models } = usePolling(() => api.listModels(), 5000, [refreshKey])
  const [workerId, setWorkerId] = useState<string>("")
  const [modelId, setModelId] = useState<string>("")
  const [feedback, setFeedback] = useState<string | null>(null)

  const selectedWorker = workers?.find((w) => String(w.id) === workerId)
  const selectedModel = models?.find((m) => String(m.id) === modelId)

  async function handleAction(action: ModelCommandAction) {
    if (!selectedWorker || !selectedModel) return
    try {
      await api.createCommand(selectedModel.id, selectedWorker.id, action)
      setFeedback(
        `Queued '${action}' for ${selectedModel.name} on ${selectedWorker.node_name || selectedWorker.hostname}`,
      )
    } catch (err) {
      setFeedback(`Failed: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  return (
    <section className="mb-12">
      <h2 className="mb-4 text-base font-semibold">Control models on a node</h2>

      {workers && workers.length === 0 ? (
        <p className="text-sm text-[color:var(--muted-foreground)]">No nodes registered yet.</p>
      ) : models && models.length === 0 ? (
        <p className="text-sm text-[color:var(--muted-foreground)]">Add a model to the catalog first.</p>
      ) : (
        <div className="surface-card flex flex-col gap-5 p-5">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-[color:var(--muted-foreground)]">Node</label>
              <Select value={workerId} onValueChange={setWorkerId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a node" />
                </SelectTrigger>
                <SelectContent>
                  {workers?.map((w) => (
                    <SelectItem key={w.id} value={String(w.id)}>
                      {w.node_name || w.hostname} · {statusLabel(w.status)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-[color:var(--muted-foreground)]">Model</label>
              <Select value={modelId} onValueChange={setModelId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {models?.map((m) => (
                    <SelectItem key={m.id} value={String(m.id)}>
                      {m.name} ({m.backend})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {selectedWorker && (
            <p className="text-xs text-[color:var(--muted-foreground)]">
              Installed on this node:{" "}
              {selectedWorker.models_available && selectedWorker.models_available.length > 0
                ? selectedWorker.models_available.join(", ")
                : "none reported"}
            </p>
          )}

          <Separator />

          <div className="flex flex-wrap gap-2">
            {ACTIONS.map((action) => (
              <Button
                key={action}
                type="button"
                variant="outline"
                title={ACTION_HELP[action]}
                disabled={!selectedWorker || !selectedModel}
                onClick={() => handleAction(action)}
                className="capitalize"
              >
                {action}
              </Button>
            ))}
          </div>

          {feedback && <p className="text-sm text-[color:var(--muted-foreground)]">{feedback}</p>}
        </div>
      )}
    </section>
  )
}

function CommandHistorySection() {
  const { data: commands, error } = usePolling(() => api.listCommands(50), 3000, [])
  const { data: models } = usePolling(() => api.listModels(), 5000, [])
  const { data: workers } = usePolling(() => api.listWorkers(), 5000, [])

  const modelNames = new Map((models ?? []).map((m) => [m.id, m.name]))
  const workerNames = new Map((workers ?? []).map((w) => [w.id, w.node_name || w.hostname]))

  return (
    <section>
      <div className="mb-4 flex items-center gap-3">
        <h2 className="text-base font-semibold">Command history</h2>
        <LiveBadge intervalSeconds={3} />
      </div>

      {error && <p className="text-sm text-[color:var(--destructive)]">Failed to fetch commands: {error}</p>}
      {commands && commands.length === 0 && (
        <p className="text-sm text-[color:var(--muted-foreground)]">No commands issued yet.</p>
      )}

      {commands && commands.length > 0 && (
        <div className="surface-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-[color:var(--border)] hover:bg-transparent">
                <TableHead>#</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Node</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Error</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {commands.map((c) => (
                <TableRow key={c.id} className="border-[color:var(--border)]">
                  <TableCell className="text-[color:var(--muted-foreground)]">{c.id}</TableCell>
                  <TableCell className="font-medium">{modelNames.get(c.model_id) ?? `#${c.model_id}`}</TableCell>
                  <TableCell>{workerNames.get(c.worker_id) ?? `#${c.worker_id}`}</TableCell>
                  <TableCell className="capitalize">{c.action}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center gap-1.5">
                      <StatusDot status={c.status} />
                      {statusLabel(c.status)}
                    </span>
                  </TableCell>
                  <TableCell className="text-[color:var(--destructive)]">{c.error || "—"}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </section>
  )
}

export function ModelsPage() {
  const [refreshKey, setRefreshKey] = useState(0)

  return (
    <div>
      <PageTitle>Models</PageTitle>
      <PageDescription>Manage the model catalog and control what's loaded on each node.</PageDescription>
      <CatalogSection onChanged={() => setRefreshKey((k) => k + 1)} />
      <ControlSection refreshKey={refreshKey} />
      <CommandHistorySection />
    </div>
  )
}
