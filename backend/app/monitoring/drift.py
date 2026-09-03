"""Data drift detection (Sections 21-22): PSI and Kolmogorov-Smirnov test."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from app.core.config import settings


def _psi(reference: np.ndarray, current: np.ndarray, buckets: int = 10) -> float:
    """Population Stability Index between two numeric distributions."""
    reference = reference[~np.isnan(reference)]
    current = current[~np.isnan(current)]
    if len(reference) == 0 or len(current) == 0:
        return 0.0

    breakpoints = np.linspace(0, 100, buckets + 1)
    edges = np.unique(np.percentile(reference, breakpoints))
    if len(edges) < 3:
        return 0.0

    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)

    ref_pct = np.where(ref_counts == 0, 1e-4, ref_counts / max(ref_counts.sum(), 1))
    cur_pct = np.where(cur_counts == 0, 1e-4, cur_counts / max(cur_counts.sum(), 1))

    psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
    return round(psi, 4)


def _status_for_score(score: float) -> str:
    if score >= settings.DRIFT_CRITICAL_THRESHOLD:
        return "HIGH"
    if score >= settings.DRIFT_WARNING_THRESHOLD:
        return "WARNING"
    return "NORMAL"


def compute_drift_report(
    reference_df: pd.DataFrame, current_df: pd.DataFrame, method: str = "psi"
) -> Dict:
    numeric_cols = [
        c for c in reference_df.select_dtypes(include=[np.number]).columns if c in current_df.columns
    ]

    results: List[Dict] = []
    for col in numeric_cols:
        ref_values = reference_df[col].to_numpy(dtype=float)
        cur_values = current_df[col].to_numpy(dtype=float)

        if method == "ks":
            stat, _p_value = ks_2samp(ref_values[~np.isnan(ref_values)], cur_values[~np.isnan(cur_values)])
            score = round(float(stat), 4)
        else:
            score = _psi(ref_values, cur_values)

        results.append({"feature": col, "drift_score": score, "status": _status_for_score(score)})

    results.sort(key=lambda r: r["drift_score"], reverse=True)

    if any(r["status"] == "HIGH" for r in results):
        overall = "CRITICAL"
    elif any(r["status"] == "WARNING" for r in results):
        overall = "WARNING"
    else:
        overall = "NORMAL"

    return {
        "method": method.upper(),
        "overall_status": overall,
        "features": results,
        "computed_at": datetime.now(timezone.utc),
    }


def inject_synthetic_drift(df: pd.DataFrame, intensity: float = 2.5) -> pd.DataFrame:
    """Used by the failure-simulation endpoint (Section 28) to produce a
    synthetically drifted copy of a reference dataset, isolated from real
    production data."""
    drifted = df.copy()
    numeric_cols = drifted.select_dtypes(include=[np.number]).columns
    rng = np.random.default_rng(seed=None)
    for col in numeric_cols:
        shift = drifted[col].std() * intensity if drifted[col].std() > 0 else intensity
        drifted[col] = drifted[col] + rng.normal(loc=shift, scale=abs(shift) * 0.3 + 1e-6, size=len(drifted))
    return drifted
