"""Shared display helpers for the Streamlit pages — status colors/labels and the
accent theme CSS in one place so every page looks and renders consistently."""

import requests
import streamlit as st

from config import BACKEND_URL

# Zepto-style brand treatment: a neutral dark canvas, with purple used sparingly
# as an accent (CTAs, active states, metric numbers) rather than washed across
# the whole page. Body text and backgrounds stay flat/neutral for contrast —
# only the elements a user should notice first get the purple.
ACCENT_CSS = """
<style>
.stApp {
    background-color: #0E0E12;
}
[data-testid="stSidebar"] {
    background-color: #131318;
    border-right: 1px solid #232330;
}
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    background-color: #7C3AED;
    color: #FFFFFF;
    border: none;
    border-radius: 999px;
    font-weight: 700;
    padding: 0.5rem 1.5rem;
}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
    background-color: #6D28D9;
    color: #FFFFFF;
}
/* Sidebar task history reads as a plain list (ChatGPT-style), not a stack of
   solid CTA buttons — purple stays reserved for the primary actions above.
   !important beats Streamlit's own flex-centering on the button internals. */
[data-testid="stSidebar"] .stButton > button {
    background-color: transparent;
    color: #F5F5F7;
    border: 1px solid transparent;
    border-radius: 8px;
    font-weight: 400;
    justify-content: flex-start !important;
    text-align: left !important;
    padding: 0.4rem 0.75rem;
}
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span {
    text-align: left !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #1F1F27;
    color: #FFFFFF;
    border: 1px solid #232330;
}
h1 {
    border-left: 4px solid #7C3AED;
    padding-left: 1.1rem;
    margin-left: 0.2rem;
}
[data-testid="stMetricValue"] {
    color: #9D5CFF;
}
[data-testid="stForm"] {
    background-color: #17171D;
    border: 1px solid #232330;
    border-radius: 16px;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #9D5CFF;
    border-bottom-color: #9D5CFF;
}
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.8rem;
    font-weight: 700;
    color: #22C55E;
    letter-spacing: 0.04em;
}
.live-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #22C55E;
    animation: live-pulse 1.4s infinite;
}
@keyframes live-pulse {
    0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.6); }
    70% { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
    100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}
</style>
"""


def inject_theme():
    st.markdown(ACCENT_CSS, unsafe_allow_html=True)


def live_badge(interval_seconds: int = 3):
    st.markdown(
        f'<div class="live-badge"><span class="live-dot"></span>'
        f'LIVE · updates every {interval_seconds}s</div>',
        unsafe_allow_html=True,
    )


STATUS_LABELS = {
    "online": "🟢 Online",
    "busy": "🟡 Busy",
    "offline": "🔴 Offline",
    "queued": "🟣 Queued",
    "assigned": "🔵 Assigned",
    "running": "🟡 Running",
    "completed": "🟢 Completed",
    "failed": "🔴 Failed",
    "connected": "🟢 Connected",
    "disconnected": "🔴 Disconnected",
    "task_created": "🟣 Task Created",
    "task_requeued": "🟠 Task Requeued",
    "inference_accepted": "🔵 Inference Accepted",
    "inference_completed": "🟢 Inference Completed",
}


def status_label(value: str) -> str:
    return STATUS_LABELS.get(value, value)


@st.fragment(run_every="3s")
def _live_task_list(limit: int):
    st.caption("RECENT TASKS")
    live_badge(3)

    try:
        resp = requests.get(f"{BACKEND_URL}/tasks", timeout=5)
        resp.raise_for_status()
        tasks = resp.json()[:limit]
    except requests.RequestException:
        st.caption("Master unreachable")
        return

    if not tasks:
        st.caption("No tasks yet")
        return

    for t in tasks:
        emoji = STATUS_LABELS.get(t["status"], "•").split(" ")[0]
        prompt = t["prompt"].strip() or "(empty prompt)"
        preview = prompt[:36] + ("…" if len(prompt) > 36 else "")
        if st.button(f"{emoji} {preview}", key=f"sidebar_task_{t['id']}", use_container_width=True):
            st.session_state["selected_task_id"] = t["id"]
            st.switch_page("pages/3_Tasks.py")


def render_task_sidebar(limit: int = 15):
    """ChatGPT-style task history in the sidebar — click one to open it on the
    Tasks page. Call once near the top of every page, after inject_theme().
    The list itself lives in a fragment so it polls Master every 3s without
    rerunning the whole page."""
    with st.sidebar:
        st.divider()
        if st.button("🆕 New task", use_container_width=True):
            st.session_state.pop("selected_task_id", None)
            st.switch_page("Home.py")

        _live_task_list(limit)
