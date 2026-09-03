from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.monitoring.performance import compute_performance_report
from app.registry.registry_service import get_champion
from app.services.monitoring_service import build_drift_report, build_full_overview

router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


@router.get("/overview")
def monitoring_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    return build_full_overview(db)


@router.get("/drift")
def monitoring_drift(method: str = "psi", db: Session = Depends(get_db)) -> Dict[str, Any]:
    return build_drift_report(db, method=method)


@router.get("/performance")
def monitoring_performance(db: Session = Depends(get_db)) -> Dict[str, Any]:
    champion = get_champion(db)
    return compute_performance_report(db, champion)
