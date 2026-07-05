import streamlit as st
import requests
import plotly.graph_objects as go

from config import BACKEND_URL
from ui_helpers import status_label, inject_theme, render_task_sidebar, live_badge

st.set_page_config(page_title="Node Analytics", page_icon="📊", layout="wide")
inject_theme()
render_task_sidebar()

if st.button("⬅ Connected Devices"):
    st.session_state.pop("analytics_node_id", None)
    st.switch_page("pages/2_Connected_Devices.py")

node_id = st.session_state.get("analytics_node_id")

if node_id is None:
    st.title("📊 Node Analytics")
    resp = requests.get(f"{BACKEND_URL}/workers")
    workers = resp.json() if resp.ok else []
    if not workers:
        st.info("No nodes registered yet.")
        st.stop()
    labels = {w["id"]: f"{w.get('node_name') or w['hostname']} (id={w['id']})" for w in workers}
    chosen = st.selectbox("Pick a node", list(labels.keys()), format_func=lambda i: labels[i])
    if st.button("View analytics", type="primary"):
        st.session_state["analytics_node_id"] = chosen
        st.rerun()
    st.stop()

RANGES = {"15 min": 15, "1 hour": 60, "6 hours": 360, "24 hours": 1440}


def add_task_bands(fig, task_intervals, chart_right_edge):
    """Shades each task's actual running window on the chart, so a CPU/memory/
    GPU spike can be visually matched against the task that caused it —
    derived from tasks.started_at/completed_at, not a separately stored flag."""
    # With many tasks in view, per-band text labels overlap into unreadable
    # clutter — keep the shading either way, but only label when it's legible.
    # Passing annotation_text=None doesn't suppress the label — Plotly falls
    # back to its own literal "new text" placeholder — so the annotation_*
    # kwargs must be omitted entirely rather than passed as None.
    show_labels = len(task_intervals) <= 6
    for interval in task_intervals:
        x0 = interval["started_at"]
        # still running: shade to the last plotted point rather than an open-ended x1,
        # which add_vrect can't render
        x1 = interval["completed_at"] or chart_right_edge
        vrect_kwargs = dict(x0=x0, x1=x1, fillcolor="#7C3AED", opacity=0.15, line_width=0)
        if show_labels:
            vrect_kwargs.update(
                annotation_text=f"#{interval['task_id']} {interval['model_name']}",
                annotation_position="top left", annotation_font_size=10,
            )
        fig.add_vrect(**vrect_kwargs)


def make_chart(recorded_at, values, name, color, y_suffix, task_intervals):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=recorded_at, y=values, mode="lines", name=name,
        line=dict(color=color, width=2),
        hovertemplate=f"%{{y}}{y_suffix}<extra></extra>",
    ))
    add_task_bands(fig, task_intervals, chart_right_edge=recorded_at[-1])
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="#17171D", plot_bgcolor="#17171D",
        font_color="#F5F5F7",
        xaxis=dict(gridcolor="#232330"),
        yaxis=dict(gridcolor="#232330", title=y_suffix or None),
        showlegend=False,
    )
    return fig


@st.fragment(run_every="5s")
def render_analytics():
    resp = requests.get(f"{BACKEND_URL}/workers/{node_id}")
    if not resp.ok:
        st.error(f"Node {node_id} not found — it may have been removed.")
        return
    node = resp.json()

    st.title(f"📊 {node.get('node_name') or node['hostname']}")
    live_badge(5)
    st.caption(
        f"{status_label(node['status'])} · {node.get('worker_type') or 'unknown type'} · "
        f"{node.get('gpu_info') or 'no GPU info'} · {node.get('cpu_info') or 'no CPU info'}"
    )

    range_label = st.radio("Time range", list(RANGES.keys()), horizontal=True, index=1)
    since_minutes = RANGES[range_label]

    metrics_resp = requests.get(
        f"{BACKEND_URL}/workers/{node_id}/metrics", params={"since_minutes": since_minutes}
    )
    if not metrics_resp.ok:
        st.error(f"Failed to fetch metrics: {metrics_resp.text}")
        return

    data = metrics_resp.json()
    metrics = data["metrics"]
    task_intervals = data["task_intervals"]

    if task_intervals:
        st.caption(f"🟣 Shaded bands mark when a task was actually running on this node "
                   f"({len(task_intervals)} task(s) in this window) — use them to spot which "
                   f"task caused a spike.")

    if not metrics:
        st.info(f"No metrics recorded for this node in the last {range_label}. "
                f"Metrics only exist for nodes running the updated Node code that reports "
                f"live CPU/memory/GPU on each heartbeat.")
        return

    recorded_at = [m["recorded_at"] for m in metrics]
    cpu = [m["cpu_percent"] for m in metrics]
    mem = [m["memory_percent"] for m in metrics]
    gpu = [m["gpu_percent"] for m in metrics]
    has_gpu_data = any(v is not None for v in gpu)

    st.subheader("CPU")
    st.plotly_chart(make_chart(recorded_at, cpu, "CPU %", "#F59E0B", "%", task_intervals),
                     use_container_width=True, config={"displayModeBar": False})

    st.subheader("Memory")
    st.plotly_chart(make_chart(recorded_at, mem, "Memory %", "#60A5FA", "%", task_intervals),
                     use_container_width=True, config={"displayModeBar": False})

    st.subheader("GPU")
    if has_gpu_data:
        st.plotly_chart(make_chart(recorded_at, gpu, "GPU %", "#22C55E", "%", task_intervals),
                         use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("GPU utilization isn't available for this node — it either has no discrete/NVIDIA "
                "GPU, or (common on Apple Silicon) the OS only exposes real-time GPU load through "
                "a root-only API, so it can't be sampled from an ordinary process.")


render_analytics()
