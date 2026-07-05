from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db import get_db
from models import ActivityLog

router = APIRouter()


@router.get("/activity")
def list_activity(
    worker_id: Optional[int] = None,
    since_minutes: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(ActivityLog)
    if worker_id is not None:
        q = q.filter(ActivityLog.worker_id == worker_id)
    if since_minutes is not None:
        cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)
        q = q.filter(ActivityLog.created_at >= cutoff)

    logs = q.order_by(ActivityLog.created_at.desc()).limit(200).all()
    return [
        {
            "id": l.id,
            "worker_id": l.worker_id,
            "task_id": l.task_id,
            "event_type": l.event_type.value,
            "details": l.details,
            "created_at": l.created_at,
        }
        for l in logs
    ]
