from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import AuditLog
from app.registry.registry_service import get_champion

router = APIRouter(tags=["health"])

_STARTED_AT = datetime.now(timezone.utc)


@router.get("/health")
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    champion = get_champion(db)
    last_event = db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc())).scalars().first()

    return {
        "status": "ok" if db_ok else "degraded",
        "uptime_seconds": round((datetime.now(timezone.utc) - _STARTED_AT).total_seconds()),
        "dependencies": {
            "database": "ok" if db_ok else "unreachable",
        },
        "active_model": champion.version if champion else None,
        "last_event": {
            "type": last_event.event_type,
            "timestamp": last_event.timestamp.isoformat(),
        }
        if last_event
        else None,
    }
