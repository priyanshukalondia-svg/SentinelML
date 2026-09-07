"""Generate the small built-in fraud dataset used by the guided demo."""
from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd


def build_default_dataset(rows: int = 5000) -> bytes:
    rng = np.random.default_rng(42)
    frame = pd.DataFrame(
        {
            "transaction_amount": rng.lognormal(4.2, 0.8, rows).round(2),
            "transaction_frequency": rng.poisson(3, rows),
            "account_age": rng.uniform(1, 2500, rows).round(1),
            "location_change": rng.binomial(1, 0.18, rows),
            "hour_of_day": rng.integers(0, 24, rows),
            "distance_from_home_km": rng.gamma(2.0, 25.0, rows).round(2),
            "num_declines_last_hour": rng.poisson(0.35, rows),
            "merchant_risk_score": rng.uniform(0, 1, rows).round(3),
            "is_online": rng.binomial(1, 0.55, rows),
        }
    )
    risk = (
        0.004 * frame["transaction_amount"]
        + 0.45 * frame["location_change"]
        + 0.55 * frame["merchant_risk_score"]
        + 0.3 * frame["is_online"]
        + 0.35 * frame["num_declines_last_hour"]
        - 0.00035 * frame["account_age"]
        + rng.normal(0, 0.45, rows)
    )
    frame["fraud"] = (risk > risk.quantile(0.78)).astype(int)

    output = BytesIO()
    frame.to_csv(output, index=False)
    return output.getvalue()