import streamlit as st
import requests

from config import BACKEND_URL
from ui_helpers import status_label, inject_theme, render_task_sidebar, live_badge

st.set_page_config(page_title="Tasks", page_icon="📋", layout="wide")
inject_theme()
render_task_sidebar()
st.title("📋 Tasks")
live_badge(3)


def render_task_detail(t):
    st.write("**Prompt:**", t["prompt"])
    if t.get("input_url"):
        st.markdown(f"**Input file:** [{t['input_url']}]({t['input_url']})")
    if t["result"]:
        st.write("**Result:**")
        st.code(t["result"], language=None)
    if t.get("result_url"):
        mimetype = t.get("result_mimetype") or ""
        if mimetype.startswith("image/"):
            st.image(t["result_url"])
        elif mimetype.startswith("video/"):
            st.video(t["result_url"])
        else:
            st.markdown(f"**Result file:** [{t['result_url']}]({t['result_url']})")


def render_tasks(status_filter):
    params = {"status": status_filter} if status_filter else {}
    resp = requests.get(f"{BACKEND_URL}/tasks", params=params)
    if not resp.ok:
        st.error(f"Failed to fetch tasks: {resp.text}")
        return
    tasks = resp.json()
    if not tasks:
        st.info("No tasks here.")
        return
    for t in tasks:
        prompt_preview = (t["prompt"][:60] + "…") if len(t["prompt"]) > 60 else t["prompt"]
        with st.expander(f"#{t['id']} · {t['model_name']} · {status_label(t['status'])} · {prompt_preview}"):
            render_task_detail(t)


@st.fragment(run_every="3s")
def render_tasks_page():
    selected_id = st.session_state.get("selected_task_id")
    if selected_id is not None:
        resp = requests.get(f"{BACKEND_URL}/tasks/{selected_id}")
        if resp.ok:
            t = resp.json()
            with st.container(border=True):
                col_title, col_close = st.columns([5, 1])
                with col_title:
                    st.subheader(f"#{t['id']} · {t['model_name']} · {status_label(t['status'])}")
                with col_close:
                    if st.button("✖ Close", use_container_width=True):
                        st.session_state.pop("selected_task_id", None)
                        st.rerun()
                render_task_detail(t)
        else:
            st.error(f"Task #{selected_id} not found: {resp.text}")
            st.session_state.pop("selected_task_id", None)
        st.divider()

    tab_queued, tab_active, tab_completed = st.tabs(["🟣 Queued", "🟡 Active", "🟢 Completed"])

    with tab_queued:
        render_tasks("queued")

    with tab_active:
        st.caption("Assigned")
        render_tasks("assigned")
        st.caption("Running")
        render_tasks("running")

    with tab_completed:
        render_tasks("completed")


render_tasks_page()
