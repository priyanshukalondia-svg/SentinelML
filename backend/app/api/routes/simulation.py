"""
Failure simulation endpoints (Section 28).

These are the endpoints behind the dashboard's "Simulate Drift / Model
Degradation / Latency Spike / Error Spike" buttons. Every simulated
prediction is written to PredictionLog with is_simulated=True and is kept
isolated from a real dataset upload — nothing here mutates the underlying
training data on disk.
"""
from __future__ import annotations

import random
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import client_key, rate_limiter
from app.deployment.predictor import predict as run_prediction
from app.models.db_models import PredictionLog
from app.monitoring.drift import inject_synthetic_drift
from app.monitoring.health import compute_health_score
from app.registry.registry_service import get_champion
from app.schemas.schemas import SimulationResponse
from app.self_healing.engine import create_alert, trigger_self_healing
from app.self_healing.rollback import maybe_rollback
from app.services.dataset_service import load_dataframe
from app.services.monitoring_service import build_drift_report, get_latest_dataset, get_reference_dataset

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


def _guard(request: Request) -> None:
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=403,
            detail={"error": "SIMULATION_DISABLED", "message": "Failure simulation is disabled (DEMO_MODE=false)."},
        )
    rate_limiter.check(f"simulation:{client_key(request)}", settings.RATE_LIMIT_SIMULATION_PER_MINUTE)


@router.post("/drift", response_model=SimulationResponse)
def simulate_drift(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    _guard(request)
    reference = get_reference_dataset(db)
    if reference is None:
        raise HTTPException(status_code=400, detail={"error": "NO_REFERENCE_DATASET", "message": "Upload a dataset first."})

    champion = get_champion(db)
    if champion is None:
        raise HTTPException(status_code=400, detail={"error": "NO_ACTIVE_MODEL", "message": "Deploy a champion model first."})

    df = load_dataframe(reference)
    feature_df = df.drop(columns=[reference.target_column], errors="ignore")
    drifted = inject_synthetic_drift(feature_df, intensity=3.0)

    sample = drifted.sample(n=min(60, len(drifted)), random_state=None)
    for _, row in sample.iterrows():
        features = {k: float(v) for k, v in row.items() if isinstance(v, (int, float))}
        try:
            run_prediction(db, features, is_simulated=True)
        except Exception:
            continue

    report = build_drift_report(db)
    record_event(db, "DRIFT_DETECTED", f"Simulated drift produced overall status {report['overall_status']}.", "WARNING")

    workflow_id = None
    if report["overall_status"] in ("WARNING", "CRITICAL"):
        create_alert(
            db,
            "CRITICAL" if report["overall_status"] == "CRITICAL" else "WARNING",
            f"{report['overall_status']} drift detected",
            "Simulated production data has drifted from the training distribution.",
            "monitoring",
        )
        try:
            latest = get_latest_dataset(db) or reference
            workflow = trigger_self_healing(db, "Critical feature drift (simulated)", latest)
            workflow_id = workflow.id
        except RuntimeError:
            pass  # cooldown active — still a valid outcome, surfaced via message below

    return {
        "message": f"Drift simulation complete — overall status: {report['overall_status']}.",
        "recovery_workflow_id": workflow_id,
    }


@router.post("/degradation", response_model=SimulationResponse)
def simulate_degradation(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    _guard(request)
    reference = get_reference_dataset(db)
    champion = get_champion(db)
    if reference is None or champion is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "PRECONDITION_FAILED", "message": "A reference dataset and deployed champion are required."},
        )

    df = load_dataframe(reference)
    feature_df = df.drop(columns=[reference.target_column], errors="ignore")
    sample = feature_df.sample(n=min(80, len(feature_df)), random_state=None)

    for _, row in sample.iterrows():
        features = {k: float(v) for k, v in row.items() if isinstance(v, (int, float))}
        try:
            result = run_prediction(db, features, is_simulated=True)
        except Exception:
            continue
        # Deliberately mislabel most simulated predictions to drag F1 down.
        wrong_label = 1 - result["prediction"] if random.random() < 0.75 else result["prediction"]
        log = db.query(PredictionLog).order_by(PredictionLog.id.desc()).first()
        if log:
            log.ground_truth = wrong_label
    db.commit()

    latest_dataset = get_latest_dataset(db)
    from app.monitoring.performance import compute_performance_report

    performance = compute_performance_report(db, champion)
    drift_report = build_drift_report(db)
    health = compute_health_score(
        db, champion, latest_dataset, performance.get("degradation_pct"), drift_report.get("overall_status", "NORMAL")
    )

    record_event(
        db,
        "MODEL_PERFORMANCE_DEGRADED",
        f"Simulated degradation: current F1={performance.get('current_f1')}, health={health['overall']}.",
        "WARNING",
    )

    rollback_result = maybe_rollback(
        db, health["overall"], error_rate=0.0, reason_hint="Simulated model performance degradation."
    )

    message = f"Degradation simulation complete — health score {health['overall']}."
    if rollback_result:
        message += f" Automatic rollback restored {rollback_result['restored_version']}."
    else:
        message += " Health remained within rollback thresholds; no rollback triggered."

    return {"message": message, "recovery_workflow_id": None}


@router.post("/latency", response_model=SimulationResponse)
def simulate_latency(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    _guard(request)
    champion = get_champion(db)
    if champion is None:
        raise HTTPException(status_code=400, detail={"error": "NO_ACTIVE_MODEL", "message": "Deploy a champion model first."})

    for _ in range(40):
        db.add(
            PredictionLog(
                model_version=champion.version,
                prediction=random.randint(0, 1),
                probability=random.random(),
                latency_ms=random.uniform(600, 1500),
                is_simulated=True,
            )
        )
    db.commit()

    latest_dataset = get_latest_dataset(db)
    drift_report = build_drift_report(db)
    health = compute_health_score(db, champion, latest_dataset, None, drift_report.get("overall_status", "NORMAL"))
    create_alert(db, "WARNING", "Latency spike detected", f"P95 latency degraded model health to {health['overall']}.", "monitoring")
    record_event(db, "LATENCY_SPIKE_DETECTED", f"Simulated latency spike — health now {health['overall']}.", "WARNING")

    rollback_result = maybe_rollback(db, health["overall"], error_rate=0.0, reason_hint="Simulated latency spike.")
    message = f"Latency spike simulated — health score {health['overall']}."
    if rollback_result:
        message += f" Automatic rollback restored {rollback_result['restored_version']}."
    return {"message": message, "recovery_workflow_id": None}


@router.post("/errors", response_model=SimulationResponse)
def simulate_errors(request: Request, db: Session = Depends(get_db)) -> Dict[str, Any]:
    _guard(request)
    champion = get_champion(db)
    if champion is None:
        raise HTTPException(status_code=400, detail={"error": "NO_ACTIVE_MODEL", "message": "Deploy a champion model first."})

    total = 40
    error_count = int(total * 0.4)
    for i in range(total):
        db.add(
            PredictionLog(
                model_version=champion.version,
                prediction=random.randint(0, 1),
                probability=random.random(),
                latency_ms=random.uniform(50, 150),
                error_status="ERROR" if i < error_count else "OK",
                is_simulated=True,
            )
        )
    db.commit()

    error_rate = error_count / total
    latest_dataset = get_latest_dataset(db)
    drift_report = build_drift_report(db)
    health = compute_health_score(db, champion, latest_dataset, None, drift_report.get("overall_status", "NORMAL"))
    create_alert(db, "CRITICAL", "API error spike detected", f"Error rate at {error_rate:.0%}.", "monitoring")
    record_event(db, "ERROR_SPIKE_DETECTED", f"Simulated error spike at {error_rate:.0%}.", "CRITICAL")

    rollback_result = maybe_rollback(db, health["overall"], error_rate=error_rate, reason_hint="Simulated API error spike.")
    message = f"Error spike simulated — error rate {error_rate:.0%}, health score {health['overall']}."
    if rollback_result:
        message += f" Automatic rollback restored {rollback_result['restored_version']}."
    return {"message": message, "recovery_workflow_id": None}
