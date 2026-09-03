from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core.database import get_db
from app.deployment.predictor import clear_model_cache
from app.models.db_models import ModelVersion
from app.registry.registry_service import get_champion, list_models, promote_model, rollback_to_previous
from app.schemas.schemas import ModelVersionOut, PredictRequest
from app.services.dataset_service import load_dataframe
from app.services.explainability import explain_single_prediction, global_feature_importance

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("", response_model=List[ModelVersionOut])
def get_models(db: Session = Depends(get_db)):
    return list_models(db)


@router.get("/{model_id}", response_model=ModelVersionOut)
def get_model(model_id: int, db: Session = Depends(get_db)):
    model = db.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(status_code=404, detail={"error": "MODEL_NOT_FOUND", "message": "Model version not found."})
    return model


@router.get("/{model_id}/lineage")
def get_model_lineage(model_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    model = db.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(status_code=404, detail={"error": "MODEL_NOT_FOUND", "message": "Model version not found."})
    run = model.training_run
    return {
        "model_version": model.version,
        "dataset_version": model.dataset_version,
        "training_run_id": run.id if run else None,
        "model_type": run.model_type if run else None,
        "mlflow_run_id": run.mlflow_run_id if run else None,
        "git_commit": model.git_commit,
        "metrics": model.metrics,
        "params": run.params if run else {},
        "deployment_status": model.deployment_status,
        "state": model.state,
        "created_at": model.created_at,
    }


@router.post("/{model_id}/deploy", response_model=ModelVersionOut)
def deploy_model(model_id: int, db: Session = Depends(get_db)):
    model = db.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(status_code=404, detail={"error": "MODEL_NOT_FOUND", "message": "Model version not found."})
    promoted = promote_model(db, model)
    clear_model_cache()
    return promoted


@router.post("/{model_id}/rollback", response_model=ModelVersionOut)
def rollback_model(model_id: int, db: Session = Depends(get_db)):
    """Manually trigger a rollback away from the given (presumably unhealthy) model."""
    model = db.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(status_code=404, detail={"error": "MODEL_NOT_FOUND", "message": "Model version not found."})

    restored = rollback_to_previous(db, model.model_name)
    if restored is None:
        raise HTTPException(
            status_code=400,
            detail={"error": "NO_PREVIOUS_MODEL", "message": "No previous healthy model available to roll back to."},
        )
    clear_model_cache()
    record_event(db, "ROLLBACK_TRIGGERED", f"Manual rollback initiated away from {model.version}.", "WARNING")
    return restored


@router.get("/{model_id}/explainability/global")
def get_global_explainability(model_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Global feature importance (Section 29)."""
    import joblib

    model = db.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(status_code=404, detail={"error": "MODEL_NOT_FOUND", "message": "Model version not found."})

    artifact = joblib.load(model.model_path)
    run = model.training_run
    dataset = run.dataset if run else None
    if dataset is None:
        raise HTTPException(status_code=400, detail={"error": "NO_DATASET", "message": "Underlying dataset unavailable."})

    df = load_dataframe(dataset)
    y = df[dataset.target_column]
    X = df[artifact["features"]].fillna(0)
    X_scaled = artifact["scaler"].transform(X.sample(n=min(300, len(X)), random_state=42))
    y_sample = y.sample(n=min(300, len(y)), random_state=42)

    return global_feature_importance(artifact["model"], artifact["features"], X_scaled, y_sample)


@router.post("/{model_id}/explainability/predict")
def explain_prediction(model_id: int, body: PredictRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Individual prediction explanation (Section 29)."""
    import joblib

    model = db.get(ModelVersion, model_id)
    if not model:
        raise HTTPException(status_code=404, detail={"error": "MODEL_NOT_FOUND", "message": "Model version not found."})

    artifact = joblib.load(model.model_path)
    return explain_single_prediction(artifact["model"], artifact["scaler"], artifact["features"], body.features)
