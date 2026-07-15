"""All HTTP calls this node makes to Master.

Kept as the single place that knows Master's API shape — node.py should call
these functions rather than hitting MASTER_URL directly, so the API contract
only needs to be updated in one place if Master's routes change.
"""

import requests

from config import MASTER_URL


def register(info: dict) -> dict:
    resp = requests.post(f"{MASTER_URL}/register", json=info, timeout=10)
    resp.raise_for_status()
    return resp.json()


def heartbeat(worker_id: int, metrics: dict) -> dict:
    resp = requests.post(
        f"{MASTER_URL}/heartbeat",
        json={"worker_id": worker_id, **metrics},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def accept_task(task_id: int, worker_id: int) -> None:
    requests.post(f"{MASTER_URL}/tasks/{task_id}/accept", json={"worker_id": worker_id}, timeout=10)


def submit_result(task_id: int, worker_id: int, result: str = None, success: bool = True, error: str = None) -> None:
    requests.post(
        f"{MASTER_URL}/tasks/{task_id}/result",
        json={"worker_id": worker_id, "result": result, "success": success, "error": error},
        timeout=600 if success else 30,
    )


def submit_command_result(
    command_id: int,
    worker_id: int,
    success: bool = True,
    error: str = None,
    installed_models=None,
) -> None:
    """Report the outcome of a model command back to Master. installed_models is
    the node's fresh installed-model list for that backend, so Master can refresh
    the worker's models_available after an install/uninstall."""
    requests.post(
        f"{MASTER_URL}/models/commands/{command_id}/result",
        json={
            "worker_id": worker_id,
            "success": success,
            "error": error,
            "installed_models": installed_models,
        },
        timeout=30,
    )


def submit_result_file(
    task_id: int,
    worker_id: int,
    file_path: str,
    content_type: str,
    success: bool = True,
    error: str = None,
) -> dict:
    """For blob results (image/video/pdf) — not yet used until an image/video
    adapter exists, but mirrors Master's POST /tasks/{id}/result/file."""
    data = {"worker_id": worker_id, "success": success, "error": error or ""}
    files = None
    if success:
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f.read(), content_type)}
    resp = requests.post(f"{MASTER_URL}/tasks/{task_id}/result/file", data=data, files=files, timeout=600)
    resp.raise_for_status()
    return resp.json()
