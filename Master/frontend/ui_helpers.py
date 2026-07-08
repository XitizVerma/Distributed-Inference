"""Shared display helpers for the Streamlit pages — status colors/labels and the
accent theme CSS in one place so every page looks and renders consistently."""

import requests
import streamlit as st

from config import BACKEND_URL

# "Liquid glass" treatment: an animated purple/indigo gradient canvas with
# frosted, translucent surfaces layered on top (backdrop-filter blur + saturate),
# hairline light borders and soft shadows — the Apple-style glassmorphism look.
# Purple stays the accent (CTAs, active states, metric numbers). The gradient
# canvas is essential: the blur needs something colorful underneath to refract,
# so surfaces read as frosted glass rather than flat panels.
ACCENT_CSS = """
<style>
/* Animated mesh-gradient canvas so the frosted panels have colour to refract. */
.stApp {
    background:
        radial-gradient(1100px 700px at 12% -8%, rgba(124, 58, 237, 0.28), transparent 60%),
        radial-gradient(1000px 800px at 92% 8%, rgba(56, 189, 248, 0.16), transparent 55%),
        radial-gradient(900px 900px at 78% 100%, rgba(168, 85, 247, 0.22), transparent 60%),
        linear-gradient(160deg, #0B0B10 0%, #101019 50%, #0B0B12 100%);
    background-attachment: fixed;
}
/* Frosted glass surface, reused across sidebar / forms / expanders / dataframes. */
[data-testid="stSidebar"] {
    background: rgba(19, 19, 26, 0.55);
    backdrop-filter: blur(22px) saturate(160%);
    -webkit-backdrop-filter: blur(22px) saturate(160%);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stForm"],
[data-testid="stExpander"] details,
div[data-testid="stDataFrame"],
[data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, 0.04) !important;
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
    border: 1px solid rgba(255, 255, 255, 0.10) !important;
    border-radius: 18px !important;
    box-shadow:
        0 8px 32px rgba(0, 0, 0, 0.35),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
/* Metric cards get the glass treatment too. */
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(14px) saturate(150%);
    -webkit-backdrop-filter: blur(14px) saturate(150%);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    box-shadow:
        0 8px 24px rgba(0, 0, 0, 0.30),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
/* Translucent, glossy CTA — a purple pill with a light top-edge highlight. */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    background: linear-gradient(180deg, rgba(139, 92, 246, 0.92), rgba(124, 58, 237, 0.92));
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 999px;
    font-weight: 700;
    padding: 0.5rem 1.5rem;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    box-shadow:
        0 6px 20px rgba(124, 58, 237, 0.35),
        inset 0 1px 0 rgba(255, 255, 255, 0.25);
    transition: transform 0.12s ease, box-shadow 0.12s ease, background 0.12s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
    background: linear-gradient(180deg, rgba(157, 92, 255, 0.98), rgba(109, 40, 217, 0.98));
    color: #FFFFFF;
    transform: translateY(-1px);
    box-shadow:
        0 10px 28px rgba(124, 58, 237, 0.45),
        inset 0 1px 0 rgba(255, 255, 255, 0.30);
}
/* Sidebar task history reads as a plain frosted list (ChatGPT-style), not a
   stack of solid CTA buttons — purple stays reserved for the primary actions.
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
    border-left: 4px solid #9D5CFF;
    padding-left: 1.1rem;
    margin-left: 0.2rem;
}
[data-testid="stMetricValue"] {
    color: #C4A6FF;
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
