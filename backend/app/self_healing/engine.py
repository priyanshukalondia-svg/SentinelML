"""
Self-Healing Engine (Section 26).

Coordinates: Detection -> Diagnosis -> Retraining -> Evaluation ->
Promotion -> Deployment, and maintains a persisted, observable state for
each recovery workflow so the dashboard's Recovery page (Section 34.8)
can render live progress.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core.config import settings
from app.core.events import event_bus
from app.models.db_models import Alert, Dataset, ModelVersion, RecoveryWorkflow
from app.registry.registry_service import evaluate_promotion, get_champion, promote_model, reject_model
from app.training.trainer import train_models

_last_retrain_trigger_time: dict[str, float] = {}


def _cooldown_active(trigger: str) -> bool:
    last = _last_retrain_trigger_time.get(trigger)
    if last is None:
        return False
    return (time.time() - last) < settings.RETRAINING_COOLDOWN_SECONDS


def _append_log(workflow: RecoveryWorkflow, step: str, message: str) -> None:
    entries = list(workflow.log or [])
    entries.append({"step": step, "message": message, "timestamp": datetime.now(timezone.utc).isoformat()})
    workflow.log = entries


def _broadcast_workflow(workflow: RecoveryWorkflow) -> None:
    event_bus.broadcast_sync(
        "recovery_update",
        {
            "id": workflow.id,
            "status": workflow.status,
            "trigger": workflow.trigger,
            "champion_version": workflow.champion_version,
            "challenger_version": workflow.challenger_version,
            "outcome": workflow.outcome,
            "log": workflow.log,
        },
    )


def create_alert(db: Session, severity: str, title: str, description: str, source: str = "monitoring") -> Alert:
    alert = Alert(severity=severity, title=title, description=description, source=source, state="OPEN")
    db.add(alert)
    db.commit()
    db.refresh(alert)
    event_bus.broadcast_sync(
        "alert",
        {
            "id": alert.id,
            "severity": alert.severity,
            "title": alert.title,
            "description": alert.description,
            "state": alert.state,
        },
    )
    return alert


def trigger_self_healing(
    db: Session, trigger: str, dataset: Dataset, model_types: Optional[list[str]] = None
) -> RecoveryWorkflow:
    """Entry point invoked by monitoring checks or the failure-simulation endpoints."""
    if _cooldown_active(trigger):
        raise RuntimeError(
            f"Retraining for trigger '{trigger}' is in cooldown "
            f"({settings.RETRAINING_COOLDOWN_SECONDS}s) — suppressing duplicate trigger."
        )
    _last_retrain_trigger_time[trigger] = time.time()

    champion = get_champion(db)
    workflow = RecoveryWorkflow(
        trigger=trigger,
        status="DETECTED",
        champion_version=champion.version if champion else "",
        champion_metric=champion.metrics.get(settings.PROMOTION_METRIC) if champion else None,
        log=[],
    )
    _append_log(workflow, "DETECTED", f"Trigger: {trigger}")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    _broadcast_workflow(workflow)

    record_event(db, "RETRAINING_TRIGGERED", f"Self-healing workflow #{workflow.id} triggered by: {trigger}", "WARNING")

    # --- Diagnosis ---
    workflow.status = "DIAGNOSING"
    _append_log(workflow, "DIAGNOSING", "Confirmed condition warrants retraining.")
    db.commit()
    _broadcast_workflow(workflow)

    # --- Retraining ---
    workflow.status = "RETRAINING"
    _append_log(workflow, "RETRAINING", "Training challenger model(s).")
    db.commit()
    _broadcast_workflow(workflow)

    types = model_types or [champion.training_run.model_type] if champion and champion.training_run else ["xgboost"]
    runs = train_models(db, dataset, types, triggered_by="self_healing")
    successful = [r for r in runs if r.status == "COMPLETED" and r.model_version]

    if not successful:
        workflow.status = "FAILED"
        workflow.outcome = "TRAINING_FAILED"
        _append_log(workflow, "FAILED", "All challenger training attempts failed.")
        workflow.completed_at = datetime.now(timezone.utc)
        db.commit()
        _broadcast_workflow(workflow)
        create_alert(db, "CRITICAL", "Self-healing failed", "Challenger training failed during recovery.", "self_healing")
        return workflow

    best_run = max(successful, key=lambda r: r.metrics.get(settings.PROMOTION_METRIC, 0.0))
    challenger: ModelVersion = db.execute(
        select(ModelVersion).where(ModelVersion.training_run_id == best_run.id)
    ).scalars().first()

    workflow.challenger_version = challenger.version
    workflow.challenger_metric = challenger.metrics.get(settings.PROMOTION_METRIC)
    workflow.status = "EVALUATING"
    _append_log(
        workflow,
        "EVALUATING",
        f"Comparing challenger {challenger.version} against champion {champion.version if champion else 'none'}.",
    )
    db.commit()
    _broadcast_workflow(workflow)

    # --- Evaluation / Promotion ---
    decision = evaluate_promotion(champion, challenger)
    if decision["approved"]:
        promote_model(db, challenger)
        workflow.status = "COMPLETED"
        workflow.outcome = "PROMOTED"
        _append_log(workflow, "PROMOTED", decision["reason"])
        _append_log(workflow, "DEPLOYED", f"{challenger.version} deployed to production.")
        create_alert(
            db,
            "RESOLVED",
            "Self-healing completed",
            f"Challenger {challenger.version} promoted and deployed.",
            "self_healing",
        )
    else:
        reject_model(db, challenger, decision["reason"])
        workflow.status = "COMPLETED"
        workflow.outcome = "REJECTED"
        _append_log(workflow, "REJECTED", decision["reason"])
        create_alert(
            db,
            "WARNING",
            "Challenger rejected",
            f"Challenger {challenger.version} did not meet promotion criteria: {decision['reason']}",
            "self_healing",
        )

    workflow.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(workflow)
    _broadcast_workflow(workflow)
    return workflow
