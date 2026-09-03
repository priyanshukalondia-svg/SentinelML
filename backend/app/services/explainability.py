"""
Model explainability (Section 29): global feature importance and
individual-prediction explanations.

Uses SHAP's TreeExplainer for tree-based models (fast, exact) and a
closed-form linear contribution for LogisticRegression (mathematically
equivalent to SHAP for linear models, and much cheaper). For models where
neither applies (e.g. the RBF-kernel SVM), we fall back to permutation
importance for the global view and a mean-centered linear approximation
for individual predictions, and say so explicitly in the response so the
UI never claims more precision than it has.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from sklearn.inspection import permutation_importance


def _is_tree_model(model) -> bool:
    return hasattr(model, "feature_importances_")


def _is_linear_model(model) -> bool:
    return hasattr(model, "coef_")


def global_feature_importance(model, feature_names: List[str], X_sample: np.ndarray, y_sample) -> Dict[str, Any]:
    if _is_tree_model(model):
        importances = model.feature_importances_
        method = "tree_feature_importance"
    elif _is_linear_model(model):
        importances = np.abs(model.coef_[0])
        method = "linear_coefficients"
    else:
        try:
            result = permutation_importance(model, X_sample, y_sample, n_repeats=5, random_state=42, n_jobs=1)
            importances = result.importances_mean
            importances = np.clip(importances, 0, None)
            method = "permutation_importance"
        except Exception:
            importances = np.zeros(len(feature_names))
            method = "unavailable"

    total = importances.sum()
    normalized = importances / total if total > 0 else importances
    ranked = sorted(
        zip(feature_names, normalized.tolist()), key=lambda pair: pair[1], reverse=True
    )
    return {
        "method": method,
        "features": [{"feature": f, "importance": round(v, 4)} for f, v in ranked],
    }


def explain_single_prediction(model, scaler, feature_names: List[str], features: Dict[str, float]) -> Dict[str, Any]:
    row = np.array([[features.get(f, 0.0) for f in feature_names]])
    row_scaled = scaler.transform(row)

    if _is_tree_model(model):
        try:
            import shap

            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(row_scaled)
            values = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]
            method = "shap_tree_explainer"
        except Exception:
            values = model.feature_importances_ * row_scaled[0]
            method = "feature_importance_weighted_fallback"
    elif _is_linear_model(model):
        # For a linear model, SHAP values w.r.t. a zero baseline reduce to
        # coefficient * (scaled) feature value — computed directly here.
        values = model.coef_[0] * row_scaled[0]
        method = "linear_contribution"
    else:
        # No fast exact method for kernel SVMs; approximate contribution as
        # (mean-centered feature value) — flagged clearly as an approximation.
        values = row_scaled[0]
        method = "approximate_centered_value"

    contributions = sorted(
        zip(feature_names, [float(v) for v in values]), key=lambda pair: abs(pair[1]), reverse=True
    )
    return {
        "method": method,
        "contributions": [{"feature": f, "contribution": round(v, 4)} for f, v in contributions],
    }
