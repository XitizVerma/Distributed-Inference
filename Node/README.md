# Node

Worker-side process for the distributed inference MVP. Runs on each machine that
should contribute inference capacity (e.g. laptops B and C). Detects local
hardware, registers with `Master`, sends periodic heartbeats, and executes
inference tasks assigned to it against a locally running Ollama model.

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running locally, with the target
  model already pulled, e.g.:

  ```bash
  ollama pull llama3.1:8b
  ollama serve
  ```

- `Master` backend already running and reachable from this machine.

## Installation

```bash
cd Node
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Configure — copy/edit `Node/.env`:

```
MASTER_URL=http://<master machine's LAN IP>:8000
OLLAMA_URL=http://localhost:11434
NODE_NAME=
HEARTBEAT_INTERVAL_SECONDS=5
```

The node's hostname (used as the unique key Master registers it under) is
always auto-detected from the system — there's no override for it, so two
nodes sharing a machine hostname on your network would collide; give the
machine itself a distinct hostname in that case.
`NODE_NAME` is a human-friendly label for this node — shown in Master's logs
and the `workers` table alongside its Master-assigned `worker_id`; if left
blank it falls back to the hostname.

## Running

```bash
python3 node.py
```

On startup the node:

1. Probes local hardware (`hardware_probe.py`) — CPU, RAM, GPU.
2. Classifies itself into a worker type (`worker_classifier.py`) — `gpu`,
   `apple_silicon`, `cpu_high`, or `cpu_standard`.
3. Lists locally available Ollama models.
4. Registers with `Master` via `POST /register`, sending its `node_name`
   along with its hardware info. Master upserts by hostname, so a node
   restarting keeps the same `worker_id` — that id (not the hostname) is what
   gets sent on every subsequent request, so Master can always tell which
   node it's talking to even if `NODE_NAME`/IP changes.
5. Loops, sending `POST /heartbeat` every `HEARTBEAT_INTERVAL_SECONDS`. If the
   heartbeat response carries a pending task, the node runs it in a background
   thread (so heartbeats keep flowing during long inference calls):
   - If the task has an `input_url` (a file the user attached, e.g. an image),
     it's downloaded from Google Drive first (`storage_client.py`, via `gdown`
     — handles Drive's large-file confirmation-page quirk that a plain HTTP
     GET doesn't).
   - Runs the task against the appropriate local runtime (currently Ollama for
     text; image/video adapters land later).
   - Reports the result back — `POST /tasks/{id}/result` for text, or
     `POST /tasks/{id}/result/file` (multipart) for a blob output, which
     Master then re-uploads to storage.

If this node goes offline mid-task (heartbeat timeout on the Master side),
the Master reassigns that task to another node — any result this node
later reports for it is ignored as stale.

## Files

| File | Purpose |
|---|---|
| `node.py` | Main loop: register, heartbeat, accept/run/report tasks |
| `client.py` | All HTTP calls to Master (`/register`, `/heartbeat`, `/tasks/*`) in one place |
| `hardware_probe.py` | Raw hardware detection (CPU/RAM/GPU/storage/network) |
| `worker_classifier.py` | Turns raw hardware specs into a coarse worker type label |
| `ollama_client.py` | Thin client for the local Ollama HTTP API |
| `storage_client.py` | Downloads input blobs Master hands out as Google Drive links |
| `config.py` | Loads settings from `.env` / environment variables |
