"""Classifies this machine's hardware into a coarse worker type for scheduling.

Kept separate from hardware_probe.py: that module only reports raw specs,
this module turns those specs into a label the scheduler can reason about.
"""


def classify_worker(cpu: dict, ram: dict, gpus: list) -> str:
    has_dedicated_gpu = any(
        g.get("memory_total_mb") not in (None, 0) for g in gpus
    )
    if has_dedicated_gpu:
        return "gpu"

    if any(g.get("type") == "Integrated GPU" for g in gpus):
        return "apple_silicon"

    if ram.get("total_gb", 0) >= 32 and cpu.get("logical_cores", 0) >= 8:
        return "cpu_high"

    return "cpu_standard"
