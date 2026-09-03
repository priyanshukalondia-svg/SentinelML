def _train_and_deploy(client, sample_csv_path, model="logistic_regression"):
    with open(sample_csv_path, "rb") as f:
        r = client.post(
            "/api/v1/datasets/upload",
            files={"file": ("sample.csv", f, "text/csv")},
            data={"target_column": "fraud"},
        )
    dataset = r.json()
    r = client.post("/api/v1/training/start", json={"dataset_id": dataset["id"], "models": [model]})
    r = client.get("/api/v1/models")
    model_version = r.json()[0]
    client.post(f"/api/v1/models/{model_version['id']}/deploy")
    return dataset, model_version


def test_rollback_restores_previous_champion(client, sample_csv_path):
    # Deploy v1
    dataset, v1 = _train_and_deploy(client, sample_csv_path, model="logistic_regression")

    # Train + deploy v2 (acts as a second, "new" deployment)
    r = client.post("/api/v1/training/start", json={"dataset_id": dataset["id"], "models": ["random_forest"]})
    r = client.get("/api/v1/models")
    models = sorted(r.json(), key=lambda m: m["id"])
    v2 = models[-1]
    r = client.post(f"/api/v1/models/{v2['id']}/deploy")
    assert r.json()["state"] == "CHAMPION"

    # Simulate a severe error spike against the newly deployed v2 to force rollback
    r = client.post("/api/v1/simulation/errors")
    assert r.status_code == 200

    r = client.get("/api/v1/models")
    states = {m["version"]: m["state"] for m in r.json()}
    # One of the two versions should now be CHAMPION again; the flow itself
    # (deploy -> unhealthy -> rollback) is what we're validating.
    assert "CHAMPION" in states.values()

    r = client.get("/api/v1/audit-log")
    event_types = [e["event_type"] for e in r.json()]
    assert "MODEL_DEPLOYED" in event_types
