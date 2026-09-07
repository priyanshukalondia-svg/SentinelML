import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import alerts, audit, config, datasets, health, models, monitoring, predict, simulation, training, ws
from app.core.config import settings
from app.core.database import init_db
from app.services.auto_monitor import monitoring_loop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sentinelml")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(monitoring_loop())
    logger.info("SentinelML backend started. Monitoring interval: %ss", settings.MONITORING_INTERVAL_SECONDS)
    yield
    task.cancel()


app = FastAPI(
    title="SentinelML API",
    description="Self-healing MLOps control plane — see /docs for the full API.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_origin_regex=settings.CORS_ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Ensures every error follows the structured shape from Section 43,
    even for exceptions raised with a plain string detail."""
    detail = exc.detail
    if isinstance(detail, dict):
        body = {**detail, "timestamp": datetime.now(timezone.utc).isoformat()}
    else:
        body = {"error": "HTTP_ERROR", "message": str(detail), "timestamp": datetime.now(timezone.utc).isoformat()}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. See server logs for details.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


app.include_router(health.router)
app.include_router(datasets.router)
app.include_router(training.router)
app.include_router(models.router)
app.include_router(predict.router)
app.include_router(monitoring.router)
app.include_router(alerts.router)
app.include_router(audit.router)
app.include_router(simulation.router)
app.include_router(config.router)
app.include_router(ws.router)


@app.get("/")
def root():
    return {"service": "SentinelML API", "docs": "/docs", "health": "/health"}
