import { BACKEND_URL } from "./config"

export type WorkerStatus = "online" | "busy" | "offline"

export interface Worker {
  id: number
  hostname: string
  node_name: string | null
  ip: string | null
  gpu_info: string | null
  cpu_info: string | null
  total_memory_mb: number | null
  available_memory_mb: number | null
  worker_type: string | null
  models_available: string[] | null
  status: WorkerStatus
  last_heartbeat_at: string | null
}

export type TaskStatus = "queued" | "assigned" | "running" | "completed" | "failed"

export interface Task {
  id: number
  prompt: string
  model_name: string
  status: TaskStatus
  input_url: string | null
  result: string | null
  result_url: string | null
  result_mimetype: string | null
  created_at: string
  completed_at: string | null
}

export interface ActivityLog {
  id: number
  worker_id: number | null
  task_id: number | null
  event_type: string
  details: unknown
  created_at: string
}

export interface WorkerMetric {
  recorded_at: string
  cpu_percent: number | null
  memory_percent: number | null
  memory_used_mb: number | null
  gpu_percent: number | null
  gpu_memory_used_mb: number | null
}

export interface TaskInterval {
  task_id: number
  model_name: string
  status: string
  started_at: string
  completed_at: string | null
}

export interface WorkerMetricsResponse {
  metrics: WorkerMetric[]
  task_intervals: TaskInterval[]
}

export interface Model {
  id: number
  name: string
  backend: string
  task_type: string | null
  params: unknown
  created_at: string
}

export type ModelCommandAction = "install" | "uninstall" | "start" | "stop"
export type ModelCommandStatus = "queued" | "sent" | "succeeded" | "failed"

export interface ModelCommand {
  id: number
  model_id: number
  worker_id: number
  action: ModelCommandAction
  status: ModelCommandStatus
  error: string | null
  created_at: string
  sent_at: string | null
  completed_at: string | null
}

export interface InferResponse {
  task_id: number
  status: string
}

class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "ApiError"
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BACKEND_URL}${path}`, init)
  if (!resp.ok) {
    const text = await resp.text().catch(() => resp.statusText)
    throw new ApiError(text || `Request failed: ${resp.status}`)
  }
  if (resp.status === 204) return undefined as T
  return (await resp.json()) as T
}

function qs(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined)
  if (entries.length === 0) return ""
  return "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString()
}

export const api = {
  // Workers
  listWorkers: () => request<Worker[]>("/workers"),
  getWorker: (id: number) => request<Worker>(`/workers/${id}`),
  getWorkerMetrics: (id: number, sinceMinutes: number) =>
    request<WorkerMetricsResponse>(`/workers/${id}/metrics${qs({ since_minutes: sinceMinutes })}`),

  // Tasks
  listTasks: (status?: string) => request<Task[]>(`/tasks${qs({ status })}`),
  getTask: (id: number) => request<Task>(`/tasks/${id}`),
  submitInfer: (prompt: string, modelName: string, file?: File | null) => {
    const form = new FormData()
    form.append("prompt", prompt)
    form.append("model_name", modelName)
    if (file) form.append("input_file", file)
    return request<InferResponse>("/infer", { method: "POST", body: form })
  },

  // Activity
  listActivity: () => request<ActivityLog[]>("/activity"),

  // Models catalog
  listModels: () => request<Model[]>("/models"),
  createModel: (payload: { name: string; backend: string; task_type: string | null }) =>
    request<Model>("/models", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  deleteModel: (id: number) => request<{ ack: boolean }>(`/models/${id}`, { method: "DELETE" }),

  // Model commands
  listCommands: (limit = 50) => request<ModelCommand[]>(`/models/commands${qs({ limit })}`),
  createCommand: (modelId: number, workerId: number, action: ModelCommandAction) =>
    request<ModelCommand>(`/models/${modelId}/commands`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ worker_id: workerId, action }),
    }),
}

export { ApiError }
