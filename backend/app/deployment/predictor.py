"""Prediction serving (Section 19) + prediction logging (Section 20)."""
from __future__ import annotations

import time
from functools import lru_cache
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.core.events import event_bus
from app.models.db_models import ModelVersion, PredictionLog
from app.registry.registry_service import get_champion


class NoActiveModelError(Exception):
    pass


@lru_cache(maxsize=8)
def _load_artifact(model_path: str):
    return joblib.load(model_path)


def predict(
    db: Session,
    features: Dict[str, float],
    ground_truth: Optional[int] = None,
    is_simulated: bool = False,
) -> Dict:
    champion: ModelVersion | None = get_champion(db)
    if champion is None:
        raise NoActiveModelError("No champion model is currently deployed.")

    artifact = _load_artifact(champion.model_path)
    model = artifact["model"]
    scaler = artifact["scaler"]
    feature_order = artifact["features"]

    row = pd.DataFrame([[features.get(f, 0.0) for f in feature_order]], columns=feature_order)

    start = time.time()
    row_scaled = scaler.transform(row)
    pred = int(model.predict(row_scaled)[0])
    proba = float(model.predict_proba(row_scaled)[0][1]) if hasattr(model, "predict_proba") else float(pred)
    latency_ms = (time.time() - start) * 1000

    log_entry = PredictionLog(
        model_version=champion.version,
        prediction=pred,
        probability=proba,
        latency_ms=latency_ms,
        ground_truth=ground_truth,
        input_features=features,
        is_simulated=is_simulated,
    )
    db.add(log_entry)
    db.commit()

    event_bus.broadcast_sync(
        "prediction",
        {"model_version": champion.version, "prediction": pred, "probability": proba, "latency_ms": latency_ms},
    )

    return {
        "prediction": pred,
        "probability": proba,
        "model_version": champion.version,
        "latency_ms": latency_ms,
    }


def clear_model_cache() -> None:
    _load_artifact.cache_clear()
