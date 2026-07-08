import streamlit as st
import requests

from config import BACKEND_URL
from ui_helpers import status_label, inject_theme, render_task_sidebar, live_badge

st.set_page_config(page_title="Models", page_icon="🧠", layout="wide")
inject_theme()
render_task_sidebar()
st.title("🧠 Models")

ACTIONS = ["install", "uninstall", "start", "stop"]
ACTION_HELP = {
    "install": "Download the model onto the node's disk",
    "uninstall": "Remove the model from the node's disk",
    "start": "Preload into GPU/RAM so it's warm for inference",
    "stop": "Evict from memory (stays installed on disk)",
}


def _get(path, **kwargs):
    return requests.get(f"{BACKEND_URL}{path}", timeout=5, **kwargs)


# --- Catalog ---------------------------------------------------------------

st.subheader("Model catalog")

with st.form("add_model", clear_on_submit=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    name = c1.text_input("Model name", placeholder="llama3.1:8b")
    backend = c2.selectbox("Backend", ["ollama", "huggingface"])
    task_type = c3.text_input("Task type", placeholder="text")
    if st.form_submit_button("➕ Add model") and name.strip():
        resp = requests.post(
            f"{BACKEND_URL}/models",
            json={"name": name.strip(), "backend": backend, "task_type": task_type.strip() or None},
            timeout=5,
        )
        if resp.ok:
            st.success(f"Added {name.strip()} ({backend})")
        else:
            st.error(f"Failed to add model: {resp.text}")

models_resp = _get("/models")
models = models_resp.json() if models_resp.ok else []

if not models:
    st.info("No models in the catalog yet. Add one above.")
else:
    header = st.columns([2, 1, 1, 1])
    for col, label in zip(header, ["Name", "Backend", "Task type", ""]):
        col.markdown(f"**{label}**")
    for m in models:
        row = st.columns([2, 1, 1, 1])
        row[0].write(m["name"])
        row[1].write(m["backend"])
        row[2].write(m.get("task_type") or "—")
        if row[3].button("🗑 Delete", key=f"del_model_{m['id']}"):
            requests.delete(f"{BACKEND_URL}/models/{m['id']}", timeout=5)
            st.rerun()

st.divider()

# --- Control ---------------------------------------------------------------

st.subheader("Control models on a node")

workers_resp = _get("/workers")
workers = workers_resp.json() if workers_resp.ok else []

if not workers:
    st.info("No nodes registered yet.")
elif not models:
    st.info("Add a model to the catalog first.")
else:
    def _worker_label(w):
        return f"{w.get('node_name') or w['hostname']} · {status_label(w['status'])}"

    worker_map = {_worker_label(w): w for w in workers}
    model_map = {f"{m['name']} ({m['backend']})": m for m in models}

    c1, c2 = st.columns(2)
    sel_worker = worker_map[c1.selectbox("Node", list(worker_map.keys()))]
    sel_model = model_map[c2.selectbox("Model", list(model_map.keys()))]

    installed = sel_worker.get("models_available") or []
    st.caption("Installed on this node: " + (", ".join(installed) if installed else "none reported"))

    btn_cols = st.columns(len(ACTIONS))
    for col, action in zip(btn_cols, ACTIONS):
        if col.button(action.capitalize(), key=f"cmd_{action}", help=ACTION_HELP[action]):
            resp = requests.post(
                f"{BACKEND_URL}/models/{sel_model['id']}/commands",
                json={"worker_id": sel_worker["id"], "action": action},
                timeout=5,
            )
            if resp.ok:
                st.success(f"Queued '{action}' for {sel_model['name']} on {_worker_label(sel_worker)}")
            else:
                st.error(f"Failed: {resp.text}")

st.divider()

# --- Command history -------------------------------------------------------


@st.fragment(run_every="3s")
def render_command_history():
    st.subheader("Command history")
    live_badge(3)

    resp = _get("/models/commands", params={"limit": 50})
    if not resp.ok:
        st.error(f"Failed to fetch commands: {resp.text}")
        return
    commands = resp.json()
    if not commands:
        st.caption("No commands issued yet.")
        return

    # Resolve model/worker names for display without an N+1 per row.
    model_names = {m["id"]: m["name"] for m in (_get("/models").json() if _get("/models").ok else [])}
    worker_names = {
        w["id"]: (w.get("node_name") or w["hostname"])
        for w in (_get("/workers").json() if _get("/workers").ok else [])
    }

    header = st.columns([0.6, 1.6, 1.4, 1, 1, 2])
    for col, label in zip(header, ["#", "Model", "Node", "Action", "Status", "Error"]):
        col.markdown(f"**{label}**")
    for c in commands:
        row = st.columns([0.6, 1.6, 1.4, 1, 1, 2])
        row[0].write(c["id"])
        row[1].write(model_names.get(c["model_id"], f"#{c['model_id']}"))
        row[2].write(worker_names.get(c["worker_id"], f"#{c['worker_id']}"))
        row[3].write(c["action"])
        row[4].markdown(status_label(c["status"]))
        row[5].write(c.get("error") or "—")


render_command_history()
