import { useEffect, useRef, useState } from "react"
import { PageTitle, PageDescription } from "@/components/layout/Layout"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { api, ApiError } from "@/lib/api"
import { ChevronDown, Rocket, UploadCloud } from "lucide-react"
import { cn } from "@/lib/utils"

const FALLBACK_MODELS = ["llama3.1:8b", "llama3.1:70b", "mistral", "phi3", "gemma2"]

type Feedback = { kind: "success" | "error" | "warning"; message: string } | null

export function HomePage() {
  const [modelOptions, setModelOptions] = useState<string[]>(FALLBACK_MODELS)
  const [modelChoice, setModelChoice] = useState<string>("")
  const [customModelOpen, setCustomModelOpen] = useState(false)
  const [customModel, setCustomModel] = useState("")
  const [prompt, setPrompt] = useState("")
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<Feedback>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let cancelled = false
    api
      .listWorkers()
      .then((workers) => {
        if (cancelled) return
        const models = new Set<string>()
        for (const w of workers) {
          for (const m of w.models_available ?? []) models.add(m)
        }
        const sorted = Array.from(models).sort()
        if (sorted.length > 0) {
          setModelOptions(sorted)
          setModelChoice(sorted[0])
        } else {
          setModelChoice(FALLBACK_MODELS[0])
        }
      })
      .catch(() => {
        setModelChoice(FALLBACK_MODELS[0])
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const modelName = customModel.trim() || modelChoice
    if (!prompt.trim()) {
      setFeedback({ kind: "warning", message: "Enter a prompt first." })
      return
    }
    setSubmitting(true)
    setFeedback(null)
    try {
      const data = await api.submitInfer(prompt, modelName, file)
      setFeedback({
        kind: "success",
        message: `Task #${data.task_id} submitted (model "${modelName}") — status: ${data.status}`,
      })
      setPrompt("")
      setFile(null)
      setCustomModel("")
      if (fileInputRef.current) fileInputRef.current.value = ""
    } catch (err) {
      const message = err instanceof ApiError ? err.message : String(err)
      setFeedback({ kind: "error", message: `Failed to submit task: ${message}` })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <PageTitle>Submit a task</PageTitle>
      <PageDescription>
        Your prompt is routed to whichever node has capacity. Check{" "}
        <span className="font-medium text-[color:var(--foreground)]">Tasks</span> for progress and results, or{" "}
        <span className="font-medium text-[color:var(--foreground)]">Connected Devices</span> for node status.
      </PageDescription>

      <Card className="surface-card w-full border-0 py-0">
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="grid max-w-sm gap-2">
              <label className="text-sm font-medium">Model</label>
              <Select value={modelChoice} onValueChange={setModelChoice}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {modelOptions.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <button
                type="button"
                onClick={() => setCustomModelOpen((v) => !v)}
                className="mt-1 flex items-center gap-1 text-xs text-[color:var(--muted-foreground)] hover:text-[color:var(--foreground)]"
              >
                <ChevronDown className={cn("h-3 w-3 transition-transform", customModelOpen && "rotate-180")} />
                Use a different model
              </button>
              {customModelOpen && (
                <Input
                  placeholder="e.g. llama3.1:70b"
                  value={customModel}
                  onChange={(e) => setCustomModel(e.target.value)}
                />
              )}
            </div>

            <div className="grid gap-2">
              <label className="text-sm font-medium">Prompt</label>
              <Textarea
                placeholder="Ask something…"
                className="h-44 resize-none"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <label className="text-sm font-medium">Input file (optional)</label>
              <label
                htmlFor="input-file"
                className="flex cursor-pointer items-center gap-3 rounded-xl border border-dashed border-[color:var(--border)] px-4 py-4 text-sm text-[color:var(--muted-foreground)] transition-colors hover:border-[color:var(--ring)] hover:text-[color:var(--foreground)]"
              >
                <UploadCloud className="h-5 w-5 shrink-0" />
                {file ? file.name : "Drag & drop or click to upload — image, PDF, etc."}
              </label>
              <input
                id="input-file"
                ref={fileInputRef}
                type="file"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              <p className="text-xs text-[color:var(--muted-foreground)]">
                Uploaded to Google Drive; whichever node picks up the task downloads it from there.
              </p>
            </div>

            <Button type="submit" disabled={submitting} size="lg" className="w-full gap-2">
              <Rocket className="h-4 w-4" />
              {submitting ? "Submitting…" : "Submit task"}
            </Button>
          </form>

          {feedback && (
            <div
              className={cn(
                "mt-5 rounded-xl border px-4 py-3 text-sm",
                feedback.kind === "success" && "border-[color:var(--status-online)]/30 bg-[color:var(--status-online)]/10",
                feedback.kind === "error" && "border-[color:var(--destructive)]/30 bg-[color:var(--destructive)]/10",
                feedback.kind === "warning" && "border-[color:var(--status-busy)]/30 bg-[color:var(--status-busy)]/10",
              )}
            >
              {feedback.message}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
