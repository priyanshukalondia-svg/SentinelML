"""
Composite model/system health scoring (Section 24).

The score is a transparent, documented weighted average of five
sub-scores, each 0-100:

  performance  - how close current F1 is to the champion baseline
  data_quality - inverse of recent dataset validation issues
  drift        - inverse of the worst recent feature drift score
  latency      - how close p95 prediction latency is to a target budget
  errors       - inverse of the recent prediction error rate

Weights sum to 1.0 and are intentionally simple/explainable rather than
learned, per the "prefer simple transparent statistical methods" guidance
in Section 7.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import Dataset, ModelVersion, PredictionLog

WEIGHTS = {
    "performance": 0.30,
    "data_quality": 0.15,
    "drift": 0.25,
    "latency": 0.15,
    "errors": 0.15,
}

LATENCY_BUDGET_MS = 200.0


def _performance_score(degradation_pct: Optional[float]) -> int:
    if degradation_pct is None:
        return 100
    return max(0, round(100 - degradation_pct * 3))


def _data_quality_score(dataset: Optional[Dataset]) -> int:
    if dataset is None:
        return 100
    status = dataset.validation_status
    return {"HEALTHY": 100, "WARNING": 75, "FAILED": 30}.get(status, 90)


def _drift_score(overall_drift_status: str) -> int:
    return {"NORMAL": 96, "WARNING": 70, "CRITICAL": 35}.get(overall_drift_status, 96)


def _latency_score(p95_latency_ms: float) -> int:
    if p95_latency_ms <= 0:
        return 100
    ratio = p95_latency_ms / LATENCY_BUDGET_MS
    return max(0, round(100 - max(ratio - 1, 0) * 100))


def _errors_score(error_rate: float) -> int:
    return max(0, round(100 - error_rate * 100 * 4))


def compute_health_score(
    db: Session,
    champion: Optional[ModelVersion],
    latest_dataset: Optional[Dataset],
    degradation_pct: Optional[float],
    overall_drift_status: str,
) -> dict:
    recent = db.execute(
        select(PredictionLog).order_by(PredictionLog.created_at.desc()).limit(200)
    ).scalars().all()

    if recent:
        latencies = sorted(p.latency_ms for p in recent)
        p95_index = max(0, int(len(latencies) * 0.95) - 1)
        p95_latency = latencies[p95_index]
        error_rate = sum(1 for p in recent if p.error_status != "OK") / len(recent)
    else:
        p95_latency = 0.0
        error_rate = 0.0

    perf = _performance_score(degradation_pct)
    dq = _data_quality_score(latest_dataset)
    drift = _drift_score(overall_drift_status)
    latency = _latency_score(p95_latency)
    errors = _errors_score(error_rate)

    overall = round(
        perf * WEIGHTS["performance"]
        + dq * WEIGHTS["data_quality"]
        + drift * WEIGHTS["drift"]
        + latency * WEIGHTS["latency"]
        + errors * WEIGHTS["errors"]
    )

    if overall >= 85:
        status = "HEALTHY"
    elif overall >= 60:
        status = "WARNING"
    else:
        status = "CRITICAL"

    return {
        "overall": overall,
        "performance": perf,
        "data_quality": dq,
        "drift": drift,
        "latency": latency,
        "errors": errors,
        "status": status,
        "computed_at": datetime.now(timezone.utc),
    }
