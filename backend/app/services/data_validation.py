"""
Data quality validation (SYSTEM_REQUIREMENTS.md Section 9).

Runs a set of transparent, explainable checks against an uploaded CSV and
returns a structured report plus an overall HEALTHY / WARNING / FAILED
verdict. Training is blocked when the verdict is FAILED (see
app.training.trainer).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

MAX_MISSING_PCT_WARNING = 5.0
MAX_MISSING_PCT_FAILED = 30.0
MAX_DUPLICATE_PCT_WARNING = 10.0
TARGET_MISSING_PCT_FAILED = 5.0


def validate_dataset(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    previous_schema: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []

    n_rows, n_cols = df.shape

    # --- Missing values ---
    missing_per_col = df.isna().mean().mul(100).round(2)
    overall_missing_pct = round(float(df.isna().mean().mean() * 100), 2)
    high_missing_cols = missing_per_col[missing_per_col > MAX_MISSING_PCT_FAILED]
    if len(high_missing_cols) > 0:
        issues.append(f"Columns with >{MAX_MISSING_PCT_FAILED}% missing values: {list(high_missing_cols.index)}")
    elif overall_missing_pct > MAX_MISSING_PCT_WARNING:
        warnings.append(f"Overall missing value rate is {overall_missing_pct}%")

    # --- Duplicates ---
    duplicate_count = int(df.duplicated().sum())
    duplicate_pct = round(duplicate_count / n_rows * 100, 2) if n_rows else 0.0
    if duplicate_pct > MAX_DUPLICATE_PCT_WARNING:
        warnings.append(f"Duplicate row rate is {duplicate_pct}%")

    # --- Data types ---
    dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

    # --- Numerical validation: infinite values ---
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_cols = [c for c in numeric_cols if np.isinf(df[c]).any()]
    if inf_cols:
        issues.append(f"Columns containing infinite values: {inf_cols}")

    # --- Target column checks ---
    if target_column:
        if target_column not in df.columns:
            issues.append(f"Target column '{target_column}' not found in dataset.")
        else:
            target_missing_pct = round(float(df[target_column].isna().mean() * 100), 2)
            if target_missing_pct > TARGET_MISSING_PCT_FAILED:
                issues.append(f"Target column '{target_column}' has {target_missing_pct}% missing values.")

    # --- Schema drift vs previous version ---
    schema_changed = False
    if previous_schema:
        current_schema = dtypes
        if set(current_schema.keys()) != set(previous_schema.keys()):
            schema_changed = True
            warnings.append("Column set differs from the previous dataset version.")

    # --- Verdict ---
    if issues:
        status = "FAILED"
    elif warnings:
        status = "WARNING"
    else:
        status = "HEALTHY"

    class_distribution = None
    if target_column and target_column in df.columns:
        vc = df[target_column].value_counts(normalize=True).round(4) * 100
        class_distribution = {str(k): float(v) for k, v in vc.items()}

    return {
        "status": status,
        "row_count": int(n_rows),
        "column_count": int(n_cols),
        "overall_missing_pct": overall_missing_pct,
        "missing_per_column_pct": {k: float(v) for k, v in missing_per_col.items()},
        "duplicate_count": duplicate_count,
        "duplicate_pct": duplicate_pct,
        "dtypes": dtypes,
        "issues": issues,
        "warnings": warnings,
        "schema_changed": schema_changed,
        "class_distribution": class_distribution,
    }
