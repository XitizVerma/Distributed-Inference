# Master

Central server for the distributed inference MVP. Keeps a registry of connected
worker machines (see the companion `Node` repo), receives inference
requests, load-balances them across online workers, and tracks tasks and
activity in MySQL. Ships with a Streamlit UI for submitting prompts and
watching devices/tasks/activity live.

## Structure

```
Master/
  backend/    FastAPI API + MySQL (SQLAlchemy models, scheduler, migrations)
  frontend/   Streamlit UI (task input, connected devices, tasks, activity logs)
```

## Prerequisites

- Python 3.10+
- MySQL server running locally (or reachable over the network)
- At least one machine running `Node` with Ollama serving a model (e.g. `llama3.1:8b`)
- A Google Cloud service account with Drive API access (for blob storage — see below)

## Google Drive setup (blob storage)

Task inputs (images/PDFs/etc. a user attaches) and outputs (images/video/PDFs a
worker produces) are stored as files in Google Drive, not in MySQL. Master
uploads/downloads them via a service account:

1. In [Google Cloud Console](https://console.cloud.google.com), create a project (or reuse one),
   enable the **Google Drive API**, then create a **Service Account** and download its JSON key.
2. Save that key as `Master/backend/google_service_account.json` (already gitignored — never commit it).
3. In your own Google Drive, create a folder for task blobs, then **share it with the
   service account's email** (looks like `...@...iam.gserviceaccount.com`) as **Editor**.
   Files the service account creates in that folder count against your own Drive quota,
   not the service account's — service accounts have none of their own on regular Drive.
4. Copy the folder's ID from its URL (`drive.google.com/drive/folders/<FOLDER_ID>`) into
   `GOOGLE_DRIVE_FOLDER_ID` in `.env`.

This is one of several possible storage backends (`Master/backend/storage/`) — swapping
to MinIO/S3 later only means adding a new class there and changing `STORAGE_BACKEND`.

Uploaded blobs are made link-viewable ("anyone with the link can read") so workers can
download them without their own Google auth — don't route sensitive data through this
path as configured.

## Installation

1. Create the database and tables:

   ```bash
   cd Master/backend
   mysql -u root -p < migrations/001_init.sql
   mysql -u root -p < migrations/002_add_worker_type_and_task_requeued.sql
   mysql -u root -p < migrations/003_add_blob_urls.sql
   mysql -u root -p < migrations/004_add_node_name.sql
   ```

   (See `backend/migrations/README.md` for details on migration order.)

2. Install backend dependencies:

   ```bash
   cd Master/backend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configure the backend — copy/edit `Master/backend/.env`:

   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=distributed_inference
   DB_SSL_MODE=false

   HEARTBEAT_TIMEOUT_SECONDS=30

   STORAGE_BACKEND=google_drive
   GOOGLE_SERVICE_ACCOUNT_FILE=./google_service_account.json
   GOOGLE_DRIVE_FOLDER_ID=<your folder id>
   ```

   `DB_SSL_MODE=false` for a local MySQL; set it to `true` to require TLS to
   MySQL (e.g. most managed cloud MySQL) — this doesn't verify the server's
   certificate, it just encrypts the connection.

4. Install frontend dependencies:

   ```bash
   cd Master/frontend
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

5. Configure the frontend — copy/edit `Master/frontend/.env`:

   ```
   BACKEND_URL=http://localhost:8000
   ```

## Running

Start the backend API (from `Master/backend`):

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

FastAPI auto-generates interactive API docs — no extra setup needed:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Start the Streamlit UI (from `Master/frontend`, in a separate terminal):

```bash
streamlit run Home.py
```

Open the URL Streamlit prints (default `http://localhost:8501`). Use:

- **Task Input** — submit a prompt + model name, plus an optional input file
  (image/PDF/etc.); the file is uploaded to Google Drive and its link is handed
  to whichever worker picks up the task.
- **Connected Devices** — see registered nodes, their hardware, and status.
- **Tasks** — queued / active / completed tasks; text results render inline,
  image/video results render directly from their Drive link.
- **Activity Logs** — connected/disconnected/task events across the system.

If nodes are on other machines on your LAN, point their `Node` install at this
machine's IP via `MASTER_URL=http://<this machine's LAN IP>:8000`.

## API

| Endpoint | Purpose |
|---|---|
| `POST /register` | Node registers itself with hardware info + `node_name`; Master upserts by hostname, so it always gets back the same `worker_id` |
| `POST /heartbeat` | Node heartbeat (sends its `worker_id`); response carries an assigned task if one is pending |
| `POST /infer` | Submit a prompt (+ optional input file); creates a task and assigns it to an online node |
| `GET /tasks`, `GET /tasks/{id}` | List/inspect tasks |
| `POST /tasks/{id}/accept` | Node acknowledges it started a task |
| `POST /tasks/{id}/result` | Node submits a text result |
| `POST /tasks/{id}/result/file` | Node submits a blob result (image/video/pdf); uploaded to storage, URL saved on the task |
| `GET /workers` | List registered nodes and their status |
| `GET /activity` | Recent activity log entries |
| `GET /health` | Liveness + DB check |

## Failure handling

A background thread checks for nodes with a stale heartbeat
(`HEARTBEAT_TIMEOUT_SECONDS`), marks them offline, and requeues any task they
were holding to another online node (`backend/scheduler.py`). A late result
from a node that gets reclaimed this way is ignored rather than overwriting
whatever result the reassigned node already produced.
