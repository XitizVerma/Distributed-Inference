from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models import Worker, WorkerStatus, Task, TaskStatus, TaskWorkerMap, ActivityLog, EventType, WorkerMetric


def assign_next_worker(db: Session, task: Task):
    """Pick the idle, online worker with the most available memory (simple load balancing)."""
    worker = (
        db.query(Worker)
        .filter(Worker.status == WorkerStatus.online)
        .order_by(Worker.available_memory_mb.desc())
        .first()
    )
    if not worker:
        return None

    mapping = TaskWorkerMap(task_id=task.id, worker_id=worker.id, status="assigned")
    task.status = TaskStatus.assigned
    worker.status = WorkerStatus.busy

    db.add(mapping)
    db.add(ActivityLog(worker_id=worker.id, task_id=task.id, event_type=EventType.task_created))
    db.commit()
    return worker


def reclaim_orphaned_tasks(db: Session):
    """Requeue tasks that were in-flight on a worker that just went offline.

    Called from the same periodic watcher that marks stale workers offline, right
    after it does so — a task held by a worker with no recent heartbeat is assumed
    lost and handed to another online worker instead of waiting forever.
    """
    orphaned_mappings = (
        db.query(TaskWorkerMap)
        .join(Worker, TaskWorkerMap.worker_id == Worker.id)
        .filter(TaskWorkerMap.status.in_(["assigned", "sent"]), Worker.status == WorkerStatus.offline)
        .all()
    )

    to_reassign = []
    for mapping in orphaned_mappings:
        mapping.status = "failed"
        task = db.query(Task).filter(Task.id == mapping.task_id).first()
        if not task or task.status in (TaskStatus.completed, TaskStatus.failed):
            continue
        task.status = TaskStatus.queued
        task.started_at = None
        db.add(ActivityLog(
            worker_id=mapping.worker_id,
            task_id=task.id,
            event_type=EventType.task_requeued,
            details={"reason": "worker heartbeat timeout"},
        ))
        to_reassign.append(task)
    db.commit()

    for task in to_reassign:
        assign_next_worker(db, task)


def assign_pending_tasks(db: Session):
    """Retries assignment for tasks still stuck in `queued` — e.g. because no
    worker was online when /infer created them. Runs on every watcher tick so
    a queued task gets picked up as soon as a worker becomes available,
    instead of sitting queued forever.
    """
    pending_tasks = db.query(Task).filter(Task.status == TaskStatus.queued).all()
    for task in pending_tasks:
        assign_next_worker(db, task)


def prune_old_metrics(db: Session, retention_hours: int):
    """Bounds worker_metrics growth — with a 1s heartbeat interval this table
    grows fast, so anything older than the retention window is dropped."""
    cutoff = datetime.utcnow() - timedelta(hours=retention_hours)
    db.query(WorkerMetric).filter(WorkerMetric.recorded_at < cutoff).delete()
    db.commit()
