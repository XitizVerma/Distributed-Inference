const STATUS_LABELS: Record<string, string> = {
  online: "Online",
  busy: "Busy",
  offline: "Offline",
  queued: "Queued",
  assigned: "Assigned",
  running: "Running",
  completed: "Completed",
  failed: "Failed",
  connected: "Connected",
  disconnected: "Disconnected",
  task_created: "Task created",
  task_requeued: "Task requeued",
  inference_accepted: "Inference accepted",
  inference_completed: "Inference completed",
  model_command_created: "Model command created",
  model_command_completed: "Model command completed",
  sent: "Sent",
  succeeded: "Succeeded",
}

const STATUS_COLORS: Record<string, string> = {
  online: "var(--status-online)",
  busy: "var(--status-busy)",
  offline: "var(--status-offline)",
  queued: "var(--status-queued)",
  assigned: "var(--status-info)",
  running: "var(--status-busy)",
  completed: "var(--status-online)",
  failed: "var(--status-offline)",
  connected: "var(--status-online)",
  disconnected: "var(--status-offline)",
  task_created: "var(--status-queued)",
  task_requeued: "var(--status-busy)",
  inference_accepted: "var(--status-info)",
  inference_completed: "var(--status-online)",
  model_command_created: "var(--status-queued)",
  model_command_completed: "var(--status-online)",
  sent: "var(--status-info)",
  succeeded: "var(--status-online)",
}

export function statusLabel(value: string): string {
  return STATUS_LABELS[value] ?? value
}

export function statusColor(value: string): string {
  return STATUS_COLORS[value] ?? "var(--muted-foreground)"
}

export function StatusDot({ status, className }: { status: string; className?: string }) {
  return <span className={`status-dot ${className ?? ""}`} style={{ backgroundColor: statusColor(status) }} />
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm">
      <StatusDot status={status} />
      {statusLabel(status)}
    </span>
  )
}
