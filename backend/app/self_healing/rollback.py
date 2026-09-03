"""Automated rollback (Section 27)."""
from __future__ import annotations

from app.core.config import settings
from app.deployment.predictor import clear_model_cache
from app.registry.registry_service import rollback_to_previous
from app.self_healing.engine import create_alert
from sqlalchemy.orm import Session


def maybe_rollback(db: Session, health_score: int, error_rate: float, reason_hint: str = "") -> dict | None:
    """Check rollback conditions (Section 27) and roll back if unhealthy."""
    should_rollback = (
        health_score < settings.ROLLBACK_MIN_HEALTH_SCORE or error_rate > settings.ROLLBACK_MAX_ERROR_RATE
    )
    if not should_rollback:
        return None

    restored = rollback_to_previous(db)
    clear_model_cache()

    if restored is None:
        create_alert(
            db,
            "CRITICAL",
            "Rollback unavailable",
            "Deployment is unhealthy but no previous champion is available to roll back to.",
            "self_healing",
        )
        return None

    create_alert(
        db,
        "RESOLVED",
        "Automatic rollback completed",
        f"Rolled back to {restored.version} after health degraded "
        f"(score={health_score}, error_rate={error_rate:.2%}). {reason_hint}",
        "self_healing",
    )
    return {"restored_version": restored.version, "health_score": health_score}
