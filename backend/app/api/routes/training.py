from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import Dataset, TrainingRun
from app.schemas.schemas import TrainingRequest, TrainingRunOut
from app.training.trainer import train_models

router = APIRouter(prefix="/api/v1/training", tags=["training"])


@router.post("/start", response_model=List[TrainingRunOut])
def start_training(
    request: TrainingRequest,
    db: Session = Depends(get_db),
):
    dataset = db.get(Dataset, request.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail={"error": "DATASET_NOT_FOUND", "message": "Dataset not found."})
    if dataset.validation_status == "FAILED":
        raise HTTPException(
            status_code=400,
            detail={
                "error": "DATA_VALIDATION_FAILED",
                "message": "Training is blocked because the selected dataset failed validation.",
            },
        )

    # Training runs synchronously here for simplicity/demo determinism; each
    # individual model's fit runs in a worker thread with a timeout (Section 11/36).
    runs = train_models(db, dataset, request.models, triggered_by=request.triggered_by)
    return runs


@router.get("/{run_id}", response_model=TrainingRunOut)
def get_training_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(TrainingRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail={"error": "RUN_NOT_FOUND", "message": "Training run not found."})
    return run


@router.get("", response_model=List[TrainingRunOut])
def list_training_runs(db: Session = Depends(get_db)):
    return db.execute(select(TrainingRun).order_by(TrainingRun.started_at.desc()).limit(100)).scalars().all()
