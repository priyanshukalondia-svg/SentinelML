"""
Automated model training (Section 11) + evaluation (Section 12) +
experiment tracking via MLflow (Section 13).

Each call to `train_single_model` performs the full per-model lifecycle:
load -> validate -> split -> preprocess -> train -> evaluate -> log -> register.
"""
from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any, Dict

import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core.config import settings
from app.core.events import event_bus
from app.models.db_models import Dataset, ModelVersion, TrainingRun
from app.services.dataset_service import load_dataframe

try:
    from xgboost import XGBClassifier

    _HAS_XGBOOST = True
except ImportError:  # pragma: no cover - keeps trainer usable without xgboost installed
    _HAS_XGBOOST = False

mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)

MODEL_BUILDERS = {
    "logistic_regression": lambda: LogisticRegression(max_iter=1000, random_state=42),
    "random_forest": lambda: RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    "svm": lambda: SVC(probability=True, kernel="rbf", random_state=42),
}
if _HAS_XGBOOST:
    MODEL_BUILDERS["xgboost"] = lambda: XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42, eval_metric="logloss"
    )


def _next_model_version(db: Session, model_name: str) -> str:
    from sqlalchemy import select

    existing = db.execute(
        select(ModelVersion).where(ModelVersion.model_name == model_name)
    ).scalars().all()
    if not existing:
        return "v1.0"
    import re

    nums = []
    for m in existing:
        match = re.match(r"v(\d+)\.(\d+)", m.version)
        if match:
            nums.append((int(match.group(1)), int(match.group(2))))
    if not nums:
        return "v1.0"
    major, minor = max(nums)
    return f"v{major}.{minor + 1}"


def _fit_and_evaluate(model_type: str, X_train, X_test, y_train, y_test) -> Dict[str, Any]:
    builder = MODEL_BUILDERS.get(model_type)
    if builder is None:
        raise ValueError(f"Unknown or unavailable model_type '{model_type}'.")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = builder()

    train_start = time.time()
    model.fit(X_train_scaled, y_train)
    training_duration = time.time() - train_start

    infer_start = time.time()
    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1] if hasattr(model, "predict_proba") else y_pred
    inference_latency_ms = (time.time() - infer_start) / max(len(X_test_scaled), 1) * 1000

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "training_time": float(training_duration),
        "inference_latency": float(inference_latency_ms),
    }
    try:
        metrics["roc_auc"] = float(roc_auc_score(y_test, y_proba))
        metrics["pr_auc"] = float(average_precision_score(y_test, y_proba))
    except ValueError:
        metrics["roc_auc"] = 0.0
        metrics["pr_auc"] = 0.0

    return {"model": model, "scaler": scaler, "metrics": metrics}


def train_single_model(
    db: Session,
    dataset: Dataset,
    model_type: str,
    run_group_id: str,
    triggered_by: str = "manual",
) -> TrainingRun:
    """Train one model end-to-end and persist a TrainingRun (+ ModelVersion on success)."""
    run = TrainingRun(
        run_group_id=run_group_id,
        dataset_id=dataset.id,
        model_type=model_type,
        status="RUNNING",
        triggered_by=triggered_by,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    event_bus.broadcast_sync("training_started", {"run_id": run.id, "model_type": model_type})

    try:
        df = load_dataframe(dataset)
        target = dataset.target_column
        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not present in dataset.")

        df = df.dropna(subset=[target])
        y = df[target]
        X = df.drop(columns=[target]).select_dtypes(include=[np.number]).fillna(0)

        if X.shape[1] == 0:
            raise ValueError("No numeric feature columns available for training after preprocessing.")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y if y.nunique() > 1 else None
        )

        params = {
            "model_type": model_type,
            "train_test_split": 0.8,
            "random_state": 42,
            "n_features": X.shape[1],
        }

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_fit_and_evaluate, model_type, X_train, X_test, y_train, y_test)
            try:
                result = future.result(timeout=settings.TRAINING_TIMEOUT_SECONDS)
            except FutureTimeoutError as exc:
                raise TimeoutError(
                    f"Training exceeded timeout of {settings.TRAINING_TIMEOUT_SECONDS}s."
                ) from exc

        with mlflow.start_run(run_name=f"{model_type}-{run_group_id[:8]}") as mlflow_run:
            mlflow.log_params(params)
            mlflow.log_metrics(result["metrics"])
            mlflow.set_tag("dataset_version", dataset.version)
            mlflow.set_tag("triggered_by", triggered_by)
            mlflow_run_id = mlflow_run.info.run_id

        model_dir = Path(settings.MODEL_STORE_DIR) / run_group_id
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / f"{model_type}.joblib"
        joblib.dump({"model": result["model"], "scaler": result["scaler"], "features": list(X.columns)}, model_path)

        run.status = "COMPLETED"
        run.mlflow_run_id = mlflow_run_id
        run.params = params
        run.metrics = result["metrics"]
        from datetime import datetime, timezone

        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(run)

        model_version = ModelVersion(
            model_name="fraud-detector",
            version=_next_model_version(db, "fraud-detector"),
            training_run_id=run.id,
            model_path=str(model_path),
            dataset_version=dataset.version,
            metrics=result["metrics"],
            state="CANDIDATE",
        )
        db.add(model_version)
        db.commit()
        db.refresh(model_version)

        record_event(
            db,
            event_type="MODEL_TRAINED",
            description=f"{model_type} trained as {model_version.version} (F1={result['metrics']['f1']:.3f}).",
            status="SUCCESS",
            model_version=model_version.version,
            dataset_version=dataset.version,
        )
        event_bus.broadcast_sync(
            "training_completed",
            {"run_id": run.id, "model_type": model_type, "metrics": result["metrics"]},
        )
        return run

    except Exception as exc:  # noqa: BLE001 - training can fail in many ML-specific ways
        run.status = "TIMEOUT" if isinstance(exc, TimeoutError) else "FAILED"
        run.error_message = str(exc)
        from datetime import datetime, timezone

        run.completed_at = datetime.now(timezone.utc)
        db.commit()
        record_event(
            db,
            event_type="MODEL_TRAINING_FAILED",
            description=f"Training failed for {model_type}: {exc}",
            status="FAILED",
        )
        event_bus.broadcast_sync("training_failed", {"run_id": run.id, "model_type": model_type, "error": str(exc)})
        return run


def train_models(
    db: Session, dataset: Dataset, model_types: list[str], triggered_by: str = "manual"
) -> list[TrainingRun]:
    run_group_id = str(uuid.uuid4())
    results = []
    for model_type in model_types:
        if model_type not in MODEL_BUILDERS:
            continue
        results.append(train_single_model(db, dataset, model_type, run_group_id, triggered_by))
    return results
