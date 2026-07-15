import threading
import time
from datetime import datetime

import requests

import client
import model_manager
from config import HOSTNAME, NODE_NAME, MASTER_URL, OLLAMA_URL, HEARTBEAT_INTERVAL_SECONDS
from hardware_probe import get_cpu, get_ram, get_gpu, get_live_metrics
from ollama_client import generate, list_local_models
from storage_client import download_input
from worker_classifier import classify_worker

WORKER_ID = None


def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{NODE_NAME}] {message}")


def print_banner():
    # Plain ASCII box-drawing — unicode box/em-dash characters render at
    # inconsistent widths across terminal fonts and would throw off alignment.
    lines = [
        "DISTRIBUTED INFERENCE - NODE",
        "",
        f"Node name     : {NODE_NAME}",
        f"Hostname      : {HOSTNAME}",
        f"Master URL    : {MASTER_URL}",
        f"Ollama URL    : {OLLAMA_URL}",
        f"Heartbeat     : every {HEARTBEAT_INTERVAL_SECONDS}s",
    ]
    width = max(len(line) for line in lines) + 4
    print("+" + "-" * width + "+")
    for line in lines:
        print("|  " + line.ljust(width - 2) + "|")
    print("+" + "-" * width + "+")


def get_system_info():
    cpu = get_cpu()
    ram = get_ram()
    gpus = get_gpu()
    return {
        "hostname": HOSTNAME,
        "node_name": NODE_NAME,
        "cpu_info": f"{cpu['processor'] or cpu['architecture']} "
                    f"({cpu['physical_cores']}c/{cpu['logical_cores']}t)",
        "total_memory_mb": ram["total_bytes"] // (1024 * 1024),
        "available_memory_mb": ram["available_bytes"] // (1024 * 1024),
        "gpu_info": ", ".join(g["name"] for g in gpus) if gpus else "none",
        "worker_type": classify_worker(cpu, ram, gpus),
        "models_available": list_local_models(),
    }


def register():
    global WORKER_ID
    data = client.register(get_system_info())
    WORKER_ID = data["worker_id"]
    status = "new registration" if data.get("is_new", True) else "already registered, reusing id"
    log(f"worker_id={WORKER_ID} ({status}) — this id is sent on every subsequent request")


def run_task(task):
    task_id = task["task_id"]
    log(f"[task_id={task_id}] accepted")
    client.accept_task(task_id, WORKER_ID)

    input_path = None
    if task.get("input_url"):
        try:
            input_path = download_input(task["input_url"])
        except Exception as exc:
            client.submit_result(task_id, WORKER_ID, success=False, error=f"input download failed: {exc}")
            log(f"[task_id={task_id}] failed to download input: {exc}")
            return

    try:
        # input_path is plumbed through for future image/video adapters that take a
        # reference file; the current text-only Ollama adapter doesn't consume it.
        result = generate(task["model_name"], task["prompt"])
        client.submit_result(task_id, WORKER_ID, result=result, success=True)
        log(f"[task_id={task_id}] completed")
    except Exception as exc:
        client.submit_result(task_id, WORKER_ID, success=False, error=str(exc))
        log(f"[task_id={task_id}] failed: {exc}")


def run_command(command):
    command_id = command["command_id"]
    action = command["action"]
    model_name = command["model_name"]
    backend = command["backend"]
    log(f"[command_id={command_id}] {action} {backend}:{model_name} — running")
    try:
        model_manager.run_command(action, model_name, backend, command.get("params"))
        client.submit_command_result(
            command_id, WORKER_ID, success=True,
            installed_models=model_manager.list_installed(backend),
        )
        log(f"[command_id={command_id}] {action} {backend}:{model_name} — succeeded")
    except Exception as exc:
        client.submit_command_result(
            command_id, WORKER_ID, success=False, error=str(exc),
            installed_models=model_manager.list_installed(backend),
        )
        log(f"[command_id={command_id}] {action} {backend}:{model_name} — failed: {exc}")


def heartbeat_loop():
    # Runs continuously; long-running inference is offloaded to a separate
    # thread (run_task) so heartbeats never stall while a task is in progress.
    while True:
        try:
            metrics = get_live_metrics()
            data = client.heartbeat(WORKER_ID, metrics)
            has_task = bool(data.get("pending_task"))
            gpu_str = f"{metrics['gpu_percent']}%" if metrics["gpu_percent"] is not None else "n/a"
            log(f"heartbeat ok — worker_id={WORKER_ID} cpu={metrics['cpu_percent']}% "
                f"mem={metrics['memory_percent']}% gpu={gpu_str} "
                f"available_memory_mb={metrics['available_memory_mb']} pending_task={has_task}")
            if has_task:
                threading.Thread(target=run_task, args=(data["pending_task"],), daemon=True).start()
            if data.get("pending_command"):
                threading.Thread(target=run_command, args=(data["pending_command"],), daemon=True).start()
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                log(f"heartbeat failed: worker_id={WORKER_ID} unknown to Master (likely a DB reset) "
                    f"— re-registering")
                try:
                    register()
                except requests.RequestException as register_exc:
                    log(f"re-registration failed: {register_exc}")
            else:
                log(f"heartbeat failed: {exc}")
        except requests.RequestException as exc:
            log(f"heartbeat failed: {exc}")

        time.sleep(HEARTBEAT_INTERVAL_SECONDS)


if __name__ == "__main__":
    print_banner()
    register()
    heartbeat_loop()
