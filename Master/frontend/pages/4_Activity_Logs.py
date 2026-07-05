import streamlit as st
import requests

from config import BACKEND_URL
from ui_helpers import status_label, inject_theme, render_task_sidebar, live_badge

st.set_page_config(page_title="Activity Logs", page_icon="📜", layout="wide")
inject_theme()
render_task_sidebar()
st.title("📜 Activity Logs")
live_badge(3)


@st.fragment(run_every="3s")
def render_activity():
    resp = requests.get(f"{BACKEND_URL}/activity")
    if not resp.ok:
        st.error(f"Failed to fetch activity: {resp.text}")
        return

    logs = resp.json()
    if not logs:
        st.info("No activity yet.")
        return

    display_rows = [
        {
            "Time": l["created_at"],
            "Event": status_label(l["event_type"]),
            "Worker ID": l.get("worker_id") or "—",
            "Task ID": l.get("task_id") or "—",
            "Details": l.get("details") or "—",
        }
        for l in logs
    ]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)


render_activity()
