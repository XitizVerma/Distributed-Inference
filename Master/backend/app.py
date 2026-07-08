import logging
import threading
import time

from fastapi import FastAPI, Request

from db import Base, engine, SessionLocal
from routes import workers, tasks, health, activity, models
from routes.workers import mark_stale_workers_offline
from scheduler import reclaim_orphaned_tasks, assign_pending_tasks, prune_old_metrics
from config import HEARTBEAT_TIMEOUT_SECONDS, METRICS_RETENTION_HOURS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("master")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Master")
app.include_router(health.router)
app.include_router(workers.router)
app.include_router(tasks.router)
app.include_router(activity.router)
app.include_router(models.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        f"{client_host} {request.method} {request.url.path} "
        f"-> {response.status_code} ({duration_ms:.1f}ms)"
    )
    return response


def _stale_worker_watcher():
    tick_seconds = HEARTBEAT_TIMEOUT_SECONDS / 2
    ticks_per_prune = max(1, int(60 / tick_seconds))  # prune roughly once a minute, not every tick
    tick_count = 0
    while True:
        db = SessionLocal()
        try:
            mark_stale_workers_offline(db, HEARTBEAT_TIMEOUT_SECONDS)
            reclaim_orphaned_tasks(db)
            assign_pending_tasks(db)
            tick_count += 1
            if tick_count % ticks_per_prune == 0:
                prune_old_metrics(db, METRICS_RETENTION_HOURS)
        finally:
            db.close()
        time.sleep(tick_seconds)


@app.on_event("startup")
def start_background_tasks():
    thread = threading.Thread(target=_stale_worker_watcher, daemon=True)
    thread.start()
