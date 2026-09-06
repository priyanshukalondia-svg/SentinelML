"""
Central application configuration.

All tunables mentioned in SYSTEM_REQUIREMENTS.md (Section 37, 41a) are
exposed here and can be overridden via environment variables / .env file,
so nothing is hard-coded throughout the application.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]  # repo root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- General ---
    APP_NAME: str = "SentinelML"
    ENV: str = "development"
    DEMO_MODE: bool = True

    # --- Database ---
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/backend/sentinelml.db"

    # --- MLflow ---
    MLFLOW_TRACKING_URI: str = f"file:{BASE_DIR}/mlruns"
    MLFLOW_EXPERIMENT_NAME: str = "sentinelml-fraud-detector"
    MLFLOW_ARTIFACT_ROOT: str = f"{BASE_DIR}/mlruns"

    # --- Storage ---
    DATA_DIR: str = f"{BASE_DIR}/ml/datasets"
    MODEL_STORE_DIR: str = f"{BASE_DIR}/ml/models"
    MAX_UPLOAD_SIZE_MB: int = 50

    # --- CORS ---
    CORS_ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://frontend:5173",
        "https://sentinelml.vercel.app",
    ]

    # --- Monitoring ---
    MONITORING_INTERVAL_SECONDS: int = 60

    # --- Drift thresholds ---
    DRIFT_WARNING_THRESHOLD: float = 0.10
    DRIFT_CRITICAL_THRESHOLD: float = 0.25

    # --- Promotion rules ---
    PROMOTION_METRIC: str = "f1"
    PROMOTION_MIN_IMPROVEMENT: float = 0.02
    PROMOTION_MAX_LATENCY_INCREASE_PCT: float = 10.0

    # --- Rollback ---
    ROLLBACK_MAX_ERROR_RATE: float = 0.05
    ROLLBACK_MIN_HEALTH_SCORE: int = 70

    # --- Training ---
    TRAINING_TIMEOUT_SECONDS: int = 900
    RETRAINING_COOLDOWN_SECONDS: int = 300

    # --- Security ---
    SECRET_KEY: str = "change-me-in-production"
    RATE_LIMIT_PREDICT_PER_MINUTE: int = 120
    RATE_LIMIT_SIMULATION_PER_MINUTE: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
