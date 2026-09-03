from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.events import event_bus
from app.models.db_models import Alert
from app.schemas.schemas import AlertOut

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=List[AlertOut])
def list_alerts(db: Session = Depends(get_db)):
    return db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(200)).scalars().all()


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail={"error": "ALERT_NOT_FOUND", "message": "Alert not found."})
    alert.state = "ACKNOWLEDGED"
    db.commit()
    db.refresh(alert)
    event_bus.broadcast_sync("alert_updated", {"id": alert.id, "state": alert.state})
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail={"error": "ALERT_NOT_FOUND", "message": "Alert not found."})
    alert.state = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    event_bus.broadcast_sync("alert_updated", {"id": alert.id, "state": alert.state})
    return alert
