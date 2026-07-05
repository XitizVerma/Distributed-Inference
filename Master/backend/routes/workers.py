import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from db import get_db
from models import Worker, WorkerStatus, Task, TaskStatus, TaskWorkerMap, ActivityLog, EventType, WorkerMetric
from schemas import (
    RegisterRequest, RegisterResponse, HeartbeatRequest, HeartbeatResponse, PendingTask,
)

router = APIRouter()
logger = logging.getLogger("master")


@router.post("/register", response_model=RegisterResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.hostname == req.hostname).first()
    is_new = worker is None

    if worker:
        worker.node_name = req.node_name
        worker.ip = req.ip
        worker.gpu_info = req.gpu_info
        worker.cpu_info = req.cpu_info
        worker.total_memory_mb = req.total_memory_mb
        worker.available_memory_mb = req.available_memory_mb
        worker.worker_type = req.worker_type
        worker.models_available = req.models_available
        worker.status = WorkerStatus.online
    else:
        worker = Worker(
            hostname=req.hostname,
            node_name=req.node_name,
            ip=req.ip,
            gpu_info=req.gpu_info,
            cpu_info=req.cpu_info,
            total_memory_mb=req.total_memory_mb,
            available_memory_mb=req.available_memory_mb,
            worker_type=req.worker_type,
            models_available=req.models_available,
            status=WorkerStatus.online,
        )
        db.add(worker)

    db.flush()
    db.add(ActivityLog(worker_id=worker.id, event_type=EventType.connected))
    db.commit()
    db.refresh(worker)

    logger.info(
        f"[worker_id={worker.id}] {'registered' if is_new else 're-registered'} "
        f"node_name={worker.node_name!r} hostname={worker.hostname!r}"
    )
    return RegisterResponse(worker_id=worker.id, is_new=is_new)


@router.post("/heartbeat", response_model=HeartbeatResponse)
def heartbeat(req: HeartbeatRequest, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == req.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="worker not registered")

    logger.info(f"[worker_id={worker.id}] heartbeat node_name={worker.node_name!r}")

    worker.last_heartbeat_at = datetime.utcnow()
    if req.available_memory_mb is not None:
        worker.available_memory_mb = req.available_memory_mb
    if worker.status != WorkerStatus.busy:
        worker.status = WorkerStatus.online

    if any(v is not None for v in (req.cpu_percent, req.memory_percent, req.gpu_percent)):
        db.add(WorkerMetric(
            worker_id=worker.id,
            cpu_percent=req.cpu_percent,
            memory_percent=req.memory_percent,
            memory_used_mb=req.memory_used_mb,
            gpu_percent=req.gpu_percent,
            gpu_memory_used_mb=req.gpu_memory_used_mb,
        ))

    mapping = (
        db.query(TaskWorkerMap)
        .filter(TaskWorkerMap.worker_id == worker.id, TaskWorkerMap.status == "assigned")
        .order_by(TaskWorkerMap.assigned_at.asc())
        .first()
    )

    pending = None
    if mapping:
        task = db.query(Task).filter(Task.id == mapping.task_id).first()
        mapping.status = "sent"
        task.status = TaskStatus.running
        task.started_at = datetime.utcnow()
        pending = PendingTask(
            task_id=task.id, prompt=task.prompt, model_name=task.model_name, input_url=task.input_url,
        )

    db.commit()
    return HeartbeatResponse(ack=True, pending_task=pending)


def _worker_dict(w: Worker) -> dict:
    return {
        "id": w.id,
        "hostname": w.hostname,
        "node_name": w.node_name,
        "ip": w.ip,
        "gpu_info": w.gpu_info,
        "cpu_info": w.cpu_info,
        "total_memory_mb": w.total_memory_mb,
        "available_memory_mb": w.available_memory_mb,
        "worker_type": w.worker_type,
        "models_available": w.models_available,
        "status": w.status.value,
        "last_heartbeat_at": w.last_heartbeat_at,
    }


@router.get("/workers")
def list_workers(db: Session = Depends(get_db)):
    workers = db.query(Worker).order_by(Worker.id).all()
    return [_worker_dict(w) for w in workers]


@router.get("/workers/{worker_id}")
def get_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="worker not found")
    return _worker_dict(worker)


@router.get("/workers/{worker_id}/metrics")
def get_worker_metrics(worker_id: int, since_minutes: int = 60, db: Session = Depends(get_db)):
    """Time series behind the node analytics charts, plus the task intervals
    that overlapped this window — so the UI can shade "a task was running
    here" bands on top of the CPU/memory/GPU lines. There's no separate
    "task running" flag stored per metric row; it's derived here by joining
    task_worker_map/tasks, since duplicating that state onto every metric row
    would just be redundant, driftable storage.

    `since_minutes` is the lookback window (e.g. 15/60/360/1440 for
    15m/1h/6h/24h).
    """
    cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)

    metric_rows = (
        db.query(WorkerMetric)
        .filter(WorkerMetric.worker_id == worker_id, WorkerMetric.recorded_at >= cutoff)
        .order_by(WorkerMetric.recorded_at.asc())
        .all()
    )

    interval_rows = (
        db.query(Task.id, Task.model_name, Task.status, Task.started_at, Task.completed_at)
        .join(TaskWorkerMap, TaskWorkerMap.task_id == Task.id)
        .filter(
            TaskWorkerMap.worker_id == worker_id,
            Task.started_at.isnot(None),
            Task.started_at <= datetime.utcnow(),
            or_(Task.completed_at.is_(None), Task.completed_at >= cutoff),
        )
        .order_by(Task.started_at.asc())
        .all()
    )

    return {
        "metrics": [
            {
                "recorded_at": r.recorded_at,
                "cpu_percent": r.cpu_percent,
                "memory_percent": r.memory_percent,
                "memory_used_mb": r.memory_used_mb,
                "gpu_percent": r.gpu_percent,
                "gpu_memory_used_mb": r.gpu_memory_used_mb,
            }
            for r in metric_rows
        ],
        "task_intervals": [
            {
                "task_id": task_id,
                "model_name": model_name,
                "status": status.value,
                "started_at": started_at,
                "completed_at": completed_at,  # null means still running
            }
            for task_id, model_name, status, started_at, completed_at in interval_rows
        ],
    }


def mark_stale_workers_offline(db: Session, timeout_seconds: int):
    cutoff = datetime.utcnow() - timedelta(seconds=timeout_seconds)
    stale_workers = (
        db.query(Worker)
        .filter(Worker.status != WorkerStatus.offline, Worker.last_heartbeat_at < cutoff)
        .all()
    )
    for worker in stale_workers:
        worker.status = WorkerStatus.offline
        db.add(ActivityLog(worker_id=worker.id, event_type=EventType.disconnected))
    if stale_workers:
        db.commit()
