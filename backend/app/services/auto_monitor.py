"""
Background monitoring loop (Section 25, 36).

Runs on a configurable interval and checks whether real (non-simulated)
conditions warrant retraining or rollback. This runs independently of the
manual "Simulate ..." buttons, which are the primary way to *demonstrate*
self-healing quickly, but this loop is what makes the system genuinely
self-healing rather than only healing on command.
"""
from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.core.database import SessionLocal
from app.monitoring.health import compute_health_score
from app.registry.registry_service import get_champion
from app.self_healing.engine import trigger_self_healing
from app.self_healing.rollback import maybe_rollback
from app.services.monitoring_service import build_drift_report, get_latest_dataset
from app.monitoring.performance import compute_performance_report

logger = logging.getLogger("sentinelml.monitor")


async def _monitor_once() -> None:
    db = SessionLocal()
    try:
        champion = get_champion(db)
        if champion is None:
            return

        latest_dataset = get_latest_dataset(db)
        drift_report = build_drift_report(db)
        performance = compute_performance_report(db, champion)
        health = compute_health_score(
            db, champion, latest_dataset, performance.get("degradation_pct"), drift_report.get("overall_status", "NORMAL")
        )

        # Rollback takes priority if the currently deployed model is unhealthy.
        rollback_result = maybe_rollback(db, health["overall"], error_rate=0.0)
        if rollback_result:
            logger.info("Auto-rollback executed: %s", rollback_result)
            return

        if drift_report.get("overall_status") == "CRITICAL" and latest_dataset is not None:
            try:
                trigger_self_healing(db, "Critical data drift (auto-detected)", latest_dataset)
            except RuntimeError as exc:
                logger.info("Skipped auto-retrain (cooldown): %s", exc)
    finally:
        db.close()


async def monitoring_loop() -> None:
    while True:
        try:
            await _monitor_once()
        except Exception:  # noqa: BLE001
            logger.exception("Monitoring loop iteration failed")
        await asyncio.sleep(settings.MONITORING_INTERVAL_SECONDS)
