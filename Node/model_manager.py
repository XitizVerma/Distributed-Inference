"""Backend-agnostic model control for the node.

Master issues install/uninstall/start/stop commands that aren't tied to any one
runtime — a model may be an Ollama LLM, a HuggingFace text-to-image model, or
something else. Each command carries a `backend`, and this module dispatches it
to the matching adapter. To add a new runtime, implement a BaseModelAdapter and
register it in ADAPTERS — nothing else (node.py / the dispatch path) changes.
"""

import ollama_client


class BaseModelAdapter:
    """Interface every backend adapter implements. `params` is the optional
    backend-specific hint blob carried on the model catalog entry."""

    def install(self, model_name: str, params=None) -> None:
        raise NotImplementedError

    def uninstall(self, model_name: str) -> None:
        raise NotImplementedError

    def start(self, model_name: str) -> None:
        """Preload into GPU/RAM so the model is warm for inference."""
        raise NotImplementedError

    def stop(self, model_name: str) -> None:
        """Evict from memory; the model stays installed on disk."""
        raise NotImplementedError

    def list_installed(self) -> list:
        """Models currently installed on disk for this backend."""
        raise NotImplementedError


class OllamaAdapter(BaseModelAdapter):
    def install(self, model_name: str, params=None) -> None:
        ollama_client.pull_model(model_name)

    def uninstall(self, model_name: str) -> None:
        ollama_client.delete_model(model_name)

    def start(self, model_name: str) -> None:
        ollama_client.load_model(model_name)

    def stop(self, model_name: str) -> None:
        ollama_client.unload_model(model_name)

    def list_installed(self) -> list:
        return ollama_client.list_local_models()


class HuggingFaceAdapter(BaseModelAdapter):
    """Stub for HuggingFace-hosted models (e.g. diffusers text-to-image). The
    dispatch path already routes here by backend; fill these in to enable it."""

    _MSG = "huggingface backend not implemented yet"

    def install(self, model_name: str, params=None) -> None:
        raise NotImplementedError(self._MSG)

    def uninstall(self, model_name: str) -> None:
        raise NotImplementedError(self._MSG)

    def start(self, model_name: str) -> None:
        raise NotImplementedError(self._MSG)

    def stop(self, model_name: str) -> None:
        raise NotImplementedError(self._MSG)

    def list_installed(self) -> list:
        return []


ADAPTERS = {
    "ollama": OllamaAdapter(),
    "huggingface": HuggingFaceAdapter(),
}


def _get_adapter(backend: str) -> BaseModelAdapter:
    adapter = ADAPTERS.get(backend)
    if adapter is None:
        raise ValueError(f"unknown model backend: {backend!r}")
    return adapter


def run_command(action: str, model_name: str, backend: str, params=None) -> None:
    """Execute one model command by dispatching to the backend's adapter.
    Raises on unknown backend/action or on any adapter failure — the caller
    turns that into a failed result reported to Master."""
    adapter = _get_adapter(backend)
    if action == "install":
        adapter.install(model_name, params)
    elif action == "uninstall":
        adapter.uninstall(model_name)
    elif action == "start":
        adapter.start(model_name)
    elif action == "stop":
        adapter.stop(model_name)
    else:
        raise ValueError(f"unknown model action: {action!r}")


def list_installed(backend: str) -> list:
    """Installed models for a backend — reported back to Master after a command
    so it can refresh the node's models_available. Best-effort: never raises."""
    try:
        return _get_adapter(backend).list_installed()
    except Exception:
        return None
