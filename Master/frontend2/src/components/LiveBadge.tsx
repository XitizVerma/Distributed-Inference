export function LiveBadge({ intervalSeconds = 3 }: { intervalSeconds?: number }) {
  return (
    <div className="inline-flex items-center gap-1.5 text-xs font-medium text-[color:var(--muted-foreground)]">
      <span className="live-dot" />
      Live · every {intervalSeconds}s
    </div>
  )
}
