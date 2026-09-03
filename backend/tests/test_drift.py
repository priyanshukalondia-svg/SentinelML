import numpy as np
import pandas as pd

from app.monitoring.drift import compute_drift_report, inject_synthetic_drift


def test_no_drift_between_identical_distributions():
    rng = np.random.default_rng(1)
    reference = pd.DataFrame({"amount": rng.normal(100, 10, 1000), "age": rng.normal(40, 5, 1000)})
    current = pd.DataFrame({"amount": rng.normal(100, 10, 1000), "age": rng.normal(40, 5, 1000)})

    report = compute_drift_report(reference, current, method="psi")
    assert report["overall_status"] == "NORMAL"
    for feature in report["features"]:
        assert feature["status"] == "NORMAL"


def test_drift_detected_on_shifted_distribution():
    rng = np.random.default_rng(2)
    reference = pd.DataFrame({"amount": rng.normal(100, 10, 1000)})
    current = pd.DataFrame({"amount": rng.normal(400, 10, 1000)})

    report = compute_drift_report(reference, current, method="psi")
    assert report["overall_status"] == "CRITICAL"
    assert report["features"][0]["status"] == "HIGH"


def test_inject_synthetic_drift_shifts_mean():
    rng = np.random.default_rng(3)
    df = pd.DataFrame({"amount": rng.normal(100, 10, 500)})
    drifted = inject_synthetic_drift(df, intensity=3.0)
    assert drifted["amount"].mean() > df["amount"].mean()


def test_ks_method_supported():
    rng = np.random.default_rng(4)
    reference = pd.DataFrame({"amount": rng.normal(100, 10, 500)})
    current = pd.DataFrame({"amount": rng.normal(100, 10, 500)})
    report = compute_drift_report(reference, current, method="ks")
    assert report["method"] == "KS"
