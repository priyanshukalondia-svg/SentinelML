from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import Dataset
from app.schemas.schemas import DatasetSummary
from app.services.default_dataset import build_default_dataset
from app.services.dataset_service import ingest_dataset

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.get("", response_model=List[DatasetSummary])
def list_datasets(db: Session = Depends(get_db)):
    return db.execute(select(Dataset).order_by(Dataset.created_at.desc())).scalars().all()


@router.get("/{dataset_id}", response_model=DatasetSummary)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail={"error": "DATASET_NOT_FOUND", "message": "Dataset not found."})
    return dataset


@router.post("/upload", response_model=DatasetSummary)
async def upload_dataset(
    file: UploadFile = File(...),
    target_column: str = Form("fraud"),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail={"error": "UNSUPPORTED_FILE_TYPE", "message": "Only CSV files are supported."},
        )
    raw = await file.read()
    try:
        dataset = ingest_dataset(db, file.filename, raw, target_column=target_column)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "UPLOAD_FAILED", "message": str(exc)}) from exc
    return dataset


@router.post("/default", response_model=DatasetSummary)
def load_default_dataset(db: Session = Depends(get_db)):
    """Load the built-in fraud dataset through the normal ingestion path."""
    try:
        return ingest_dataset(db, "sentinelml_default_transactions.csv", build_default_dataset(), target_column="fraud")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "DEFAULT_DATASET_FAILED", "message": str(exc)}) from exc
