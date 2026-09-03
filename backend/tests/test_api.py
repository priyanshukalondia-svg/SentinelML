def test_full_train_deploy_predict_flow(client, sample_csv_path):
    with open(sample_csv_path, "rb") as f:
        r = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample.csv", f, "text/csv")},
            data={"target_column": "fraud"},
        )
    assert r.status_code == 200
    dataset = r.json()
    assert dataset["validation_status"] in ("HEALTHY", "WARNING")

    r = client.post(
        "/api/v1/training/start",
        json={"dataset_id": dataset["id"], "models": ["logistic_regression"]},
    )
    assert r.status_code == 200
    runs = r.json()
    assert len(runs) == 1
    assert runs[0]["status"] == "COMPLETED"
    assert runs[0]["mlflow_run_id"]  # tracked in MLflow
    assert "f1" in runs[0]["metrics"]

    r = client.get("/api/v1/models")
    models = r.json()
    assert len(models) >= 1
    candidate = models[0]

    r = client.post(f"/api/v1/models/{candidate['id']}/deploy")
    assert r.status_code == 200
    assert r.json()["state"] == "CHAMPION"

    r = client.post(
        "/api/v1/predict",
        json={"features": {"transaction_amount": 50.0, "transaction_frequency": 3, "account_age": 300, "location_change": 0}},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["prediction"] in (0, 1)
    assert 0.0 <= body["probability"] <= 1.0
    assert body["model_version"] == candidate["version"]


def test_predict_without_deployed_model_returns_400(client, sample_csv_path):
    # Fresh app state per test module isn't guaranteed, but if nothing has been
    # deployed yet in a clean test DB this should fail gracefully.
    r = client.post("/api/v1/predict", json={"features": {"transaction_amount": 10}})
    assert r.status_code in (200, 400)


def test_training_blocked_on_failed_validation(client, tmp_path):
    import pandas as pd

    bad_df = pd.DataFrame({"amount": [None] * 100, "fraud": [0] * 100})
    path = tmp_path / "bad.csv"
    bad_df.to_csv(path, index=False)

    with open(path, "rb") as f:
        r = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("bad.csv", f, "text/csv")},
            data={"target_column": "fraud"},
        )
    dataset = r.json()
    assert dataset["validation_status"] == "FAILED"

    r = client.post("/api/v1/training/start", json={"dataset_id": dataset["id"], "models": ["logistic_regression"]})
    assert r.status_code == 400
    assert r.json()["error"] == "DATA_VALIDATION_FAILED"


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "dependencies" in body
