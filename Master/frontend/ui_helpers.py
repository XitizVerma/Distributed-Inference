"""Shared display helpers for the Streamlit pages — status colors/labels and the
accent theme CSS in one place so every page looks and renders consistently."""

import requests
import streamlit as st

from config import BACKEND_URL

# Neutral "liquid glass" treatment: a soft, near-monochrome dark canvas with
# frosted, translucent surfaces layered on top (backdrop-filter blur + saturate),
# hairline light borders and soft shadows — the Apple-style glassmorphism look
# with NO brand-colour accent. Everything reads as clear/white frosted glass.
# The subtle cool gradient exists only to give the blur something to refract;
# it stays neutral (grey/blue-grey) so nothing reads as "purple".
ACCENT_CSS = """
<style>
/* Neutral canvas with a bit more tonal movement, so the near-clear glass has
   something worth blurring — like the desktop showing through a macOS panel. */
.stApp {
    background:
        radial-gradient(900px 600px at 10% -6%, rgba(255, 255, 255, 0.10), transparent 58%),
        radial-gradient(1000px 800px at 92% 6%, rgba(148, 163, 184, 0.14), transparent 55%),
        radial-gradient(850px 850px at 80% 104%, rgba(226, 232, 240, 0.08), transparent 60%),
        radial-gradient(700px 500px at 45% 55%, rgba(255, 255, 255, 0.04), transparent 60%),
        linear-gradient(160deg, #0C0D10 0%, #12141A 50%, #0B0C0F 100%);
    background-attachment: fixed;
}
/* Frosted glass surface — very translucent + heavy blur, macOS menu-bar style.
   The specular top-edge highlight (inset 0 1px) is what sells it as glass. */
[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(40px) saturate(180%);
    -webkit-backdrop-filter: blur(40px) saturate(180%);
    border-right: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.14);
}
[data-testid="stForm"],
[data-testid="stExpander"] details,
div[data-testid="stDataFrame"],
[data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.02) !important;
    backdrop-filter: blur(36px) saturate(180%);
    -webkit-backdrop-filter: blur(36px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.14) !important;
    border-radius: 20px !important;
    box-shadow:
        0 10px 40px rgba(0, 0, 0, 0.30),
        inset 0 1px 0 rgba(255, 255, 255, 0.18),
        inset 0 0 0 0.5px rgba(255, 255, 255, 0.04);
}
/* Metric cards get the glass treatment too. */
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(30px) saturate(180%);
    -webkit-backdrop-filter: blur(30px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    box-shadow:
        0 10px 32px rgba(0, 0, 0, 0.28),
        inset 0 1px 0 rgba(255, 255, 255, 0.18);
}
/* Clear glass CTA — translucent white pill with a light top-edge highlight. */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    background: rgba(255, 255, 255, 0.06);
    color: #F5F5F7;
    border: 1px solid rgba(255, 255, 255, 0.20);
    border-radius: 999px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
    backdrop-filter: blur(20px) saturate(180%);
    -webkit-backdrop-filter: blur(20px) saturate(180%);
    box-shadow:
        0 6px 20px rgba(0, 0, 0, 0.28),
        inset 0 1px 0 rgba(255, 255, 255, 0.28);
    transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.30);
    transform: translateY(-1px);
    box-shadow:
        0 10px 28px rgba(0, 0, 0, 0.38),
        inset 0 1px 0 rgba(255, 255, 255, 0.34);
}
/* Sidebar task history reads as a plain list (ChatGPT-style), not a stack of
   glass CTA buttons.
   !important beats Streamlit's own flex-centering on the button internals. */
[data-testid="stSidebar"] .stButton > button {
    background: transparent;
    color: #F5F5F7;
    border: 1px solid transparent;
    border-radius: 10px;
    font-weight: 400;
    justify-content: flex-start !important;
    text-align: left !important;
    padding: 0.4rem 0.75rem;
    box-shadow: none;
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
}
[data-testid="stSidebar"] .stButton > button div,
[data-testid="stSidebar"] .stButton > button p,
[data-testid="stSidebar"] .stButton > button span {
    text-align: left !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.12);
    transform: none;
    box-shadow: none;
}
h1 {
    border-left: 4px solid rgba(255, 255, 255, 0.25);
    padding-left: 1.1rem;
    margin-left: 0.2rem;
}
[data-testid="stMetricValue"] {
    color: #F5F5F7;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #FFFFFF;
    border-bottom-color: rgba(255, 255, 255, 0.6);
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
    "model_command_created": "🟣 Model Command Created",
    "model_command_completed": "🟢 Model Command Completed",
    "sent": "🔵 Sent",
    "succeeded": "🟢 Succeeded",
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
