"""Helper for writing structured audit log entries (Section 31)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.events import event_bus
from app.models.db_models import AuditLog


def record_event(
    db: Session,
    event_type: str,
    description: str,
    status: str = "INFO",
    model_version: Optional[str] = None,
    dataset_version: Optional[str] = None,
    broadcast: bool = True,
) -> AuditLog:
    entry = AuditLog(
        event_type=event_type,
        description=description,
        status=status,
        model_version=model_version,
        dataset_version=dataset_version,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    if broadcast:
        event_bus.broadcast_sync(
            "audit_event",
            {
                "id": entry.id,
                "event_type": entry.event_type,
                "description": entry.description,
                "status": entry.status,
                "model_version": entry.model_version,
                "dataset_version": entry.dataset_version,
                "timestamp": entry.timestamp.isoformat(),
            },
        )
    return entry
