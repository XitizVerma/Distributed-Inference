import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db import get_db
from models import (
    Model, ModelCommand, ModelAction, ModelCommandStatus,
    Worker, ActivityLog, EventType,
)
from schemas import CreateModelRequest, CreateCommandRequest, CommandResultRequest

router = APIRouter()
logger = logging.getLogger("master")


def _model_dict(m: Model) -> dict:
    return {
        "id": m.id,
        "name": m.name,
        "backend": m.backend,
        "task_type": m.task_type,
        "params": m.params,
        "created_at": m.created_at,
    }


def _command_dict(c: ModelCommand) -> dict:
    return {
        "id": c.id,
        "model_id": c.model_id,
        "worker_id": c.worker_id,
        "action": c.action.value,
        "status": c.status.value,
        "error": c.error,
        "created_at": c.created_at,
        "sent_at": c.sent_at,
        "completed_at": c.completed_at,
    }


# --- catalog ---------------------------------------------------------------

@router.post("/models")
def create_model(req: CreateModelRequest, db: Session = Depends(get_db)):
    model = Model(
        name=req.name,
        backend=req.backend,
        task_type=req.task_type,
        params=req.params,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    logger.info(f"[model_id={model.id}] added to catalog name={model.name!r} backend={model.backend!r}")
    return _model_dict(model)


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    models = db.query(Model).order_by(Model.id).all()
    return [_model_dict(m) for m in models]


@router.delete("/models/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="model not found")
    db.delete(model)
    db.commit()
    return {"ack": True}


# --- commands --------------------------------------------------------------

@router.post("/models/{model_id}/commands")
def create_command(model_id: int, req: CreateCommandRequest, db: Session = Depends(get_db)):
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="model not found")

    worker = db.query(Worker).filter(Worker.id == req.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="worker not found")

    try:
        action = ModelAction(req.action)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid action: {req.action}")

    command = ModelCommand(
        model_id=model_id,
        worker_id=req.worker_id,
        action=action,
        status=ModelCommandStatus.queued,
    )
    db.add(command)
    db.flush()
    db.add(ActivityLog(
        worker_id=req.worker_id,
        event_type=EventType.model_command_created,
        details={"command_id": command.id, "model": model.name, "action": action.value},
    ))
    db.commit()
    db.refresh(command)

    logger.info(
        f"[model_command_id={command.id}] queued action={action.value} "
        f"model={model.name!r} for worker_id={req.worker_id}"
    )
    return _command_dict(command)


@router.get("/models/commands")
def list_commands(
    worker_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(ModelCommand)
    if worker_id is not None:
        q = q.filter(ModelCommand.worker_id == worker_id)
    if status:
        q = q.filter(ModelCommand.status == status)
    commands = q.order_by(ModelCommand.created_at.desc()).limit(limit).all()
    return [_command_dict(c) for c in commands]


@router.post("/models/commands/{command_id}/result")
def submit_command_result(command_id: int, req: CommandResultRequest, db: Session = Depends(get_db)):
    command = db.query(ModelCommand).filter(ModelCommand.id == command_id).first()
    if not command:
        raise HTTPException(status_code=404, detail="command not found")

    command.status = ModelCommandStatus.succeeded if req.success else ModelCommandStatus.failed
    command.error = None if req.success else (req.error or "unknown error")
    command.completed_at = datetime.utcnow()

    # Close the loop: refresh the node's installed-model list so the UI reflects
    # the install/uninstall without waiting for the node to re-register.
    if req.installed_models is not None:
        worker = db.query(Worker).filter(Worker.id == req.worker_id).first()
        if worker:
            worker.models_available = req.installed_models

    db.add(ActivityLog(
        worker_id=req.worker_id,
        event_type=EventType.model_command_completed,
        details={"command_id": command.id, "action": command.action.value, "success": req.success},
    ))
    db.commit()

    logger.info(
        f"[model_command_id={command.id}] result "
        f"({'success' if req.success else 'failed'}) from worker_id={req.worker_id}"
    )
    return {"ack": True}
