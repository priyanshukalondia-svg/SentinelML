import numpy as np
import pandas as pd

from app.services.data_validation import validate_dataset


def test_healthy_dataset_passes():
    df = pd.DataFrame(
        {
            "amount": np.random.normal(100, 10, 200),
            "age": np.random.randint(18, 80, 200),
            "fraud": np.random.binomial(1, 0.1, 200),
        }
    )
    report = validate_dataset(df, target_column="fraud")
    assert report["status"] == "HEALTHY"
    assert report["row_count"] == 200


def test_high_missing_values_fails():
    df = pd.DataFrame({"amount": [None] * 60 + [1.0] * 40, "fraud": [0, 1] * 50})
    report = validate_dataset(df, target_column="fraud")
    assert report["status"] == "FAILED"
    assert report["issues"]


def test_missing_target_column_fails():
    df = pd.DataFrame({"amount": [1, 2, 3]})
    report = validate_dataset(df, target_column="fraud")
    assert report["status"] == "FAILED"


def test_moderate_missing_values_warns():
    values = [1.0] * 90 + [None] * 10
    df = pd.DataFrame({"amount": values, "fraud": [0, 1] * 50})
    report = validate_dataset(df, target_column="fraud")
    assert report["status"] in ("WARNING", "HEALTHY")


def test_duplicate_detection():
    df = pd.DataFrame({"amount": [1.0] * 20, "fraud": [0] * 20})
    report = validate_dataset(df, target_column="fraud")
    assert report["duplicate_count"] > 0


def test_schema_change_detected():
    df = pd.DataFrame({"amount": [1.0, 2.0], "new_col": [1, 2], "fraud": [0, 1]})
    previous_schema = {"amount": "float64", "fraud": "int64"}
    report = validate_dataset(df, target_column="fraud", previous_schema=previous_schema)
    assert report["schema_changed"] is True
