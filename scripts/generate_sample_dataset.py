"""
Generates a synthetic credit-card-style fraud transactions dataset used to
drive the SentinelML demo scenario (Section 50 of SYSTEM_REQUIREMENTS.md).

Usage:
    python scripts/generate_sample_dataset.py [--rows 20000] [--out ml/datasets/samples/transactions.csv]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def generate(rows: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    n_fraud = int(rows * 0.09)
    n_normal = rows - n_fraud

    def make_block(n: int, fraud: bool) -> pd.DataFrame:
        # Distributions deliberately overlap so no model hits a perfect
        # score — this leaves realistic room for a challenger to beat a
        # champion during the champion/challenger demo (Section 17-18).
        amount_mean = 210 if fraud else 70
        amount = np.abs(rng.normal(amount_mean, amount_mean * 0.9, n))
        frequency = rng.poisson(2.2 if fraud else 3.6, n)
        account_age_days = rng.exponential(260 if fraud else 700, n)
        location_change = rng.binomial(1, 0.35 if fraud else 0.12, n)
        hour_of_day = rng.integers(0, 24, n)
        distance_from_home_km = np.abs(rng.normal(120 if fraud else 20, 110 if fraud else 35, n))
        num_declines_last_hour = rng.poisson(0.9 if fraud else 0.25, n)
        merchant_risk_score = np.clip(rng.normal(0.55 if fraud else 0.28, 0.22, n), 0, 1)
        is_online = rng.binomial(1, 0.62 if fraud else 0.4, n)

        return pd.DataFrame(
            {
                "transaction_amount": amount.round(2),
                "transaction_frequency": frequency,
                "account_age": account_age_days.round(1),
                "location_change": location_change,
                "hour_of_day": hour_of_day,
                "distance_from_home_km": distance_from_home_km.round(2),
                "num_declines_last_hour": num_declines_last_hour,
                "merchant_risk_score": merchant_risk_score.round(3),
                "is_online": is_online,
                "fraud": 1 if fraud else 0,
            }
        )

    df = pd.concat([make_block(n_normal, False), make_block(n_fraud, True)], ignore_index=True)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # A touch of realistic messiness for the data-quality checks to find.
    missing_mask = rng.random(len(df)) < 0.015
    df.loc[missing_mask, "distance_from_home_km"] = np.nan
    dup_rows = df.sample(frac=0.003, random_state=seed)
    df = pd.concat([df, dup_rows], ignore_index=True)

    return df


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=20000)
    parser.add_argument("--out", type=str, default="ml/datasets/samples/transactions.csv")
    args = parser.parse_args()

    df = generate(args.rows)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()
