from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SentinelBaseModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)


class DatasetSummary(SentinelBaseModel):
    id: int
    dataset_id: str
    version: str
    file_name: str
    row_count: int
    feature_count: int
    target_column: str
    validation_status: str
    is_reference: bool
    quality_report: Dict[str, Any]
    created_at: datetime


class TrainingRequest(SentinelBaseModel):
    dataset_id: int
    models: List[str] = Field(
        default_factory=lambda: ["logistic_regression", "random_forest", "xgboost", "svm"],
        description="Subset of: logistic_regression, random_forest, xgboost, svm",
    )
    triggered_by: str = "manual"


class TrainingRunOut(SentinelBaseModel):
    id: int
    run_group_id: str
    model_type: str
    status: str
    mlflow_run_id: str
    params: Dict[str, Any]
    metrics: Dict[str, Any]
    error_message: str
    triggered_by: str
    started_at: datetime
    completed_at: Optional[datetime]


class ModelVersionOut(SentinelBaseModel):
    id: int
    model_name: str
    version: str
    dataset_version: str
    metrics: Dict[str, Any]
    state: str
    deployment_status: str
    git_commit: str
    created_at: datetime


class PredictRequest(SentinelBaseModel):
    features: Dict[str, float]
    ground_truth: Optional[int] = None


class PredictResponse(SentinelBaseModel):
    prediction: int
    probability: float
    model_version: str
    latency_ms: float


class DriftFeatureResult(SentinelBaseModel):
    feature: str
    drift_score: float
    status: str  # NORMAL / WARNING / HIGH


class DriftReport(SentinelBaseModel):
    method: str
    overall_status: str
    features: List[DriftFeatureResult]
    computed_at: datetime


class PerformanceReport(SentinelBaseModel):
    baseline_f1: Optional[float]
    current_f1: Optional[float]
    degradation_pct: Optional[float]
    sample_size: int
    computed_at: datetime


class HealthScore(SentinelBaseModel):
    overall: int
    performance: int
    data_quality: int
    drift: int
    latency: int
    errors: int
    status: str  # HEALTHY / WARNING / CRITICAL
    computed_at: datetime


class AlertOut(SentinelBaseModel):
    id: int
    severity: str
    title: str
    description: str
    source: str
    state: str
    created_at: datetime
    resolved_at: Optional[datetime]


class AuditLogOut(SentinelBaseModel):
    id: int
    event_type: str
    description: str
    status: str
    model_version: Optional[str]
    dataset_version: Optional[str]
    timestamp: datetime


class RecoveryWorkflowOut(SentinelBaseModel):
    id: int
    trigger: str
    status: str
    champion_version: str
    challenger_version: str
    champion_metric: Optional[float]
    challenger_metric: Optional[float]
    outcome: str
    log: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]


class SimulationResponse(SentinelBaseModel):
    message: str
    recovery_workflow_id: Optional[int] = None


class ErrorResponse(SentinelBaseModel):
    error: str
    message: str
    timestamp: datetime
