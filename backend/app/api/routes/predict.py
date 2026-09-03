from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import client_key, rate_limiter
from app.deployment.predictor import NoActiveModelError, predict as run_prediction
from app.schemas.schemas import PredictRequest, PredictResponse

router = APIRouter(prefix="/api/v1", tags=["prediction"])


@router.post("/predict", response_model=PredictResponse)
def predict(request: Request, body: PredictRequest, db: Session = Depends(get_db)):
    rate_limiter.check(f"predict:{client_key(request)}", settings.RATE_LIMIT_PREDICT_PER_MINUTE)
    try:
        result = run_prediction(db, body.features, ground_truth=body.ground_truth)
    except NoActiveModelError as exc:
        raise HTTPException(
            status_code=400, detail={"error": "NO_ACTIVE_MODEL", "message": str(exc)}
        ) from exc
    return result
