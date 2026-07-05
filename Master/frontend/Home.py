import streamlit as st
import requests

from config import BACKEND_URL
from ui_helpers import inject_theme, render_task_sidebar

st.set_page_config(page_title="Distributed Inference — Task Input", page_icon="🔮", layout="wide")
inject_theme()
render_task_sidebar()

st.title("🔮 Distributed Inference")
st.caption("Submit a prompt below — it's routed to whichever node has capacity. "
           "Check **Tasks** for progress/results and **Connected Devices** for node status.")

st.divider()

FALLBACK_MODELS = ["llama3.1:8b", "llama3.1:70b", "mistral", "phi3", "gemma2"]


def fetch_known_models():
    """Union of models registered nodes report having pulled — so the dropdown
    only offers models that can actually be run right now."""
    try:
        resp = requests.get(f"{BACKEND_URL}/workers", timeout=5)
        resp.raise_for_status()
        workers = resp.json()
    except requests.RequestException:
        return []
    models = set()
    for w in workers:
        models.update(w.get("models_available") or [])
    return sorted(models)


known_models = fetch_known_models()
model_options = known_models or FALLBACK_MODELS

with st.form("submit_task", border=True, clear_on_submit=True):
    col_model, col_spacer = st.columns([1, 2])
    with col_model:
        model_choice = st.selectbox("Model", model_options)
        with st.expander("Use a different model"):
            custom_model = st.text_input("Custom model name", placeholder="e.g. llama3.1:70b")

    prompt = st.text_area("Prompt", height=180, placeholder="Ask something…")
    input_file = st.file_uploader(
        "Optional input file (image/pdf/etc.)",
        help="Uploaded to Google Drive; whichever node picks up the task downloads it from there.",
    )

    submitted = st.form_submit_button("🚀 Submit task", type="primary", use_container_width=True)

if submitted:
    model_name = custom_model.strip() or model_choice
    if not prompt.strip():
        st.warning("Enter a prompt first.")
    else:
        files = None
        if input_file is not None:
            files = {"input_file": (input_file.name, input_file.getvalue(), input_file.type)}
        with st.spinner("Submitting to Master…"):
            resp = requests.post(
                f"{BACKEND_URL}/infer",
                data={"prompt": prompt, "model_name": model_name},
                files=files,
            )
        if resp.ok:
            data = resp.json()
            st.success(f"✅ Task **#{data['task_id']}** submitted (model `{model_name}`) "
                       f"— status: `{data['status']}`")
        else:
            st.error(f"Failed to submit task: {resp.text}")
