export function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric-tile flex flex-1 flex-col gap-1.5 px-5 py-4">
      <span className="text-xs font-medium text-[color:var(--muted-foreground)]">{label}</span>
      <span className="text-2xl font-semibold tracking-tight text-[color:var(--foreground)]">{value}</span>
    </div>
  )
}
