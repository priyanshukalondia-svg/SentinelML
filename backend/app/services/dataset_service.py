"""Dataset ingestion, storage and versioning (Sections 8 & 10)."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import record_event
from app.core.config import settings
from app.models.db_models import Dataset
from app.services.data_validation import validate_dataset


def _slugify(name: str) -> str:
    stem = Path(name).stem
    return re.sub(r"[^a-zA-Z0-9_]+", "_", stem).strip("_").lower() or "dataset"


def _next_version(db: Session, dataset_id: str) -> str:
    existing = db.execute(
        select(Dataset).where(Dataset.dataset_id == dataset_id)
    ).scalars().all()
    if not existing:
        return "v1.0"
    minor_numbers = []
    for d in existing:
        m = re.match(r"v(\d+)\.(\d+)", d.version)
        if m:
            minor_numbers.append((int(m.group(1)), int(m.group(2))))
    if not minor_numbers:
        return "v1.0"
    major, minor = max(minor_numbers)
    return f"v{major}.{minor + 1}"


def ingest_dataset(db: Session, file_name: str, raw_bytes: bytes, target_column: str = "fraud") -> Dataset:
    """Validate, store, and version an uploaded CSV file."""
    if len(raw_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValueError(f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    dataset_id = _slugify(file_name)
    version = _next_version(db, dataset_id)

    storage_dir = Path(settings.DATA_DIR) / dataset_id / version
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = storage_dir / "data.csv"
    file_path.write_bytes(raw_bytes)

    df = pd.read_csv(file_path)

    previous = db.execute(
        select(Dataset)
        .where(Dataset.dataset_id == dataset_id)
        .order_by(Dataset.created_at.desc())
    ).scalars().first()
    previous_schema = previous.schema_json.get("dtypes") if previous else None

    report = validate_dataset(df, target_column=target_column, previous_schema=previous_schema)

    dataset = Dataset(
        dataset_id=dataset_id,
        version=version,
        file_name=file_name,
        file_path=str(file_path),
        row_count=report["row_count"],
        feature_count=report["column_count"],
        target_column=target_column,
        schema_json={"dtypes": report["dtypes"]},
        quality_report=report,
        validation_status=report["status"],
        is_reference=(previous is None),  # first version of a dataset becomes the drift reference by default
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    record_event(
        db,
        event_type="DATA_VALIDATION_FAILED" if report["status"] == "FAILED" else "DATASET_INGESTED",
        description=f"Dataset '{dataset_id}' {version} ingested with status {report['status']}.",
        status=report["status"],
        dataset_version=version,
    )

    return dataset


def load_dataframe(dataset: Dataset) -> pd.DataFrame:
    return pd.read_csv(dataset.file_path)
