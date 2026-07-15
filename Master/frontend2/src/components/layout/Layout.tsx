import type { ReactNode } from "react"
import { useLocation } from "react-router-dom"
import { Sidebar } from "./Sidebar"

const PAGE_TITLES: Record<string, string> = {
  "/": "Home",
  "/devices": "Connected Devices",
  "/tasks": "Tasks",
  "/activity": "Activity Logs",
  "/analytics": "Node Analytics",
  "/models": "Models",
}

export function Layout({ children }: { children: ReactNode }) {
  const location = useLocation()
  const title = PAGE_TITLES[location.pathname] ?? "Distributed Inference"

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="surface-topbar sticky top-0 z-10 flex h-14 shrink-0 items-center px-8">
          <span className="text-sm font-medium text-[color:var(--muted-foreground)]">{title}</span>
        </header>
        <main className="flex-1 overflow-y-auto px-8 py-10">
          <div className="fade-in mx-auto max-w-6xl">{children}</div>
        </main>
      </div>
    </div>
  )
}

export function PageTitle({ children }: { children: ReactNode }) {
  return <h1 className="mb-2 text-2xl font-semibold tracking-tight">{children}</h1>
}

export function PageDescription({ children }: { children: ReactNode }) {
  return <p className="mb-8 text-sm leading-relaxed text-[color:var(--muted-foreground)]">{children}</p>
}
