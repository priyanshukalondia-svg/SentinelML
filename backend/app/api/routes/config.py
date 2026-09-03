"""
Exposes the tunables from Section 37 for the dashboard's Settings page.

Updates are applied in-memory for the life of the running process (true
hot-reload) rather than persisted to disk — this keeps the demo simple
while still avoiding hard-coded thresholds anywhere in the application
logic itself, which all read from `settings` at call time.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(prefix="/api/v1/config", tags=["config"])


class ConfigOut(BaseModel):
    monitoring_interval_seconds: int
    drift_warning_threshold: float
    drift_critical_threshold: float
    promotion_metric: str
    promotion_min_improvement: float
    promotion_max_latency_increase_pct: float
    rollback_max_error_rate: float
    rollback_min_health_score: int
    training_timeout_seconds: int
    retraining_cooldown_seconds: int
    demo_mode: bool


class ConfigUpdate(BaseModel):
    monitoring_interval_seconds: Optional[int] = None
    drift_warning_threshold: Optional[float] = None
    drift_critical_threshold: Optional[float] = None
    promotion_min_improvement: Optional[float] = None
    promotion_max_latency_increase_pct: Optional[float] = None
    rollback_max_error_rate: Optional[float] = None
    rollback_min_health_score: Optional[int] = None
    training_timeout_seconds: Optional[int] = None
    retraining_cooldown_seconds: Optional[int] = None


def _to_out() -> ConfigOut:
    return ConfigOut(
        monitoring_interval_seconds=settings.MONITORING_INTERVAL_SECONDS,
        drift_warning_threshold=settings.DRIFT_WARNING_THRESHOLD,
        drift_critical_threshold=settings.DRIFT_CRITICAL_THRESHOLD,
        promotion_metric=settings.PROMOTION_METRIC,
        promotion_min_improvement=settings.PROMOTION_MIN_IMPROVEMENT,
        promotion_max_latency_increase_pct=settings.PROMOTION_MAX_LATENCY_INCREASE_PCT,
        rollback_max_error_rate=settings.ROLLBACK_MAX_ERROR_RATE,
        rollback_min_health_score=settings.ROLLBACK_MIN_HEALTH_SCORE,
        training_timeout_seconds=settings.TRAINING_TIMEOUT_SECONDS,
        retraining_cooldown_seconds=settings.RETRAINING_COOLDOWN_SECONDS,
        demo_mode=settings.DEMO_MODE,
    )


@router.get("", response_model=ConfigOut)
def get_config() -> ConfigOut:
    return _to_out()


@router.patch("", response_model=ConfigOut)
def update_config(body: ConfigUpdate) -> ConfigOut:
    field_map = {
        "monitoring_interval_seconds": "MONITORING_INTERVAL_SECONDS",
        "drift_warning_threshold": "DRIFT_WARNING_THRESHOLD",
        "drift_critical_threshold": "DRIFT_CRITICAL_THRESHOLD",
        "promotion_min_improvement": "PROMOTION_MIN_IMPROVEMENT",
        "promotion_max_latency_increase_pct": "PROMOTION_MAX_LATENCY_INCREASE_PCT",
        "rollback_max_error_rate": "ROLLBACK_MAX_ERROR_RATE",
        "rollback_min_health_score": "ROLLBACK_MIN_HEALTH_SCORE",
        "training_timeout_seconds": "TRAINING_TIMEOUT_SECONDS",
        "retraining_cooldown_seconds": "RETRAINING_COOLDOWN_SECONDS",
    }
    for field, attr in field_map.items():
        value = getattr(body, field)
        if value is not None:
            setattr(settings, attr, value)
    return _to_out()
