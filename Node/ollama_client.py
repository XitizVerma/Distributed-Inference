import requests

from config import OLLAMA_URL, OLLAMA_KEEP_ALIVE


def generate(model_name: str, prompt: str) -> str:
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            # Ollama auto-loads the model on this request if it isn't already
            # resident; keep_alive controls how long it stays loaded afterward.
            # "0" evicts it right after responding, so idle nodes aren't holding
            # multi-GB models in memory between tasks.
            "keep_alive": OLLAMA_KEEP_ALIVE,
        },
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def list_local_models():
    resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
    resp.raise_for_status()
    return [m["name"] for m in resp.json().get("models", [])]


def pull_model(model_name: str) -> None:
    """Download/install a model onto this node (`ollama pull`). stream=false so
    the call blocks until the pull finishes; the pull of a multi-GB model can
    take a while, hence the long timeout."""
    resp = requests.post(
        f"{OLLAMA_URL}/api/pull",
        json={"model": model_name, "stream": False},
        timeout=3600,
    )
    resp.raise_for_status()
    status = resp.json().get("status")
    if status and status != "success":
        raise RuntimeError(f"pull did not succeed: {status}")


def delete_model(model_name: str) -> None:
    """Remove a model from disk (`ollama rm`)."""
    resp = requests.delete(
        f"{OLLAMA_URL}/api/delete",
        json={"model": model_name},
        timeout=60,
    )
    resp.raise_for_status()


def _set_keep_alive(model_name: str, keep_alive) -> None:
    """Load or evict a model by issuing an empty /api/generate with a keep_alive:
    a positive duration loads it into memory and holds it; "0" (or 0) unloads it
    immediately. No prompt means Ollama just (un)loads the weights, no inference."""
    resp = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": model_name, "keep_alive": keep_alive},
        timeout=600,
    )
    resp.raise_for_status()


def load_model(model_name: str) -> None:
    """Preload into GPU/RAM so it's warm for inference (start)."""
    _set_keep_alive(model_name, "5m")


def unload_model(model_name: str) -> None:
    """Evict from memory; the model stays installed on disk (stop)."""
    _set_keep_alive(model_name, 0)
