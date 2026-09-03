from datetime import datetime, timezone

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(64), index=True)  # logical name, e.g. "fraud_transactions"
    version: Mapped[str] = mapped_column(String(16))  # e.g. v1.0
    file_name: Mapped[str] = mapped_column(String(256))
    file_path: Mapped[str] = mapped_column(String(512))
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    feature_count: Mapped[int] = mapped_column(Integer, default=0)
    target_column: Mapped[str] = mapped_column(String(128), default="")
    schema_json: Mapped[dict] = mapped_column(JSON, default=dict)
    quality_report: Mapped[dict] = mapped_column(JSON, default=dict)
    validation_status: Mapped[str] = mapped_column(String(16), default="HEALTHY")  # HEALTHY / WARNING / FAILED
    is_reference: Mapped[bool] = mapped_column(default=False)  # used as drift baseline
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    training_runs: Mapped[list["TrainingRun"]] = relationship(back_populates="dataset")


class TrainingRun(Base):
    __tablename__ = "training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_group_id: Mapped[str] = mapped_column(String(64), index=True)  # groups multiple models trained together
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"))
    model_type: Mapped[str] = mapped_column(String(64))
    mlflow_run_id: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(16), default="RUNNING")  # RUNNING/COMPLETED/FAILED/TIMEOUT
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")
    triggered_by: Mapped[str] = mapped_column(String(32), default="manual")  # manual / self_healing
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="training_runs")
    model_version: Mapped["ModelVersion"] = relationship(back_populates="training_run", uselist=False)


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(64), default="fraud-detector")
    version: Mapped[str] = mapped_column(String(16))  # e.g. v1.0
    training_run_id: Mapped[int] = mapped_column(ForeignKey("training_runs.id"))
    model_path: Mapped[str] = mapped_column(String(512))
    dataset_version: Mapped[str] = mapped_column(String(16))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    git_commit: Mapped[str] = mapped_column(String(64), default="")
    state: Mapped[str] = mapped_column(String(16), default="CANDIDATE")  # CANDIDATE/CHAMPION/CHALLENGER/ARCHIVED/REJECTED
    deployment_status: Mapped[str] = mapped_column(String(16), default="NOT_DEPLOYED")  # NOT_DEPLOYED/DEPLOYED
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    training_run: Mapped["TrainingRun"] = relationship(back_populates="model_version")


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_version: Mapped[str] = mapped_column(String(16))
    prediction: Mapped[int] = mapped_column(Integer)
    probability: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[float] = mapped_column(Float)
    ground_truth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_status: Mapped[str] = mapped_column(String(16), default="OK")
    input_features: Mapped[dict] = mapped_column(JSON, default=dict)
    is_simulated: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, index=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    severity: Mapped[str] = mapped_column(String(16))  # CRITICAL / WARNING / INFO / RESOLVED
    title: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(32), default="monitoring")  # monitoring/self_healing/system
    state: Mapped[str] = mapped_column(String(16), default="OPEN")  # OPEN/ACKNOWLEDGED/RESOLVED
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="INFO")
    model_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    dataset_version: Mapped[str | None] = mapped_column(String(16), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(default=utcnow, index=True)


class RecoveryWorkflow(Base):
    __tablename__ = "recovery_workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trigger: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="DETECTED")
    # DETECTED -> RETRAINING -> EVALUATING -> PROMOTED/REJECTED -> DEPLOYED / ROLLED_BACK
    champion_version: Mapped[str] = mapped_column(String(16), default="")
    challenger_version: Mapped[str] = mapped_column(String(16), default="")
    champion_metric: Mapped[float | None] = mapped_column(Float, nullable=True)
    challenger_metric: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome: Mapped[str] = mapped_column(String(32), default="")  # PROMOTED / REJECTED / ROLLED_BACK
    log: Mapped[list] = mapped_column(JSON, default=list)  # ordered list of {step, timestamp, message}
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)


class SystemState(Base):
    """Single-row table tracking small pieces of global mutable state
    (active champion model name, last health check time, last drift check, etc.)."""

    __tablename__ = "system_state"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
