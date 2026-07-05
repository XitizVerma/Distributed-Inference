import streamlit as st
import requests

from config import BACKEND_URL
from ui_helpers import status_label, inject_theme, render_task_sidebar, live_badge

st.set_page_config(page_title="Connected Devices", page_icon="🖥️", layout="wide")
inject_theme()
render_task_sidebar()
st.title("🖥️ Connected Devices")
live_badge(3)


@st.fragment(run_every="3s")
def render_devices():
    resp = requests.get(f"{BACKEND_URL}/workers")
    if not resp.ok:
        st.error(f"Failed to fetch nodes: {resp.text}")
        return

    workers = resp.json()
    if not workers:
        st.info("No nodes registered yet. Start a Node process pointed at this Master.")
        return

    counts = {"online": 0, "busy": 0, "offline": 0}
    for w in workers:
        counts[w["status"]] = counts.get(w["status"], 0) + 1

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total nodes", len(workers))
    col2.metric("🟢 Online", counts.get("online", 0))
    col3.metric("🟡 Busy", counts.get("busy", 0))
    col4.metric("🔴 Offline", counts.get("offline", 0))

    st.divider()

    FILTERS = {
        "All": None,
        "🟢 Online": "online",
        "🟡 Busy": "busy",
        "🔴 Offline": "offline",
    }
    selected_filter = st.radio("Filter", list(FILTERS.keys()), horizontal=True, label_visibility="collapsed")
    status_filter = FILTERS[selected_filter]

    filtered_workers = [w for w in workers if status_filter is None or w["status"] == status_filter]

    if not filtered_workers:
        st.info(f"No nodes match filter: {selected_filter}")
        return

    header = st.columns([1.8, 1.1, 1, 1.6, 1.6, 1.7, 1.6, 0.9])
    for col, label in zip(
        header, ["Node", "Status", "Type", "GPU", "CPU", "Memory (free/total MB)", "Last heartbeat", ""]
    ):
        col.markdown(f"**{label}**")

    for w in filtered_workers:
        row = st.columns([1.8, 1.1, 1, 1.6, 1.6, 1.7, 1.6, 0.9])
        row[0].write(w.get("node_name") or w["hostname"])
        row[1].markdown(status_label(w["status"]))
        row[2].write(w.get("worker_type") or "—")
        row[3].write(w.get("gpu_info") or "—")
        row[4].write(w.get("cpu_info") or "—")
        row[5].write(f"{w.get('available_memory_mb') or 0} / {w.get('total_memory_mb') or 0}")
        row[6].write(w.get("last_heartbeat_at") or "—")
        if row[7].button("📊", key=f"analytics_{w['id']}", help="View analytics for this node"):
            st.session_state["analytics_node_id"] = w["id"]
            st.switch_page("pages/5_Node_Analytics.py")


render_devices()
