import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Point every test run at an isolated temp SQLite DB + storage dirs so tests
# never touch a developer's real local database or model store.
_TMP = tempfile.mkdtemp(prefix="sentinelml_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["MLFLOW_TRACKING_URI"] = f"file:{_TMP}/mlruns"
os.environ["DATA_DIR"] = f"{_TMP}/datasets"
os.environ["MODEL_STORE_DIR"] = f"{_TMP}/models"

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app.core.database import init_db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _init_database():
    init_db()
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def sample_csv_path(tmp_path):
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(0)
    n = 800
    df = pd.DataFrame(
        {
            "transaction_amount": np.abs(rng.normal(90, 60, n)),
            "transaction_frequency": rng.poisson(3, n),
            "account_age": np.abs(rng.normal(400, 200, n)),
            "location_change": rng.binomial(1, 0.2, n),
            "fraud": rng.binomial(1, 0.15, n),
        }
    )
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return path
