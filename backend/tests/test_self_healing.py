def _train_and_deploy(client, sample_csv_path, model="logistic_regression"):
    with open(sample_csv_path, "rb") as f:
        r = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample.csv", f, "text/csv")},
            data={"target_column": "fraud"},
        )
    dataset = r.json()
    r = client.post("/api/v1/training/start", json={"dataset_id": dataset["id"], "models": [model]})
    run = r.json()[0]
    r = client.get("/api/v1/models")
    model_version = next(m for m in r.json() if m["id"])
    client.post(f"/api/v1/models/{model_version['id']}/deploy")
    return dataset, model_version


def test_self_healing_workflow_runs_end_to_end(client, sample_csv_path):
    _train_and_deploy(client, sample_csv_path)

    r = client.post("/api/v1/simulation/drift")
    assert r.status_code == 200
    body = r.json()
    assert "message" in body

    r = client.get("/api/v1/recovery")
    workflows = r.json()
    assert len(workflows) >= 1
    latest = workflows[0]
    assert latest["status"] == "COMPLETED"
    assert latest["outcome"] in ("PROMOTED", "REJECTED")
    # every step should be present in the ordered log
    steps = [entry["step"] for entry in latest["log"]]
    assert "DETECTED" in steps
    assert "RETRAINING" in steps
    assert "EVALUATING" in steps


def test_alerts_created_during_self_healing(client, sample_csv_path):
    _train_and_deploy(client, sample_csv_path)
    client.post("/api/v1/simulation/drift")

    r = client.get("/api/v1/alerts")
    alerts = r.json()
    assert len(alerts) >= 1
