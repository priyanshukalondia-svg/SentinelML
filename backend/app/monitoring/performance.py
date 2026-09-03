"""Model performance monitoring against the champion baseline (Section 23)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sklearn.metrics import f1_score
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import ModelVersion, PredictionLog


def compute_performance_report(db: Session, champion: Optional[ModelVersion]) -> dict:
    if champion is None:
        return {
            "baseline_f1": None,
            "current_f1": None,
            "degradation_pct": None,
            "sample_size": 0,
            "computed_at": datetime.now(timezone.utc),
        }

    baseline_f1 = champion.metrics.get("f1")

    labeled = db.execute(
        select(PredictionLog)
        .where(PredictionLog.model_version == champion.version, PredictionLog.ground_truth.is_not(None))
        .order_by(PredictionLog.created_at.desc())
        .limit(500)
    ).scalars().all()

    if not labeled:
        return {
            "baseline_f1": baseline_f1,
            "current_f1": None,
            "degradation_pct": None,
            "sample_size": 0,
            "computed_at": datetime.now(timezone.utc),
        }

    y_true = [p.ground_truth for p in labeled]
    y_pred = [p.prediction for p in labeled]
    current_f1 = float(f1_score(y_true, y_pred, zero_division=0))

    degradation_pct = None
    if baseline_f1:
        degradation_pct = round(max((baseline_f1 - current_f1) / baseline_f1 * 100, 0), 2)

    return {
        "baseline_f1": baseline_f1,
        "current_f1": current_f1,
        "degradation_pct": degradation_pct,
        "sample_size": len(labeled),
        "computed_at": datetime.now(timezone.utc),
    }
