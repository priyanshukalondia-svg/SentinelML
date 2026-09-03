from __future__ import annotations

from typing import Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import Dataset, ModelVersion, PredictionLog
from app.monitoring.drift import compute_drift_report
from app.monitoring.health import compute_health_score
from app.monitoring.performance import compute_performance_report
from app.registry.registry_service import get_champion


def get_reference_dataset(db: Session) -> Optional[Dataset]:
    return db.execute(select(Dataset).where(Dataset.is_reference.is_(True))).scalars().first()


def get_latest_dataset(db: Session) -> Optional[Dataset]:
    return db.execute(select(Dataset).order_by(Dataset.created_at.desc())).scalars().first()


def get_recent_production_frame(db: Session, limit: int = 300) -> Optional[pd.DataFrame]:
    logs = db.execute(
        select(PredictionLog).order_by(PredictionLog.created_at.desc()).limit(limit)
    ).scalars().all()
    if not logs:
        return None
    rows = [log.input_features for log in logs if log.input_features]
    if not rows:
        return None
    return pd.DataFrame(rows)


def build_drift_report(db: Session, method: str = "psi") -> dict:
    reference = get_reference_dataset(db)
    current_frame = get_recent_production_frame(db)

    if reference is None or current_frame is None or current_frame.empty:
        return {
            "method": method.upper(),
            "overall_status": "NORMAL",
            "features": [],
            "computed_at": pd.Timestamp.utcnow(),
        }

    reference_df = pd.read_csv(reference.file_path)
    if reference.target_column in reference_df.columns:
        reference_df = reference_df.drop(columns=[reference.target_column])

    return compute_drift_report(reference_df, current_frame, method=method)


def build_full_overview(db: Session) -> dict:
    champion: Optional[ModelVersion] = get_champion(db)
    latest_dataset = get_latest_dataset(db)
    drift_report = build_drift_report(db)
    performance = compute_performance_report(db, champion)
    health = compute_health_score(
        db,
        champion,
        latest_dataset,
        performance.get("degradation_pct"),
        drift_report.get("overall_status", "NORMAL"),
    )

    recent = db.execute(
        select(PredictionLog).order_by(PredictionLog.created_at.desc()).limit(200)
    ).scalars().all()
    avg_latency = round(sum(p.latency_ms for p in recent) / len(recent), 2) if recent else 0.0

    return {
        "active_model": champion.version if champion else None,
        "health": health,
        "drift": drift_report,
        "performance": performance,
        "avg_latency_ms": avg_latency,
        "prediction_volume": len(recent),
    }
