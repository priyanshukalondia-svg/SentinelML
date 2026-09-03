"""
Model registry: champion/challenger lifecycle & promotion rules
(Sections 15-18).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core.config import settings
from app.core.events import event_bus
from app.models.db_models import ModelVersion


def get_champion(db: Session, model_name: str = "fraud-detector") -> Optional[ModelVersion]:
    return db.execute(
        select(ModelVersion).where(
            ModelVersion.model_name == model_name, ModelVersion.state == "CHAMPION"
        )
    ).scalars().first()


def list_models(db: Session, model_name: str = "fraud-detector") -> list[ModelVersion]:
    return db.execute(
        select(ModelVersion)
        .where(ModelVersion.model_name == model_name)
        .order_by(ModelVersion.created_at.desc())
    ).scalars().all()


def evaluate_promotion(champion: Optional[ModelVersion], challenger: ModelVersion) -> dict:
    """Apply the configured promotion rule (Section 18)."""
    metric = settings.PROMOTION_METRIC
    challenger_metric = challenger.metrics.get(metric, 0.0)

    if champion is None:
        return {
            "approved": True,
            "reason": "No existing champion — challenger is promoted automatically as the first model.",
            "champion_metric": None,
            "challenger_metric": challenger_metric,
        }

    champion_metric = champion.metrics.get(metric, 0.0)
    min_improvement = settings.PROMOTION_MIN_IMPROVEMENT
    required = champion_metric + min_improvement

    latency_ok = True
    champion_latency = champion.metrics.get("inference_latency")
    challenger_latency = challenger.metrics.get("inference_latency")
    if champion_latency and challenger_latency:
        increase_pct = (challenger_latency - champion_latency) / champion_latency * 100
        latency_ok = increase_pct <= settings.PROMOTION_MAX_LATENCY_INCREASE_PCT

    metric_ok = challenger_metric >= required
    approved = metric_ok and latency_ok

    reasons = []
    reasons.append(
        f"challenger {metric}={challenger_metric:.4f} vs required >= {required:.4f} "
        f"(champion {champion_metric:.4f} + min_improvement {min_improvement}): "
        f"{'PASS' if metric_ok else 'FAIL'}"
    )
    if champion_latency and challenger_latency:
        reasons.append(
            f"latency increase {increase_pct:.1f}% vs max {settings.PROMOTION_MAX_LATENCY_INCREASE_PCT}%: "
            f"{'PASS' if latency_ok else 'FAIL'}"
        )

    return {
        "approved": approved,
        "reason": "; ".join(reasons),
        "champion_metric": champion_metric,
        "challenger_metric": challenger_metric,
    }


def promote_model(db: Session, challenger: ModelVersion) -> ModelVersion:
    current_champion = get_champion(db, challenger.model_name)
    if current_champion:
        current_champion.state = "ARCHIVED"
        current_champion.deployment_status = "NOT_DEPLOYED"
        db.add(current_champion)

    challenger.state = "CHAMPION"
    challenger.deployment_status = "DEPLOYED"
    db.add(challenger)
    db.commit()
    db.refresh(challenger)

    record_event(
        db,
        event_type="MODEL_PROMOTED",
        description=f"{challenger.version} promoted to CHAMPION and deployed.",
        status="SUCCESS",
        model_version=challenger.version,
        dataset_version=challenger.dataset_version,
    )
    record_event(
        db,
        event_type="MODEL_DEPLOYED",
        description=f"{challenger.version} deployed to production.",
        status="SUCCESS",
        model_version=challenger.version,
    )
    event_bus.broadcast_sync("model_promoted", {"version": challenger.version, "metrics": challenger.metrics})
    return challenger


def reject_model(db: Session, challenger: ModelVersion, reason: str) -> ModelVersion:
    challenger.state = "REJECTED"
    db.add(challenger)
    db.commit()
    db.refresh(challenger)

    record_event(
        db,
        event_type="MODEL_REJECTED",
        description=f"{challenger.version} rejected: {reason}",
        status="INFO",
        model_version=challenger.version,
    )
    event_bus.broadcast_sync("model_rejected", {"version": challenger.version, "reason": reason})
    return challenger


def rollback_to_previous(db: Session, model_name: str = "fraud-detector") -> Optional[ModelVersion]:
    """Restore the most recently archived (previously-healthy) champion."""
    current = get_champion(db, model_name)
    previous = db.execute(
        select(ModelVersion)
        .where(ModelVersion.model_name == model_name, ModelVersion.state == "ARCHIVED")
        .order_by(ModelVersion.created_at.desc())
    ).scalars().first()

    if previous is None:
        return None

    if current:
        current.state = "REJECTED"
        current.deployment_status = "NOT_DEPLOYED"
        db.add(current)

    previous.state = "CHAMPION"
    previous.deployment_status = "DEPLOYED"
    db.add(previous)
    db.commit()
    db.refresh(previous)

    record_event(
        db,
        event_type="ROLLBACK_COMPLETED",
        description=f"Rolled back to {previous.version} after {current.version if current else 'unknown'} became unhealthy.",
        status="SUCCESS",
        model_version=previous.version,
    )
    event_bus.broadcast_sync("rollback_completed", {"restored_version": previous.version})
    return previous
