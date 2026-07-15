import type { Task } from "@/lib/api"

export function TaskDetail({ task }: { task: Task }) {
  const mimetype = task.result_mimetype || ""
  return (
    <div className="flex flex-col gap-3 text-sm">
      <div>
        <span className="font-semibold">Prompt: </span>
        <span className="whitespace-pre-wrap">{task.prompt}</span>
      </div>
      {task.input_url && (
        <div>
          <span className="font-semibold">Input file: </span>
          <a
            href={task.input_url}
            target="_blank"
            rel="noreferrer"
            className="text-[color:var(--status-info)] underline"
          >
            {task.input_url}
          </a>
        </div>
      )}
      {task.result && (
        <div>
          <span className="mb-1 block font-semibold">Result:</span>
          <pre className="surface-card overflow-x-auto whitespace-pre-wrap p-3 text-xs">{task.result}</pre>
        </div>
      )}
      {task.result_url &&
        (mimetype.startsWith("image/") ? (
          <img src={task.result_url} alt="Task result" className="max-w-md rounded-xl border border-[color:var(--border)]" />
        ) : mimetype.startsWith("video/") ? (
          <video src={task.result_url} controls className="max-w-md rounded-xl border border-[color:var(--border)]" />
        ) : (
          <div>
            <span className="font-semibold">Result file: </span>
            <a
              href={task.result_url}
              target="_blank"
              rel="noreferrer"
              className="text-[color:var(--status-info)] underline"
            >
              {task.result_url}
            </a>
          </div>
        ))}
    </div>
  )
}
