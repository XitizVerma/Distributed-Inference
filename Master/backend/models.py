import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum, JSON, Float,
)

from db import Base

# Every DateTime column below defaults via Python's datetime.utcnow rather than
# MySQL's server-side NOW() (which was the previous approach, using
# server_default=func.now()). MySQL's NOW() runs in the server's LOCAL time
# zone, while every cutoff comparison elsewhere in this app (heartbeat
# staleness, metrics time-range filters, task-interval windows) uses Python's
# datetime.utcnow(). On a server whose local time isn't UTC, that mismatch
# silently broke time-window filtering — e.g. the node analytics time-range
# filter looked like it "didn't work" because every row's timestamp was
# offset by the server's UTC difference, making short windows (15m/1h/6h)
# unable to exclude anything. Python-side defaults keep every timestamp in
# this schema on the same clock as the code that filters by it.


class WorkerStatus(str, enum.Enum):
    online = "online"
    busy = "busy"
    offline = "offline"


class TaskStatus(str, enum.Enum):
    queued = "queued"
    assigned = "assigned"
    running = "running"
    completed = "completed"
    failed = "failed"


class EventType(str, enum.Enum):
    connected = "connected"
    disconnected = "disconnected"
    inference_accepted = "inference_accepted"
    inference_completed = "inference_completed"
    task_created = "task_created"
    task_requeued = "task_requeued"


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), nullable=False, unique=True)
    node_name = Column(String(128))
    ip = Column(String(64))
    gpu_info = Column(String(255))
    cpu_info = Column(String(255))
    total_memory_mb = Column(Integer)
    available_memory_mb = Column(Integer)
    worker_type = Column(String(32))
    models_available = Column(JSON)
    status = Column(Enum(WorkerStatus), default=WorkerStatus.online)
    last_heartbeat_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    registered_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    prompt = Column(Text, nullable=False)
    model_name = Column(String(128), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.queued)
    input_url = Column(String(512))  # blob the worker should download and use as input, if any
    result = Column(Text)  # inline result, for small text outputs
    result_url = Column(String(512))  # blob result (image/video/pdf), if any
    result_mimetype = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class TaskWorkerMap(Base):
    __tablename__ = "task_worker_map"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, nullable=False)
    worker_id = Column(Integer, nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="assigned")  # assigned -> sent -> done


class WorkerMetric(Base):
    """One row per heartbeat that carried live utilization data — the time
    series behind the per-node analytics charts."""
    __tablename__ = "worker_metrics"

    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    cpu_percent = Column(Float)
    memory_percent = Column(Float)
    memory_used_mb = Column(Integer)
    gpu_percent = Column(Float)  # null when the node has no way to report GPU load (e.g. Apple Silicon)
    gpu_memory_used_mb = Column(Integer)


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, nullable=True)
    task_id = Column(Integer, nullable=True)
    event_type = Column(Enum(EventType), nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
