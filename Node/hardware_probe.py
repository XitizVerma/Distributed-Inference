import json
import platform
import shutil
import subprocess

import psutil

try:
    import GPUtil
except ImportError:
    GPUtil = None


def get_cpu():
    return {
        "processor": platform.processor(),
        "architecture": platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_frequency_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else None,
    }


def get_ram():
    ram = psutil.virtual_memory()

    return {
        "total_bytes": ram.total,
        "available_bytes": ram.available,
        "used_bytes": ram.used,
        "total_gb": round(ram.total / (1024 ** 3), 2),
    }


def get_storage():
    usage = shutil.disk_usage("/")

    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "total_gb": round(usage.total / (1024 ** 3), 2),
    }


def get_gpu():
    gpus = []

    if GPUtil:
        try:
            for gpu in GPUtil.getGPUs():
                gpus.append({
                    "id": gpu.id,
                    "name": gpu.name,
                    "driver": gpu.driver,
                    "memory_total_mb": gpu.memoryTotal,
                    "memory_free_mb": gpu.memoryFree,
                    "memory_used_mb": gpu.memoryUsed,
                })
        except Exception:
            pass

    # Apple Silicon fallback
    if not gpus and platform.system() == "Darwin":
        try:
            chip = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                text=True
            ).strip()

            gpus.append({
                "name": chip,
                "type": "Integrated GPU",
                "memory_total_mb": None
            })
        except Exception:
            pass

    return gpus


def get_live_metrics():
    """Point-in-time utilization snapshot sent on every heartbeat — the time
    series behind Master's per-node analytics charts.

    gpu_percent stays None on nodes with no way to report real GPU load
    without elevated privileges (e.g. Apple Silicon integrated GPUs have no
    public non-root API for this; GPUtil only reports real load for NVIDIA).
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()

    metrics = {
        "available_memory_mb": ram.available // (1024 * 1024),
        "cpu_percent": cpu_percent,
        "memory_percent": ram.percent,
        "memory_used_mb": ram.used // (1024 * 1024),
        "gpu_percent": None,
        "gpu_memory_used_mb": None,
    }

    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                metrics["gpu_percent"] = round(gpu.load * 100, 1)
                metrics["gpu_memory_used_mb"] = gpu.memoryUsed
        except Exception:
            pass

    return metrics


def get_network():
    interfaces = []

    stats = psutil.net_if_stats()

    for name, stat in stats.items():
        interfaces.append({
            "interface": name,
            "is_up": stat.isup,
            "speed_mbps": stat.speed
        })

    return interfaces


def detect_resources():
    return {
        "os": platform.platform(),
        "hostname": platform.node(),
        "cpu": get_cpu(),
        "ram": get_ram(),
        "storage": get_storage(),
        "gpu": get_gpu(),
        "network": get_network(),
    }


if __name__ == "__main__":
    resources = detect_resources()

    print(json.dumps(resources, indent=4))

    with open("resources.json", "w") as f:
        json.dump(resources, f, indent=4)

    print("\nExported to resources.json")