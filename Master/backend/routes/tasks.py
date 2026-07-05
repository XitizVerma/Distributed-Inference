import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from db import get_db
from models import Task, TaskStatus, TaskWorkerMap, Worker, WorkerStatus, ActivityLog, EventType
from schemas import InferResponse, TaskAcceptRequest, TaskResultRequest
from scheduler import assign_next_worker
from storage import get_storage

router = APIRouter()
logger = logging.getLogger("master")


def _worker_tag(db: Session, worker_id: int) -> str:
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    node_name = worker.node_name if worker else None
    return f"worker_id={worker_id} node_name={node_name!r}"


@router.post("/infer", response_model=InferResponse)
async def infer(
    prompt: str = Form(...),
    model_name: str = Form("llama3.1:8b"),
    input_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    task = Task(prompt=prompt, model_name=model_name, status=TaskStatus.queued)
    db.add(task)
    db.commit()
    db.refresh(task)

    if input_file is not None:
        contents = await input_file.read()
        storage = get_storage()
        filename = f"task_{task.id}_input_{input_file.filename}"
        task.input_url = storage.upload(contents, filename, input_file.content_type or "application/octet-stream")
        db.commit()

    assign_next_worker(db, task)
    db.refresh(task)
    return InferResponse(task_id=task.id, status=task.status.value)


@router.get("/tasks")
def list_tasks(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Task)
    if status:
        q = q.filter(Task.status == status)
    tasks = q.order_by(Task.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "prompt": t.prompt,
            "model_name": t.model_name,
            "status": t.status.value,
            "input_url": t.input_url,
            "result": t.result,
            "result_url": t.result_url,
            "result_mimetype": t.result_mimetype,
            "created_at": t.created_at,
            "completed_at": t.completed_at,
        }
        for t in tasks
    ]


@router.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return {
        "id": task.id,
        "prompt": task.prompt,
        "model_name": task.model_name,
        "status": task.status.value,
        "input_url": task.input_url,
        "result": task.result,
        "result_url": task.result_url,
        "result_mimetype": task.result_mimetype,
    }


@router.post("/tasks/{task_id}/accept")
def accept_task(task_id: int, req: TaskAcceptRequest, db: Session = Depends(get_db)):
    logger.info(f"[task_id={task_id}] accepted by {_worker_tag(db, req.worker_id)}")
    db.add(ActivityLog(worker_id=req.worker_id, task_id=task_id, event_type=EventType.inference_accepted))
    db.commit()
    return {"ack": True}


def _finalize_common(db: Session, task: Task, worker_id: int):
    mapping = (
        db.query(TaskWorkerMap)
        .filter(TaskWorkerMap.task_id == task.id, TaskWorkerMap.worker_id == worker_id)
        .first()
    )
    if mapping:
        mapping.status = "done"

    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if worker and worker.status == WorkerStatus.busy:
        worker.status = WorkerStatus.online

    db.add(ActivityLog(worker_id=worker_id, task_id=task.id, event_type=EventType.inference_completed))


@router.post("/tasks/{task_id}/result")
def submit_result(task_id: int, req: TaskResultRequest, db: Session = Depends(get_db)):
    """Text-only result path — for small outputs like LLM completions."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task not found")

    if task.status in (TaskStatus.completed, TaskStatus.failed):
        # Task was already reclaimed and finished by another worker after this
        # one's heartbeat timed out — ignore the late result, don't overwrite.
        logger.info(f"[task_id={task_id}] late result from {_worker_tag(db, req.worker_id)} ignored")
        return {"ack": True, "note": "task already finalized, late result ignored"}

    task.result = req.result if req.success else (req.error or "unknown error")
    task.status = TaskStatus.completed if req.success else TaskStatus.failed
    task.completed_at = datetime.utcnow()

    logger.info(
        f"[task_id={task_id}] result ({'success' if req.success else 'failed'}) "
        f"from {_worker_tag(db, req.worker_id)}"
    )
    _finalize_common(db, task, req.worker_id)
    db.commit()
    return {"ack": True}


@router.post("/tasks/{task_id}/result/file")
async def submit_result_file(
    task_id: int,
    worker_id: int = Form(...),
    success: bool = Form(True),
    error: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Blob result path — for image/video/pdf outputs, uploaded to object storage."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="task not found")

    if task.status in (TaskStatus.completed, TaskStatus.failed):
        logger.info(f"[task_id={task_id}] late file result from {_worker_tag(db, worker_id)} ignored")
        return {"ack": True, "note": "task already finalized, late result ignored"}

    if success and file is not None:
        contents = await file.read()
        storage = get_storage()
        filename = f"task_{task_id}_result_{file.filename}"
        task.result_url = storage.upload(contents, filename, file.content_type or "application/octet-stream")
        task.result_mimetype = file.content_type
        task.status = TaskStatus.completed
    else:
        task.result = error or "unknown error"
        task.status = TaskStatus.failed

    task.completed_at = datetime.utcnow()

    logger.info(
        f"[task_id={task_id}] file result ({'success' if success else 'failed'}) "
        f"from {_worker_tag(db, worker_id)}"
    )
    _finalize_common(db, task, worker_id)
    db.commit()
    return {"ack": True, "result_url": task.result_url}
